"""
screen.py - Step 1 of paper screening: filter a pubmed-search results file
by age and citations, then add a journal metric.

What it does:
  1. Keeps only papers from the last YEARS_BACK years.
  2. Gets citation counts from NIH iCite and removes papers with fewer than
     MIN_CITATIONS, unless they were published in the last RECENT_MONTHS_EXEMPT
     months (new papers haven't had time to be cited).
  3. Adds each journal's "2-year mean citedness" from OpenAlex (similar to an
     impact factor: average citations per paper the journal published in the
     previous 2 years).
  4. Saves the kept papers to results/<same name>_filtered.json

Run from the project folder:
  python .claude/skills/paper-screening/screen.py results/2026-11-04_my-topic.json
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# SETTINGS - change these to make the screen stricter or looser
# ---------------------------------------------------------------------------
YEARS_BACK = 5             # keep papers published in this calendar year or the 5 before it
MIN_CITATIONS = 50         # minimum iCite citation count to keep a paper...
RECENT_MONTHS_EXEMPT = 12  # ...unless it was published within this many months
# ---------------------------------------------------------------------------

ICITE_URL = "https://icite.od.nih.gov/api/pubs"
OPENALEX_URL = "https://api.openalex.org/"
BATCH_SIZE = 50  # papers per API request


# ---------------------------------------------------------------------------
# Helper for web requests
# ---------------------------------------------------------------------------

def get_json(url, params):
    """GET a URL and return the JSON reply. Waits 0.15 s first to stay polite
    (well under iCite's and OpenAlex's rate limits) and retries if the server is busy."""
    for attempt in range(1, 4):
        time.sleep(0.15)
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 429 or response.status_code >= 500:
            print(f"  Server busy (status {response.status_code}), retrying...")
            time.sleep(3 * attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"{url} did not respond after 3 attempts. Try again later.")


def in_batches(items, size=BATCH_SIZE):
    """Split a list into chunks: [1..120] -> [1..50], [51..100], [101..120]."""
    for start in range(0, len(items), size):
        yield items[start:start + size]


# ---------------------------------------------------------------------------
# Step 1: publication age
# ---------------------------------------------------------------------------

def months_ago(n):
    """The date n months before today (day capped at 28 so every month works)."""
    total_months = date.today().year * 12 + (date.today().month - 1) - n
    return date(total_months // 12, total_months % 12 + 1, min(date.today().day, 28))


def published_on(paper):
    """The paper's publication date. Older results files have only a year;
    then we assume 1 January (the strictest choice for the recency exemption)."""
    text = paper.get("pub_date") or f"{paper.get('year') or 1900}-01-01"
    return date.fromisoformat(text)


# ---------------------------------------------------------------------------
# Step 2: citations from iCite
# ---------------------------------------------------------------------------

def get_citation_counts(pmids):
    """Return {pmid: citation count} from iCite. iCite counts citations from
    other PubMed papers, so numbers are lower than Google Scholar's."""
    counts = {}
    for batch in in_batches(pmids, 200):  # iCite accepts many PMIDs per request
        data = get_json(ICITE_URL, {"pmids": ",".join(batch), "fl": "pmid,citation_count"})
        for record in data.get("data", []):
            counts[str(record["pmid"])] = record.get("citation_count") or 0
    return counts


# ---------------------------------------------------------------------------
# Step 3: journal metric from OpenAlex
# ---------------------------------------------------------------------------

def openalex_params(params, api_key):
    """Add the OpenAlex API key if we have one (optional, gives a bigger daily budget)."""
    return dict(params, api_key=api_key) if api_key else params


def find_journal_ids_by_doi(dois, api_key):
    """Ask OpenAlex which journal each DOI was published in.
    Returns {doi (lower case): OpenAlex journal id like 'S110447773'}."""
    journal_for_doi = {}
    # Commas and | have special meaning in OpenAlex filters, so skip such DOIs
    safe_dois = [d for d in dois if "," not in d and "|" not in d]
    for batch in in_batches(safe_dois):
        params = {"filter": "doi:" + "|".join(batch),
                  "select": "doi,primary_location", "per-page": BATCH_SIZE}
        data = get_json(OPENALEX_URL + "works", openalex_params(params, api_key))
        for work in data["results"]:
            source = (work.get("primary_location") or {}).get("source") or {}
            # Only count real journals (not preprint servers or repositories)
            if source.get("id") and source.get("type", "journal") == "journal":
                doi = work["doi"].replace("https://doi.org/", "").lower()
                journal_for_doi[doi] = source["id"].split("/")[-1]
    return journal_for_doi


