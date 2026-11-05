---
name: paper-screening
description: Screen a results JSON from pubmed-search. Filters by publication age and iCite citation counts, adds an OpenAlex journal metric (2-year mean citedness), then has Claude judge each abstract against the research scope in CLAUDE.md (include / exclude / maybe, with reason, subtopic and study type). Produces a CSV in results/ sorted by journal metric. Use after pubmed-search, before writing a review.
---

# Paper screening

Input: a results file made by the `pubmed-search` skill, e.g.
`results/2026-11-04_my-topic.json`. Run all commands from the project folder.

## Step 1: Filters and metrics (script)

```
python .claude/skills/paper-screening/screen.py results/<file>.json
```

The script:
1. Keeps papers published in the last `YEARS_BACK` years (this calendar year
   and the 5 before it by default).
2. Gets citation counts from NIH iCite and removes papers with fewer than
   `MIN_CITATIONS` (50), **unless** published within the last
   `RECENT_MONTHS_EXEMPT` (12) months.
3. Adds the journal's OpenAlex 2-year mean citedness (similar to an impact
   factor), found by DOI, or by journal name if the DOI fails.
4. Prints how many papers were removed at each step and saves the kept papers
   to `results/<file>_filtered.json`.

The thresholds are settings at the top of `screen.py`. Check the "Matched by
name" lines it prints: a name match can pick the wrong journal.

Notes:
- iCite counts only citations from PubMed papers, so counts are lower than
  Google Scholar's. Papers iCite doesn't know yet count as 0 citations.
- OpenAlex works without a key on a small shared daily budget. If it stops
  responding, the user can get a free key at https://openalex.org/settings/api
  and add `OPENALEX_API_KEY=...` to `.env`. Never sign up for a key on the
  user's behalf.

## Step 2: Relevance screen (Claude)

Read `results/<file>_filtered.json`. For **every** paper, read the title and
abstract and judge it against the research scope in CLAUDE.md. Base each
judgement on the abstract only, not on what you remember about the paper.

For each paper record:
- **decision**: `include` (clearly within scope), `exclude` (out of scope, e.g.
  HLA only for transplant matching or disease-association typing, or no link to
  peptide presentation or T-cell recognition), or `maybe` (partly relevant, or
  the abstract is too vague to tell).
- **reason**: one line saying why.
- **subtopic**: the main one of `immunopeptidomics`, `neoantigen prediction`,
  `TCR identification`, `immunotherapy`. Use `other` only for excluded papers
  that fit none.
- **study_type**: `original research`, `review`, `method/tool` (main
  contribution is new software, an algorithm or a lab method), or `clinical`
  (patient trial or clinical cohort). Keep reviews; don't exclude a paper just
  because it is a review.

Write the decisions to `results/<file>_decisions.json`, keyed by PMID:

```json
{
  "12345678": {"decision": "include", "reason": "Identifies HLA-I neoantigens in melanoma by MS",
               "subtopic": "immunopeptidomics", "study_type": "original research"}
}
```

## Step 3: Make the CSV (script)

```
python .claude/skills/paper-screening/make_csv.py results/<file>_filtered.json results/<file>_decisions.json
```

This checks that every paper has a valid decision, then writes
`results/<file>_screened.csv` sorted by journal metric (highest first), with
columns: pmid, title, first_author, journal, year, citations, journal_metric,
decision, reason, subtopic, study_type, pubmed_link.

## Report to the user

Tell the user:
- the counts at each step (loaded, removed by age, removed by citations, kept
  because recent, final count), and the include / maybe / exclude totals;
- the top included papers (title, first author, journal, year, citations,
  metric);
- any "Matched by name" journal lookups or papers with no metric;
- the CSV path.
