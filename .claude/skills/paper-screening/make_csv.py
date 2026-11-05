"""
make_csv.py - Final step of paper screening: combine the filtered papers
(from screen.py) with the relevance decisions (written by Claude) into a CSV.

Run from the project folder:
  python .claude/skills/paper-screening/make_csv.py results/X_filtered.json results/X_decisions.json

The decisions file looks like this (one entry per PMID):
  {
    "12345678": {"decision": "include", "reason": "MS-based neoantigen discovery in melanoma",
                 "subtopic": "immunopeptidomics", "study_type": "original research"},
    ...
  }

Output: results/X_screened.csv, sorted by journal metric (highest first).
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

# Allowed values, so typos are caught before they end up in the CSV
DECISIONS = {"include", "exclude", "maybe"}
SUBTOPICS = {"immunopeptidomics", "neoantigen prediction", "TCR identification",
             "immunotherapy", "other"}
STUDY_TYPES = {"original research", "review", "method/tool", "clinical"}

COLUMNS = ["pmid", "title", "first_author", "journal", "year", "citations",
           "journal_metric", "decision", "reason", "subtopic", "study_type", "pubmed_link"]


def main():
    parser = argparse.ArgumentParser(description="Merge screening decisions into a CSV.")
    parser.add_argument("filtered_file", help="results/X_filtered.json from screen.py")
    parser.add_argument("decisions_file", help="results/X_decisions.json")
    args = parser.parse_args()

    with open(args.filtered_file, encoding="utf-8") as f:
        papers = json.load(f)["papers"]
    with open(args.decisions_file, encoding="utf-8") as f:
        decisions = json.load(f)

    # Check every paper has a valid decision before writing anything
    problems = []
    for paper in papers:
        d = decisions.get(paper["pmid"])
        if d is None:
            problems.append(f"{paper['pmid']}: no decision")
            continue
        if d.get("decision") not in DECISIONS:
            problems.append(f"{paper['pmid']}: bad decision {d.get('decision')!r}")
        if d.get("subtopic") not in SUBTOPICS:
            problems.append(f"{paper['pmid']}: bad subtopic {d.get('subtopic')!r}")
        if d.get("study_type") not in STUDY_TYPES:
            problems.append(f"{paper['pmid']}: bad study type {d.get('study_type')!r}")
    if problems:
        sys.exit("Fix the decisions file first:\n  " + "\n  ".join(problems))

    # Build one row per paper
    rows = []
    for paper in papers:
        d = decisions[paper["pmid"]]
        rows.append({
            "pmid": paper["pmid"],
            "title": paper["title"],
            "first_author": paper["authors"][0] if paper["authors"] else "",
            "journal": paper["journal"],
            "year": paper["year"],
            "citations": paper["citations"],
            "journal_metric": paper["journal_metric"],
            "decision": d["decision"],
            "reason": d["reason"],
            "subtopic": d["subtopic"],
            "study_type": d["study_type"],
            "pubmed_link": f"https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/",
        })

    # Highest journal metric first; papers without a metric go last
    rows.sort(key=lambda r: r["journal_metric"] if r["journal_metric"] is not None else -1,
              reverse=True)

    output_path = Path(args.filtered_file.replace("_filtered.json", "_screened.csv"))
    # utf-8-sig makes Excel show special characters (é, α, ...) correctly
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} papers to {output_path}")
    print("Decisions:", dict(Counter(r["decision"] for r in rows)))
    print("Subtopics (included):", dict(Counter(r["subtopic"] for r in rows if r["decision"] == "include")))
    print("Study types (included):", dict(Counter(r["study_type"] for r in rows if r["decision"] == "include")))


if __name__ == "__main__":
    main()
