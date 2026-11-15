---
name: review-writing
description: Write a narrative literature review from a screened CSV made by the paper-screening skill. Selects the papers relevant to a specific review question, organises them by theme, writes 3,000-5,000 words with Vancouver citations, checks every citation against the CSV, and saves a Word document plus a checked _references.json to results/. Use after paper-screening, when the user asks for a review to be written.
---

# Review writing

Input: a screened CSV from the `paper-screening` skill, e.g.
`results/2026-11-06_my-topic_screened.csv`, plus its `_filtered.json`
(same folder, same name, which holds the abstracts).

You also need **the specific review question**. If the user hasn't given one,
ask before writing — the CSV usually covers a broader scope than any single
review, and the question decides which papers belong. Don't invent one.

Run all commands from the project folder.

## Step 1: See the candidates

```
python .claude/skills/review-writing/prepare.py results/<file>_screened.csv
```

This prints every paper judged `include`, grouped by subtopic, one line each
(PMID, year, journal, journal metric, study type, title, screening reason).

It also prints **preprint/journal duplicate pairs** as `<preprint> -> <published>`.
Cite the published version and never both.

Add `--include-maybe` to also offer the `maybe` papers. Use this when the
question reaches into territory the screener wasn't sure about; say so to the
user, because `maybe` papers are a weaker basis for a claim.

## Step 2: Choose the papers for this question

From the stage-1 list, pick the papers that bear on **this** question, by PMID.
Judge from the title and the screening reason. A good narrative review of
3,000-5,000 words cites roughly **40-80 papers**; more than that and you are
summarising paper-by-paper rather than synthesising.

Prefer, in this order:
1. papers that answer the question directly;
2. original research and method papers over reviews (cite reviews for
   background and for claims about the state of a field);
3. recent work, and papers in higher-metric journals where the choice is
   otherwise even.

Save the chosen PMIDs, one per line, to the scratchpad (not `results/`) so the
run is repeatable, then read their abstracts:

```
python .claude/skills/review-writing/prepare.py results/<file>_screened.csv --abstracts <scratchpad>/selected.txt
```

Read every abstract you are about to cite. If an abstract turns out not to
support the claim you had in mind, drop the paper — do not stretch it.

## Step 3: Plan the themes

Group the chosen papers into 4-6 themes, each becoming a section. Themes are
**questions or findings**, not methods lists: "Where non-canonical neoantigens
come from" beats "Mass spectrometry papers".

Write the plan down before drafting: for each theme, the papers in it and the
one or two sentences it contributes. Note where papers disagree — a
disagreement is worth more words than another agreeing citation.

## Step 4: Write the draft

Save to the scratchpad as markdown, e.g. `<scratchpad>/draft_markers.md`.

**Write citations as `[[pmid]]` markers, not numbers**, e.g.
`NMD inhibition reshapes the immunopeptidome [[41956098]]` or
`[[42711693,41956098]]` for two papers at once. Numbering 50 references by hand
in first-appearance order goes wrong; step 4b does it for you.

Structure (from CLAUDE.md):
- **Introduction** — the question, why it matters, what the review covers.
- **Thematic sections** — one per theme from step 3.
- **Gaps & future directions** — what the retrieved literature does not settle.
- **Conclusion**.
- **References** — under a `## References` heading.

Rules:
- **3,000-5,000 words**, excluding references.
- **Synthesise**: each paragraph should make a point that draws on several
  papers, not walk through one paper at a time.
- **Every claim from the literature carries a citation**, written as a
  `[[pmid]]` marker.
- **Cite only PMIDs in the CSV.** Never add a paper from memory, however
  well-known, and never invent an author, year, finding or title. If something
  important is missing from the CSV, say so in "Gaps" or run another search with
  the `pubmed-search` skill — do not fill the hole from memory.
- Describe each paper only from its abstract. Do not assume a method or result
  the abstract doesn't state.