def get_journal_by_id(journal_id, api_key):
    """Return (journal name, 2-year mean citedness) for an OpenAlex journal id."""
    params = {"select": "display_name,summary_stats"}
    data = get_json(OPENALEX_URL + "sources/" + journal_id, openalex_params(params, api_key))
    return data["display_name"], (data.get("summary_stats") or {}).get("2yr_mean_citedness")


def get_journal_by_name(name, api_key):
    """Fallback when the DOI didn't work: search OpenAlex journals by name.
    Returns (matched name, metric), or (None, None) if nothing is found."""
    params = {"search": name, "filter": "type:journal", "per-page": 1,
              "select": "display_name,summary_stats"}
    results = get_json(OPENALEX_URL + "sources", openalex_params(params, api_key))["results"]
    if not results:
        return None, None
    return results[0]["display_name"], (results[0].get("summary_stats") or {}).get("2yr_mean_citedness")


def add_journal_metrics(papers, api_key):
    """Set paper['journal_metric'] and paper['openalex_journal'] for every paper."""
    journal_for_doi = find_journal_ids_by_doi([p["doi"].lower() for p in papers if p["doi"]], api_key)
    cache = {}  # so each journal is looked up only once
    for paper in papers:
        journal_id = journal_for_doi.get(paper["doi"].lower())
        if journal_id:
            key = journal_id
            if key not in cache:
                cache[key] = get_journal_by_id(journal_id, api_key)
        else:
            key = "name:" + paper["journal"]
            if key not in cache:
                cache[key] = get_journal_by_name(paper["journal"], api_key)
                # Name matches can be wrong, so show them for checking
                print(f"  Matched by name: '{paper['journal']}' -> '{cache[key][0]}'")
        paper["openalex_journal"], metric = cache[key]
        paper["journal_metric"] = round(metric, 2) if metric is not None else None


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Filter a pubmed-search results file.")
    parser.add_argument("results_file", help="e.g. results/2026-11-04_my-topic.json")
    args = parser.parse_args()

    load_dotenv()  # reads OPENALEX_API_KEY from .env if present
    api_key = os.getenv("OPENALEX_API_KEY") or None

    input_path = Path(args.results_file)
    with open(input_path, encoding="utf-8") as f:
        search = json.load(f)
    papers = search["papers"]
    print(f"Loaded {len(papers)} papers from {input_path}")

    # --- Step 1: publication age ---
    first_year = date.today().year - YEARS_BACK
    papers_recent_enough = [p for p in papers if p["year"] and int(p["year"]) >= first_year]
    removed_age = len(papers) - len(papers_recent_enough)
    print(f"Step 1 - published {first_year} or later: removed {removed_age}, "
          f"{len(papers_recent_enough)} left")

    # --- Step 2: citations ---
    counts = get_citation_counts([p["pmid"] for p in papers_recent_enough])
    exempt_after = months_ago(RECENT_MONTHS_EXEMPT)
    kept, exempted = [], 0
    for paper in papers_recent_enough:
        paper["citations"] = counts.get(paper["pmid"], 0)  # not in iCite yet = 0
        if paper["citations"] >= MIN_CITATIONS:
            kept.append(paper)
        elif published_on(paper) >= exempt_after:
            kept.append(paper)
            exempted += 1
    removed_citations = len(papers_recent_enough) - len(kept)
    print(f"Step 2 - at least {MIN_CITATIONS} citations, or published since {exempt_after}: "
          f"removed {removed_citations}, {len(kept)} left "
          f"({exempted} of them kept only because they are recent)")

    # --- Step 3: journal metric ---
    print("Step 3 - looking up journal metrics in OpenAlex...")
    add_journal_metrics(kept, api_key)
    missing = sum(1 for p in kept if p["journal_metric"] is None)
    print(f"  Journal metric found for {len(kept) - missing} of {len(kept)} papers")

    # --- Save ---
    output_path = input_path.with_name(input_path.stem + "_filtered.json")
    output = {
        "source_file": str(input_path),
        "query": search.get("query"),
        "screened_on": date.today().isoformat(),
        "settings": {"YEARS_BACK": YEARS_BACK, "MIN_CITATIONS": MIN_CITATIONS,
                     "RECENT_MONTHS_EXEMPT": RECENT_MONTHS_EXEMPT},
        "counts": {"loaded": len(papers), "removed_by_age": removed_age,
                   "removed_by_citations": removed_citations,
                   "kept_by_recent_exemption": exempted, "kept": len(kept)},
        "papers": kept,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(kept)} papers to {output_path}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError) as error:
        sys.exit(f"Problem talking to iCite/OpenAlex: {error}")
