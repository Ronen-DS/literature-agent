"""Turn PMID markers in a draft into numbered Vancouver citations.

Write the draft with [[pmid]] markers instead of numbers, e.g.

    NMD inhibition reshapes the immunopeptidome [[41956098]] and increases
    neoantigen presentation in small cell lung cancer [[42711693,41956098]].

Then run this script. It numbers the PMIDs in order of first appearance,
replaces each marker with [1], [2,5] or [3-6], and builds the reference list
from the screened CSV. Numbering 50+ references by hand goes wrong; this
cannot.

  python .claude/skills/review-writing/number_refs.py <draft-with-markers> <screened.csv> <output>
"""

import re
import sys
from pathlib import Path

from prepare import load_csv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MARKER = re.compile(r"\[\[([\d,\s]+)\]\]")


def format_numbers(numbers):
    """Format [1,2,3,7] as '1-3,7' (Vancouver collapses runs of three or more)."""
    numbers = sorted(set(numbers))
    parts, run = [], [numbers[0]]
    for number in numbers[1:]:
        if number == run[-1] + 1:
            run.append(number)
        else:
            parts.append(run)
            run = [number]
    parts.append(run)

    pieces = []
    for run in parts:
        if len(run) >= 3:
            pieces.append(f"{run[0]}-{run[-1]}")
        else:
            pieces.extend(str(n) for n in run)
    return ",".join(pieces)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    draft_path, csv_path, out_path = (Path(p) for p in sys.argv[1:])

    text = draft_path.read_text(encoding="utf-8")
    rows = {r["pmid"]: r for r in load_csv(csv_path)}

    # Walk the markers in order and give each new PMID the next number.
    numbers = {}
    missing = []

    def replace(match):
        pmids = [p.strip() for p in match.group(1).split(",") if p.strip()]
        out = []
        for pmid in pmids:
            if pmid not in rows:
                missing.append(pmid)
            if pmid not in numbers:
                numbers[pmid] = len(numbers) + 1
            out.append(numbers[pmid])
        return f"[{format_numbers(out)}]"

    body = MARKER.sub(replace, text)

    if missing:
        sys.exit(
            "These PMIDs are not in the CSV, so they cannot be cited:\n  "
            + "\n  ".join(sorted(set(missing)))
        )

    # Build the reference list in numbered order.
    lines = ["", "## References", ""]
    for pmid, number in sorted(numbers.items(), key=lambda kv: kv[1]):
        row = rows[pmid]
        title = row["title"].rstrip(".")
        lines.append(
            f"{number}. {row['first_author']}, et al. {title}. "
            f"{row['journal']}. {row['year']}. PMID: {pmid}"
        )

    out_path.write_text(body.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Numbered {len(numbers)} references -> {out_path}")


if __name__ == "__main__":
    main()
