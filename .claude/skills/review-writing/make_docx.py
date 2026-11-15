"""Convert a finished review draft (markdown) into a Word .docx.

The draft is the output of number_refs.py, so citations are already numbers
like [1] or [2,5] and the reference list is plain numbered lines.

This handles only the small amount of markdown the review format uses:
  # Heading      -> Heading 1 (the title)
  ## Heading     -> Heading 2 (section headings)
  blank line     -> paragraph break
  everything else-> a normal paragraph

Reference lines keep their numbers as literal text (not a Word auto-numbered
list), so the numbers can never drift out of step with the in-text citations.

Run from the project folder:
  python .claude/skills/review-writing/make_docx.py <draft.md> results/<name>_review.docx

Needs python-docx (in requirements.txt): pip install python-docx
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    draft_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])

    text = draft_path.read_text(encoding="utf-8")
    document = Document()

    # Use a serif body font at a readable size.
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    headings = 0
    references = 0
    in_references = False

    for block in text.split("\n"):
        line = block.rstrip()
        if not line:
            continue

        if line.startswith("## "):
            document.add_heading(line[3:].strip(), level=2)
            headings += 1
            in_references = line[3:].strip().lower() == "references"
        elif line.startswith("# "):
            document.add_heading(line[2:].strip(), level=1)
            headings += 1
        else:
            document.add_paragraph(line)
            if in_references and re.match(r"^\d+\.\s", line):
                references += 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(out_path)

    # Check nothing was left half-converted.
    leftovers = []
    if "[[" in text:
        leftovers.append("unconverted [[pmid]] markers")
    if leftovers:
        print("WARNING:", ", ".join(leftovers))

    print(f"Wrote {out_path}")
    print(f"Headings: {headings}; reference entries: {references}")


if __name__ == "__main__":
    main()
