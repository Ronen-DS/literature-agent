---
name: pubmed-search
description: Find PubMed papers for a literature review within the research scope defined in CLAUDE.md (immunopeptidomics / HLA peptidomics, neoantigens, TCRs and TCR-neoantigen reactivity, T-cell cancer immunotherapy). Use when a review question needs papers retrieved, a search needs refining, or more references are needed. Turns the question into a PubMed query, runs search.py, and saves results to results/.
---

# PubMed search

Use this skill to collect papers for a review question. Only papers saved by
this process may be cited (see Accuracy rules in CLAUDE.md).

## 1. Turn the question into a PubMed query

1. **Restate the question** in one sentence and check it fits the research
   scope in CLAUDE.md. If it drifts outside the scope, say so before searching.
2. **Split it into 2-3 key concepts.** Example: "How accurate are MS-based
   immunopeptidomics methods for finding neoantigens?" gives
   (a) immunopeptidomics, (b) neoantigens.
3. **List synonyms for each concept.** Start from the suggested terms in
   CLAUDE.md and add MeSH terms where they exist:
   - immunopeptidomics: `immunopeptidom*`, `"HLA ligandome"`, `"MHC-bound peptides"`, `"HLA peptidomics"`
   - neoantigens: `neoantigen*`, `neoepitope*`, `"Antigens, Neoplasm"[MeSH Terms]`
   - TCRs: `"TCR repertoire"`, `"TCR-pMHC"`, `"Receptors, Antigen, T-Cell"[MeSH Terms]`
   - T-cell therapy: `"TCR-T"`, `"tumor-infiltrating lymphocytes"`, `"neoantigen vaccine*"`
4. **Combine them:** join synonyms with `OR` inside brackets, and join concepts
   with `AND`:
   ```
   (immunopeptidom*[tiab] OR "HLA ligandome"[tiab] OR "MHC-bound peptides"[tiab])
   AND (neoantigen*[tiab] OR neoepitope*[tiab] OR "Antigens, Neoplasm"[MeSH Terms])
   ```
   - `[tiab]` = search title and abstract; `[MeSH Terms]` = PubMed's subject index.
   - `*` matches word endings (neoantigen, neoantigens).
   - Add `AND review[pt]` to find only reviews, or `NOT review[pt]` to skip them.
   - Avoid `NOT` for the transplantation exclusion; it can drop relevant papers.
     Screen those out by reading instead (step 3).

## 2. Run the search

Run from the project folder:

```
python search.py "<query>" --max 20 --topic <short-label>
```

Options:
- `--max N`: how many papers to save (default 20), best matches first.
- `--mindate YYYY` / `--maxdate YYYY`: limit by publication date (YYYY/MM/DD also works).
- `--topic label`: short name for the output file (otherwise taken from the query).

Example:
```
python search.py "(immunopeptidom*[tiab] OR \"HLA ligandome\"[tiab]) AND neoantigen*[tiab]" --max 30 --mindate 2018 --topic immunopeptidomics-neoantigens
```

**Check the match count first.** The script prints how many papers match in
total. If it's in the thousands, narrow the query (more specific terms, a date
range, `[tiab]` tags). If there are fewer than about 10, broaden it (more
synonyms, drop a concept). Rerunning is fine; files from the same day get `_2`,
`_3` added instead of being overwritten.

## 3. Check and save the results

Results are written to `results/<date>_<short-topic>.json`, containing the query,
date range, total matches, and a `papers` list where each paper has:
`pmid`, `title`, `authors`, `journal`, `year`, `pub_date` (YYYY-MM-DD), `abstract`, `doi`.

To filter by citations and journal metrics and screen for relevance, use the
`paper-screening` skill next.

After each search:
1. Read the titles and abstracts and **screen against the scope** in CLAUDE.md.
   Drop off-topic papers (e.g. HLA used only for transplant matching or disease
   association) and note why.
2. Tell the user the query used, the total match count, how many papers were
   saved, how many look relevant, and the result file path.
3. Keep the PMID and DOI of every paper you use; they are the citation source
   of truth. Never cite a paper that isn't in a results file.
4. If evidence looks thin, run another search with different synonyms rather
   than filling gaps from memory.
