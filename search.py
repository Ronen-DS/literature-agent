"""
search.py - Search PubMed and save the results to a JSON file.

How it works:
  1. "esearch" asks PubMed which papers match the query and returns their PMIDs.
  2. "efetch" downloads the full records (title, authors, abstract...) for those PMIDs.
  3. We pull out the fields we need and save them to results/<date>_<topic>.json

Examples:
  python search.py "immunopeptidome AND neoantigen"
  python search.py "TCR-T AND neoantigen" --max 50
  python search.py "HLA ligandome" --mindate 2020 --maxdate 2025
  python search.py "HLA ligandome" --topic hla-ligandome
"""

import argparse
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

# Base address of the NCBI E-utilities web service
EUTILS_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

# NCBI asks programs to identify themselves with a "tool" name
TOOL_NAME = "lit-review-agent"

# How many records to download per efetch request (keeps each request small)
FETCH_BATCH_SIZE = 200

# Folder where result files are saved (next to this script)
RESULTS_DIR = Path(__file__).parent / "results"


# ---------------------------------------------------------------------------
# Talking to NCBI
# ---------------------------------------------------------------------------

def get_api_key():
    """Read NCBI_API_KEY from .env (if the file exists) or the environment.
    Returns None when there is no key - the script still works, just slower."""
    load_dotenv()  # does nothing if there is no .env file
    return os.getenv("NCBI_API_KEY") or None


def make_request(endpoint, params, api_key):
    """Send one request to NCBI, waiting first so we respect the rate limit.

    NCBI allows 3 requests/second without a key and 10/second with one,
    so we pause a little longer than 1/3 or 1/10 of a second before each call.
    If NCBI says "too many requests" (429) or has a server error, we retry.
    """
    params = dict(params, tool=TOOL_NAME)
    if api_key:
        params["api_key"] = api_key
    wait_seconds = 0.11 if api_key else 0.34

    for attempt in range(1, 4):  # try up to 3 times
        time.sleep(wait_seconds)
        response = requests.get(EUTILS_URL + endpoint, params=params, timeout=30)
        if response.status_code == 429 or response.status_code >= 500:
            print(f"  NCBI busy (status {response.status_code}), retrying...")
            time.sleep(2 * attempt)  # wait a bit longer each time
            continue
        response.raise_for_status()  # stop with an error for other problems
        return response

    raise RuntimeError("NCBI did not respond after 3 attempts. Try again later.")