- Where the evidence is thin, conflicting or rests on `maybe` papers, say so in
  the text ("one small study", "evidence is limited to two cohorts").

Do not write a References section yourself; step 4b builds it.

## Step 4b: Number the citations (script)

```
python .claude/skills/review-writing/number_refs.py <scratchpad>/draft_markers.md results/<file>_screened.csv <scratchpad>/draft.md
```

This numbers the PMIDs in order of first appearance, replaces each marker with
`[1]`, `[2,5]` or `[3-6]`, and appends a `## References` section built from the
CSV, so every reference's authors, title, journal and year come from the
retrieved record rather than from memory. It refuses to run if a marker holds a
PMID that is not in the CSV.

## Step 5: Check the citations

```
python .claude/skills/review-writing/check_refs.py <scratchpad>/draft.md results/<file>_screened.csv
```

It fails on: a PMID not in the CSV, a reference with no PMID, an `exclude`d
paper, a preprint whose published version exists, an in-text `[n]` with no
reference (or the reverse), numbering out of first-appearance order, and a word
count outside 3,000-5,000.

Fix every problem and run it again until it passes. Do not hand over a draft
that fails this check, and never change the script to make a draft pass.

## Step 6: Make the Word document

Use the `docx` skill to convert the finished markdown into a Word document at
`results/<date>_<topic>_review.docx`. Keep the heading structure, and keep the
reference numbers as literal text (not an auto-numbered list) so they always
match the in-text citations.

Notes for this machine, found on the first run:
- `pandoc` is not installed, so the markdown cannot be converted directly.
- The `docx` npm package is not preinstalled either. Run `npm install docx` in
  the scratchpad directory and write the conversion script there, so no Node
  packages land in the project.
- The docx skill's visual check does not work here: `pdftoppm` is missing and
  its LibreOffice helper needs Unix sockets. Verify the file instead by reading
  `word/document.xml` out of the .docx with Python's `zipfile` and confirming
  the heading count, the reference count, and that no `[[pmid]]` markers or `##`
  characters survived.

## Step 7: Save the reference list as JSON (always)

Every review gets a reference list saved next to its .docx, with the same name
ending in `_references.json`, e.g.
`results/2026-11-06_my-topic_review.docx` →
`results/2026-11-06_my-topic_references.json`. It records which screened CSV
the references came from, so the citations can be re-checked at any time.

Build it from the `## References` section of the final numbered draft, in the
same order, one entry per reference. Take each DOI from the `_filtered.json`
next to the CSV; never type a DOI from memory (leave `"doi": ""` if it has none).

```json
{
  "review": "results/2026-11-06_my-topic_review.docx",
  "screened_csv": "results/2026-11-06_my-topic_screened.csv",
  "references": [
    {"number": 1, "pmid": "37328642", "doi": "10.1038/s41571-023-00789-4",
     "citation": "Yang K, et al. Antigen presentation in cancer ... 2023. PMID: 37328642"}
  ]
}
```

**Write this file with the Write tool**, not from a Python script. A hook in
`.claude/settings.json` runs `check_citations.py` after every Write to a
`*_references.json` file. If any reference has no PMID, a PMID is not in the
CSV, or a paper's decision is not `include`, the hook blocks and sends the
failure report back. Fix the reference list (and the review, if a citation in
it is wrong) and write the file again until it passes. Never edit the CSV or
the script to make it pass.

To run the same check by hand:

```
python .claude/skills/review-writing/check_citations.py results/<name>_references.json
```

Note that this check accepts only `include` papers. If the review cites a
`maybe` paper, the check will fail on it. Tell the user, and don't hand over
the review until they have decided how to handle it.

## Report to the user

- the review question as you understood it;
- how many papers were available, how many you cited, and whether any `maybe`
  papers were used;
- the themes you organised it under;
- the word count and that the citation check passed;
- the path to the .docx, the `_references.json` (and that its check passed),
  and the markdown draft;
- anything the literature in the CSV could not answer.
