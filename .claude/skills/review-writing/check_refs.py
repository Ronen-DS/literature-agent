"""Check a review draft's citations against the screened CSV.

This is the guard against invented references. It checks that:
  1. every PMID in the reference list is really in the screened CSV;
  2. every in-text [n] has a reference entry, and vice versa;
  3. the numbering follows the order of first appearance (Vancouver style);
  4. no reference is a preprint whose published version is also available;
  5. the word count is in the target range.

Run from the project folder:
  python .claude/skills/review-writing/check_refs.py results/draft.md results/<...>_screened.csv

It prints PROBLEMS or "All checks passed" and exits non-zero if anything failed.
"""

import argparse
import re
import sys
from pathlib import Path

from prepare import find_duplicate_pairs, load_csv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIN_WORDS = 3000
MAX_WORDS = 5000


def split_draft(text):
    """Split the draft into (body, references section)."""
    # The references heading may be "## References" or "# References".
    match = re.search(r"^#+\s*References\s*$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        sys.exit("No '## References' heading found in the draft.")
    return text[: match.start()], text[match.end():]


def citation_numbers_in_order(body):
    """Return the citation numbers in the order they first appear in the body.

    Handles [1], [2,3] and [4-6].
    """
    order = []
    for group in re.findall(r"\[([\d,\s\-–]+)\]", body):
        for part in group.split(","):
            part = part.strip().replace("–", "-")  # en dash -> hyphen
            if not part:
                continue
            if "-" in part:
                start, end = part.split("-", 1)
                if not (start.strip().isdigit() and end.strip().isdigit()):
                    continue
                numbers = range(int(start), int(end) + 1)
            elif part.isdigit():
                numbers = [int(part)]
            else:
                continue
            for number in numbers:
                if number not in order:
                    order.append(number)
    return order


def parse_references(section):
    """Return {number: pmid} from reference lines like '1. Authors. Title. PMID: 123'."""
    references = {}
    for line in section.splitlines():
        line = line.strip()
        match = re.match(r"^(\d+)[.)]\s+(.*)$", line)
        if not match:
            continue
        number, rest = int(match.group(1)), match.group(2)
        pmid_match = re.search(r"PMID:?\s*(\d{6,9})", rest, re.IGNORECASE)
        references[number] = pmid_match.group(1) if pmid_match else None
    return references


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", help="The review draft (markdown)")
    parser.add_argument("csv_path", help="results/<date>_<topic>_screened.csv")
    args = parser.parse_args()

    text = Path(args.draft).read_text(encoding="utf-8")
    rows = load_csv(args.csv_path)
    allowed = {r["pmid"]: r for r in rows}
    usable = [r for r in rows if r["decision"].strip().lower() in {"include", "maybe"}]
    duplicates, suspected = find_duplicate_pairs(usable)

    body, ref_section = split_draft(text)
    cited = citation_numbers_in_order(body)
    references = parse_references(ref_section)

    problems = []
    warnings = []

    # 1. Reference PMIDs must exist in the CSV.
    for number, pmid in sorted(references.items()):
        if pmid is None:
            problems.append(f"Reference {number} has no PMID.")
        elif pmid not in allowed:
            problems.append(
                f"Reference {number} cites PMID {pmid}, which is NOT in the CSV. "
                "Remove it - it may be an invented paper."
            )
        elif allowed[pmid]["decision"].strip().lower() == "exclude":
            problems.append(
                f"Reference {number} (PMID {pmid}) was screened as 'exclude'."
            )
        elif pmid in duplicates:
            problems.append(
                f"Reference {number} (PMID {pmid}) is a preprint; cite the "
                f"published version PMID {duplicates[pmid]} instead."
            )
        elif pmid in suspected:
            warnings.append(
                f"Reference {number} (PMID {pmid}) may be the same work as "
                f"PMID {suspected[pmid]} (same first author). Check you have "
                "not cited one paper twice."
            )

    # Both halves of a possible duplicate pair cited: almost certainly one paper.
    cited_pmids = set(references.values())
    for older, newer in suspected.items():
        if older in cited_pmids and newer in cited_pmids:
            problems.append(
                f"PMIDs {older} and {newer} are both cited but may be the same "
                "work (same first author, similar title). Compare the abstracts "
                "and cite only one."
            )

    # 2. In-text citations and reference entries must match up.
    for number in cited:
        if number not in references:
            problems.append(f"[{number}] is cited in the text but has no reference entry.")
    for number in references:
        if number not in cited:
            problems.append(f"Reference {number} is never cited in the text.")

    # 3. Vancouver numbering: first appearances must run 1, 2, 3, ...
    if cited != sorted(cited) or (cited and cited[0] != 1):
        problems.append(
            "Citations are not numbered in order of first appearance. "
            f"First appearances run: {cited[:15]}{' ...' if len(cited) > 15 else ''}"
        )

    # 4. Word count of the body (references excluded).
    words = len(re.findall(r"\b[\w'-]+\b", body))
    if not MIN_WORDS <= words <= MAX_WORDS:
        problems.append(f"Body is {words} words; target is {MIN_WORDS}-{MAX_WORDS}.")

    print(f"Body word count: {words}")
    print(f"References: {len(references)}; distinct in-text citations: {len(cited)}")
    unused = len(usable) - len(references)
    print(f"Papers available but not cited: {unused}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}) - check these yourself:")
        for warning in warnings:
            print(f"  - {warning}")

    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for problem in problems:
            print(f"  - {problem}")
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