def search_pmids(query, max_results, mindate, maxdate, api_key):
    """Step 1 (esearch): return (total number of matches, list of PMIDs)."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",  # best matches first
    }
    # Optional publication-date filter. NCBI needs both ends of the range,
    # so if only one is given we fill the other with a very wide value.
    if mindate or maxdate:
        params["datetype"] = "pdat"  # pdat = publication date
        params["mindate"] = mindate or "1800"
        params["maxdate"] = maxdate or "3000"

    data = make_request("esearch.fcgi", params, api_key).json()
    result = data["esearchresult"]

    # PubMed reports problems with the query (e.g. a misspelled field tag) here
    if "ERROR" in result:
        raise RuntimeError("PubMed error: " + result["ERROR"])
    for warning_type, items in result.get("warninglist", {}).items():
        if items:
            print(f"  PubMed warning ({warning_type}): {items}")

    return int(result["count"]), result["idlist"]


def fetch_records(pmids, api_key):
    """Step 2 (efetch): download full records in batches; return XML <PubmedArticle> elements."""
    articles = []
    for start in range(0, len(pmids), FETCH_BATCH_SIZE):
        batch = pmids[start:start + FETCH_BATCH_SIZE]
        params = {"db": "pubmed", "id": ",".join(batch), "retmode": "xml"}
        xml_text = make_request("efetch.fcgi", params, api_key).content
        root = ET.fromstring(xml_text)
        articles.extend(root.findall("PubmedArticle"))
    return articles


# ---------------------------------------------------------------------------
# Pulling fields out of the PubMed XML
# ---------------------------------------------------------------------------

def element_text(element):
    """Get all text inside an XML element, including text in tags like <i>."""
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())  # also tidies spaces


def parse_authors(article):
    """Return a list like ["Smith J", "Lee K"] (or a group name for consortia)."""
    authors = []
    for author in article.findall(".//AuthorList/Author"):
        last_name = author.findtext("LastName")
        initials = author.findtext("Initials", default="")
        group_name = author.findtext("CollectiveName")
        if last_name:
            authors.append(f"{last_name} {initials}".strip())
        elif group_name:
            authors.append(group_name)
    return authors


def parse_year(article):
    """Find the publication year. PubMed stores dates in a few different ways."""
    pub_date = article.find(".//Journal/JournalIssue/PubDate")
    if pub_date is not None:
        year = pub_date.findtext("Year")
        if year:
            return year
        # Some records use free text, e.g. "2021 Jan-Feb"; grab the first 4 digits
        match = re.search(r"\d{4}", pub_date.findtext("MedlineDate", default=""))
        if match:
            return match.group()
    # Fall back to the electronic publication date
    return article.findtext(".//ArticleDate/Year", default="")


# PubMed writes months as "Jan", "Feb"... (sometimes as numbers)
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
          "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def parse_pub_date(article):
    """Return the publication date as 'YYYY-MM-DD' (missing month/day become 01).
    Prefers the electronic date (ArticleDate), which is usually when the paper
    first appeared online; otherwise uses the journal issue date."""
    for path in (".//ArticleDate", ".//Journal/JournalIssue/PubDate"):
        date_element = article.find(path)
        if date_element is None or not date_element.findtext("Year"):
            continue
        year = int(date_element.findtext("Year"))
        month_text = date_element.findtext("Month", default="1")
        if month_text.isdigit():
            month = int(month_text)
        else:
            month = MONTHS.get(month_text[:3].lower(), 1)
        day_text = date_element.findtext("Day", default="1")
        day = int(day_text) if day_text.isdigit() else 1
        return f"{year:04d}-{month:02d}-{day:02d}"
    # Last resort: only the year is known
    year = parse_year(article)
    return f"{year}-01-01" if year else ""


def parse_abstract(article):
    """Join all abstract sections. Structured abstracts get their labels
    (e.g. "METHODS: ...") so the sections stay readable."""
    parts = []
    for section in article.findall(".//Abstract/AbstractText"):
        text = element_text(section)
        label = section.get("Label")
        parts.append(f"{label}: {text}" if label else text)
    return "\n".join(parts)


def parse_doi(article):
    """Find the DOI, which can be stored in two different places."""
    for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        if article_id.get("IdType") == "doi":
            return article_id.text or ""
    for location in article.findall(".//ELocationID"):
        if location.get("EIdType") == "doi":
            return location.text or ""
    return ""


def parse_article(article):
    """Turn one <PubmedArticle> into a simple dictionary."""
    return {
        "pmid": article.findtext(".//MedlineCitation/PMID", default=""),
        "title": element_text(article.find(".//ArticleTitle")),
        "authors": parse_authors(article),
        "journal": article.findtext(".//Journal/Title", default=""),
        "year": parse_year(article),
        "pub_date": parse_pub_date(article),
        "abstract": parse_abstract(article),
        "doi": parse_doi(article),
    }


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def make_short_topic(text):
    """Turn text into a short, file-name-safe label, e.g.
    'Immunopeptidome AND neoantigen[tiab]' -> 'immunopeptidome-and-neoantigen-tiab'."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words[:5]) or "search"


def save_results(papers, query, total_found, mindate, maxdate, topic):
    """Write everything to results/<date>_<topic>.json and return the file path."""
    RESULTS_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()  # e.g. 2026-11-04
    path = RESULTS_DIR / f"{today}_{make_short_topic(topic)}.json"

    # Don't overwrite an earlier search from the same day: add _2, _3, ...
    counter = 2
    while path.exists():
        path = RESULTS_DIR / f"{today}_{make_short_topic(topic)}_{counter}.json"
        counter += 1

    output = {
        "query": query,
        "date_range": {"min": mindate, "max": maxdate},
        "searched_on": today,
        "total_matches_in_pubmed": total_found,
        "papers_saved": len(papers),
        "papers": papers,
    }
    # ensure_ascii=False keeps characters like "é" or "α" readable in the file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main():
    # Read the command-line arguments
    parser = argparse.ArgumentParser(description="Search PubMed and save results as JSON.")
    parser.add_argument("query", help='PubMed query, e.g. "immunopeptidome AND neoantigen"')
    parser.add_argument("--max", type=int, default=20, help="maximum papers to save (default 20)")
    parser.add_argument("--mindate", help="earliest publication date: YYYY, YYYY/MM or YYYY/MM/DD")
    parser.add_argument("--maxdate", help="latest publication date: YYYY, YYYY/MM or YYYY/MM/DD")
    parser.add_argument("--topic", help="short label for the file name (default: made from the query)")
    args = parser.parse_args()

    api_key = get_api_key()
    print("Using NCBI API key." if api_key else "No NCBI API key found; running at the slower rate.")

    print(f"Searching PubMed for: {args.query}")
    total_found, pmids = search_pmids(args.query, args.max, args.mindate, args.maxdate, api_key)
    print(f"  {total_found} papers match; downloading the top {len(pmids)}.")

    papers = [parse_article(a) for a in fetch_records(pmids, api_key)] if pmids else []

    path = save_results(papers, args.query, total_found, args.mindate, args.maxdate,
                        args.topic or args.query)
    print(f"Saved {len(papers)} papers to {path}")


if __name__ == "__main__":
    main()
