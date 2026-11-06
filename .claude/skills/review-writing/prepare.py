"""Prepare the papers for a literature review.

Reads a screened CSV made by the paper-screening skill, plus the matching
_filtered.json (which holds the abstracts), and helps pick the papers to cite.

Two stages, so you never load 200 abstracts at once:
  Stage 1 (no --abstracts): print a one-line summary of every usable paper.
  Stage 2 (--abstracts PMIDS): print the full abstracts of just the papers
          you picked in stage 1.

It also finds preprint/journal duplicate pairs (the same work posted on
bioRxiv and then published) so the review cites the journal version.

Run from the project folder. See SKILL.md for the exact commands.
"""

import argparse
import csv
import difflib
import json
import re
import sys
from pathlib import Path

# Abstracts contain Greek letters and symbols. The Windows console defaults to
# a codepage that cannot print them, which would crash the script, so force
# UTF-8 output and replace anything that still will not print.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Journal names that mean "this is a preprint, not the final published paper".
PREPRINT_NAMES = ("biorxiv", "medrxiv", "arxiv", "research square", "ssrn", "preprint")

# How similar two titles must be to count as the same work. A preprint is often
# retitled before publication, so a shared first author lets us accept a much
# weaker title match.
SAME_TITLE = 0.90
SAME_AUTHOR_TITLE = 0.60
SUSPECT_AUTHOR_TITLE = 0.45


def is_preprint(journal):
    """True if the journal name looks like a preprint server."""
    return any(name in journal.lower() for name in PREPRINT_NAMES)


def normalise_title(title):
    """Lowercase a title and drop punctuation, so near-identical titles match."""
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def load_csv(path):
    """Read the screened CSV into a list of dictionaries (one per paper)."""
    # utf-8-sig strips the byte-order mark Excel writes at the start of a file.
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_abstracts(path):
    """Read the filtered JSON and return {pmid: abstract}."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {str(p["pmid"]): (p.get("abstract") or "") for p in data["papers"]}


def find_duplicate_pairs(rows):
    """Find pairs of rows that are the same work (preprint + journal version).

    Returns two dictionaries, each {pmid_to_avoid: pmid_to_cite}:
      confirmed - near-identical titles, or a shared first author plus a
                  similar title. Cite the published version.
      suspected - same first author and a loosely similar title, where one is a
                  preprint. Might be the same work retitled, or might be two
                  real papers from one group. Read both abstracts and decide.
    """
    confirmed, suspected = {}, {}
    titles = [(row, normalise_title(row["title"])) for row in rows]

    for i, (row_a, title_a) in enumerate(titles):
        for row_b, title_b in titles[i + 1:]:
            ratio = difflib.SequenceMatcher(None, title_a, title_b).ratio()
            same_author = (
                row_a["first_author"]
                and row_a["first_author"] == row_b["first_author"]
            )
            a_pre = is_preprint(row_a["journal"])
            b_pre = is_preprint(row_b["journal"])
            one_is_preprint = a_pre or b_pre

            if ratio >= SAME_TITLE or (
                same_author and one_is_preprint and ratio >= SAME_AUTHOR_TITLE
            ):
                target = confirmed
            elif same_author and one_is_preprint and ratio >= SUSPECT_AUTHOR_TITLE:
                target = suspected
            else:
                continue

            if a_pre and not b_pre:
                target[row_a["pmid"]] = row_b["pmid"]
            elif b_pre and not a_pre:
                target[row_b["pmid"]] = row_a["pmid"]
            else:
                # Both preprints or both journals: keep the newer one.
                older, newer = sorted([row_a, row_b], key=lambda r: r.get("year") or "")
                target[older["pmid"]] = newer["pmid"]

    return confirmed, suspected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", help="results/<date>_<topic>_screened.csv")
    parser.add_argument(
        "--abstracts",
        help="Stage 2: comma-separated PMIDs (or a path to a file of PMIDs, "
             "one per line) to print abstracts for.",
    )
    parser.add_argument(
        "--include-maybe",
        action="store_true",
        help='Also offer papers judged "maybe", not just "include".',
    )
    parser.add_argument(
        "--papers",
        help="Path to the _filtered.json holding the abstracts "
             "(default: the CSV path with _screened.csv swapped for _filtered.json).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        sys.exit(f"No such file: {csv_path}")

    # The abstracts live in the _filtered.json next to the CSV.
    if args.papers:
        papers_path = Path(args.papers)
    else:
        papers_path = Path(str(csv_path).replace("_screened.csv", "_filtered.json"))
    if not papers_path.exists():
        sys.exit(
            f"No such file: {papers_path}\n"
            "Pass the filtered JSON with --papers (it holds the abstracts)."
        )

    rows = load_csv(csv_path)
    abstracts = load_abstracts(papers_path)

    wanted = {"include", "maybe"} if args.include_maybe else {"include"}
    usable = [r for r in rows if r["decision"].strip().lower() in wanted]
    duplicates, suspected = find_duplicate_pairs(usable)

    # ---------- Stage 2: abstracts for the chosen papers ----------
    if args.abstracts:
        source = Path(args.abstracts)
        if source.exists():
            text = source.read_text(encoding="utf-8")
        else:
            text = args.abstracts
        pmids = [p for p in re.split(r"[,\s]+", text.strip()) if p]

        by_pmid = {r["pmid"]: r for r in rows}
        for pmid in pmids:
            row = by_pmid.get(pmid)
            if row is None:
                print(f"\n### {pmid}\nNOT IN THIS CSV - do not cite it.\n")
                continue
            if pmid in duplicates:
                print(f"\n[!] PMID {pmid} is a preprint duplicate of "
                      f"{duplicates[pmid]} - cite {duplicates[pmid]} instead.")
            if pmid in suspected:
                print(f"\n[?] PMID {pmid} may be the same work as "
                      f"{suspected[pmid]} (same first author). Compare the two "
                      "abstracts; if they are one paper, cite only "
                      f"{suspected[pmid]}.")
            print(f"\n### {pmid} | {row['journal']} {row['year']} | "
                  f"{row['first_author']} | {row['study_type']}")
            print(row["title"])
            print(abstracts.get(pmid) or "(no abstract available)")
        return

    # ---------- Stage 1: the candidate list ----------
    print(f"{len(rows)} papers in {csv_path.name}; "
          f"{len(usable)} usable ({'include + maybe' if args.include_maybe else 'include only'}).")

    if duplicates:
        print(f"\nPreprint/journal duplicate pairs ({len(duplicates)}) - "
              f"cite the second PMID, not the first:")
        for preprint, published in sorted(duplicates.items()):
            print(f"  {preprint} -> {published}")

    if suspected:
        print(f"\nPossible duplicates ({len(suspected)}) - same first author, "
              "loosely similar title. Read both abstracts before citing either:")
        for older, newer in sorted(suspected.items()):
            print(f"  {older} ~ {newer}")

    print("\nCandidates, grouped by subtopic. Columns: PMID | year | journal | "
          "metric | study type | title | screening reason")
    for subtopic in sorted({r["subtopic"] for r in usable}):
        group = [r for r in usable if r["subtopic"] == subtopic]
        print(f"\n## {subtopic} ({len(group)})")
        for row in sorted(group, key=lambda r: r.get("year") or "", reverse=True):
            flag = "  [preprint dup]" if row["pmid"] in duplicates else ""
            print(f"{row['pmid']} | {row['year']} | {row['journal']} | "
                  f"{row['journal_metric'] or '-'} | {row['study_type']} | "
                  f"{row['title']} | {row['reason']}{flag}")


if __name__ == "__main__":
    main()
