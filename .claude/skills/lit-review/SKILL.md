---
name: lit-review
description: Run the full literature-review pipeline for one review question - PubMed searches, merge, screening, review writing with checked references, and a short final report.
argument-hint: "[review question]"
disable-model-invocation: true
allowed-tools:
  - Skill(pubmed-search)
  - Skill(review-writing)
  - Bash(python .claude/skills/review-writing/prepare.py:*)
  - Bash(python .claude/skills/review-writing/number_refs.py:*)
  - Bash(python .claude/skills/review-writing/check_refs.py:*)
---

# /lit-review: full pipeline

Review question: **$ARGUMENTS**

Run the steps below **in order**. Run all commands from the project folder.

## Stop rule (applies to every step)

If a step fails, **stop**. Don't start the next step and don't work around the
failure. Then report:
- which step failed, and the exact error or symptom, explained in plain language;
- what the earlier steps produced (counts and file paths);
- what you think the fix is, so the user can decide.

A step **fails** if any of these happen:
- a script exits with an error;
- a step produces no usable output (0 papers saved, 0 papers kept,
  0 `include` papers, or a missing file);
- the screener reports something went wrong;
- a check you are told to fix and rerun still fails after you have honestly
  fixed what it reports.

Never edit a script, the CSV, or the decisions to get past a failure. Never
fill a gap from memory.

## Step 0: Check the question

- If the question above is empty, stop and ask the user for one.
- Restate it in one sentence and check it against the research scope in
  CLAUDE.md. If it falls outside the scope, stop and say why.
- Choose a short kebab-case topic label for the file names, e.g.
  `neoantigen-presentation`.

## Step 1: Search PubMed (2-3 queries)

Use the `pubmed-search` skill. Run **2 or 3** queries for recall: one narrow
query, and one or two broader ones. Each broader query keeps one concept as a
strict anchor and widens the other (see "Recall" in that skill). Give each
query its own `--topic`, e.g. `<label>-narrow` and `<label>-broad`.

For each query, record the query string, the total match count, how many papers
were saved, and the results file path. If a query's match count is far too
large or too small, adjust it as the skill says. That is normal refining, not a
failure.

## Step 2: Merge (and filter)

Merge all the step-1 results files into one set with `screen.py`. It removes
duplicate PMIDs, then applies the age and citation filters and adds journal
metrics:

```
python .claude/skills/paper-screening/screen.py results/<file-a>.json results/<file-b>.json [results/<file-c>.json] --out <label>-combined
```

Record what it prints: loaded, duplicates removed, removed by age, removed by
citations, kept because recent, and kept. The output is
`results/<today>_<label>-combined_filtered.json`.

## Step 3: Screen (screener subagent)

Launch the `screener` subagent with the Agent tool. Give it the path of the
`_filtered.json` from step 2, and tell it the file is already filtered, so it
must **not** run `screen.py` again. Also give it the review question for
context. Tell it that the scope in CLAUDE.md is still what it judges against.

It returns a short summary and the CSV path. Record the include / maybe /
exclude totals, and confirm that the CSV
`results/<today>_<label>-combined_screened.csv` exists.

## Step 4: Write the review and references JSON

Use the `review-writing` skill with the CSV from step 3 and the review question
above. Follow **all** its steps, including:
- `check_refs.py` must pass on the draft;
- the .docx goes to `results/<today>_<label>_review.docx`;
- the references go to `results/<today>_<label>_references.json`. **Write this
  file with the Write tool**, so the citation hook (`check_citations.py`)
  checks it.

If the hook blocks the write, fix the reference list (and the review, if a
citation in it is wrong), then write the file again. If it still fails, apply
the stop rule. If the review needs `maybe` papers, the hook will reject them.
Stop and ask the user rather than dropping or forcing them.

## Step 5: Final report

Keep it short:

- **Question** as you understood it, and the topic label.
- **Search**: each query with its match count and papers saved.
- **Merge/filter**: loaded → duplicates removed → removed by age → removed by
  citations → kept.
- **Screening**: include / maybe / exclude.
- **Review**: papers cited, body word count, the themes.
- **Citation check**: the `check_refs.py` result and the hook's
  `check_citations.py` result (PASS, or the problems).
- **Files**: the .docx path, the references JSON path, and the screened CSV path.
- **Gaps**: anything the retrieved literature could not answer.
