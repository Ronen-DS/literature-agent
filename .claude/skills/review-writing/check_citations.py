"""Check a review's saved reference list against the screened CSV it came from.

The reference list is a JSON file saved next to the review's .docx, e.g.
results/2026-11-06_my-topic_references.json, shaped like this:

    {
      "review": "results/2026-11-06_my-topic_review.docx",
      "screened_csv": "results/2026-11-06_my-topic_screened.csv",
      "references": [
        {"number": 1, "pmid": "37328642", "doi": "10.1038/...", "citation": "Yang K, et al. ..."},
        ...
      ]
    }

The check FAILS if:
  - a reference has no PMID;
  - a PMID is not in the screened CSV (it may be an invented paper);
  - a PMID is in the CSV but its decision is not "include";
  - the same PMID is listed twice, or the numbers do not run 1, 2, 3, ...;
  - a DOI is given but differs from the DOI PubMed returned for that PMID.

Two ways to run it (from the project folder):

  By hand:
    python .claude/skills/review-writing/check_citations.py results/<name>_references.json

  As a Claude Code hook (settings.json runs this after every Write):
    python .claude/skills/review-writing/check_citations.py --hook
  In hook mode it reads the hook's JSON from stdin, ignores any file that is
  not a *_references.json, and on failure prints {"decision": "block", ...}
  so the report is sent back to Claude to fix.

By hand, it exits 1 on failure and 0 on success.
"""

import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The project folder is three levels above this file:
# <project>/.claude/skills/review-writing/check_citations.py
PROJECT_DIR = Path(__file__).resolve().parents[3]


def resolve(path_text):
    """Turn a path from the JSON (usually relative, like results/x.csv) into a real path."""
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_DIR / path


def load_csv(path):
    """Read the screened CSV into {pmid: row}."""
    # utf-8-sig strips the byte-order mark Excel writes at the start of a file.
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {row["pmid"].strip(): row for row in csv.DictReader(f)}


def load_dois(csv_path):
    """Read {pmid: doi} from the _filtered.json next to the CSV, if it exists."""
    papers_path = Path(str(csv_path).replace("_screened.csv", "_filtered.json"))
    if not papers_path.exists():
        return {}
    with open(papers_path, encoding="utf-8") as f:
        data = json.load(f)
    return {str(p["pmid"]): (p.get("doi") or "").strip() for p in data["papers"]}


def check(refs_path):
    """Check one references JSON. Returns (passed, report_text)."""
    lines = [f"Citation check: {refs_path}"]
    problems = []

    # --- Read the references file ---
    try:
        data = json.loads(Path(refs_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return False, f"{lines[0]}\nFAIL: cannot read the file as JSON ({error})."

    csv_text = data.get("screened_csv")
    references = data.get("references")
    if not csv_text:
        return False, f"{lines[0]}\nFAIL: no \"screened_csv\" field, so the source CSV is unknown."
    if not isinstance(references, list) or not references:
        return False, f"{lines[0]}\nFAIL: no \"references\" list, or it is empty."

    csv_path = resolve(csv_text)
    if not csv_path.exists():
        return False, f"{lines[0]}\nFAIL: the screened CSV {csv_text} does not exist."

    rows = load_csv(csv_path)
    dois = load_dois(csv_path)
    lines.append(f"Screened CSV: {csv_text} ({len(rows)} papers)")
    lines.append(f"References checked: {len(references)}")

    # --- Check each reference ---
    seen = {}
    for position, ref in enumerate(references, start=1):
        number = ref.get("number", position)
        label = f"Reference {number}"
        pmid = str(ref.get("pmid") or "").strip()

        if number != position:
            problems.append(f"{label} is in position {position}; numbers must run 1, 2, 3, ...")

        if not pmid:
            problems.append(f"{label} has no PMID. Every reference needs one.")
            continue
        if pmid in seen:
            problems.append(f"{label} repeats PMID {pmid} (already reference {seen[pmid]}).")
        seen[pmid] = number

        row = rows.get(pmid)
        if row is None:
            problems.append(
                f"{label}: PMID {pmid} is NOT in the screened CSV. "
                "It may be an invented paper - remove it."
            )
            continue
        decision = row["decision"].strip().lower()
        if decision != "include":
            problems.append(
                f"{label}: PMID {pmid} was screened as '{decision}', not 'include'."
            )

        doi = str(ref.get("doi") or "").strip().lower()
        known = dois.get(pmid, "").lower()
        if doi and known and doi != known:
            problems.append(
                f"{label}: DOI {doi} does not match the DOI PubMed gave for PMID {pmid} ({known})."
            )

    if problems:
        lines.append(f"\nFAIL - {len(problems)} problem(s):")
        lines.extend(f"  - {p}" for p in problems)
        return False, "\n".join(lines)

    lines.append("\nPASS - every reference has a PMID that is in the CSV with decision 'include'.")
    return True, "\n".join(lines)


def run_as_hook():
    """Hook mode: read the hook input from stdin and reply in the hook JSON format."""
    hook_input = json.load(sys.stdin)
    file_path = (hook_input.get("tool_input") or {}).get("file_path", "")

    # The hook fires on every Write; only reference lists concern us.
    if not file_path.endswith("_references.json"):
        sys.exit(0)

    passed, report = check(file_path)
    if passed:
        # Pass: let Claude see the short report as extra context.
        reply = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": report,
            }
        }
    else:
        # Fail: "decision": "block" sends the reason back to Claude to fix.
        reply = {
            "decision": "block",
            "reason": report + "\n\nFix the reference list and write the file again.",
        }
    print(json.dumps(reply))
    sys.exit(0)


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--hook":
        run_as_hook()
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    passed, report = check(sys.argv[1])
    print(report)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
