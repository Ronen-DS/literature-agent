# Lit Review Agent

## Project
- AI agent that searches academic papers and writes literature reviews.
- Later phase: adapt finished reviews into grant proposal background/significance sections.
- Field: biomedical / life sciences.

## Research scope
- Core topics: HLA peptidomics / immunopeptidomics (mass spectrometry of HLA-bound peptides), neoantigen identification and prediction, TCR identification and TCR reactivity to neoantigens, and T-cell based cancer immunotherapy (e.g. TCR-T, TIL, neoantigen vaccines).
- Include: original research and reviews linking these topics, both computational and experimental methods.
- Exclude: papers on HLA only for transplantation matching or disease-association typing, unless they involve peptide presentation or T-cell recognition.
- Suggested search terms: immunopeptidome, HLA ligandome, MHC-bound peptides, neoantigen, neoepitope, TCR repertoire, TCR-pMHC, T cell reactivity, HLA class I, HLA class II.
- Each review's specific question will be given in the prompt; stay within this scope.

## Paper search
- Source: PubMed / MEDLINE only, via NCBI E-utilities (esearch, efetch, esummary).
- Respect NCBI rate limits: 3 requests/sec without an API key, 10/sec with one.
- Read the API key from the `NCBI_API_KEY` environment variable (stored in `.env`); never hard-code it.
- Keep PMIDs and DOIs for every paper; they are the source of truth for citations.

## Review output
- Default format: narrative review, ~3,000-5,000 words.
- Organize by themes, not paper-by-paper summaries; synthesize, compare, and note gaps.
- Typical structure: Introduction, thematic sections, Gaps & future directions, Conclusion, References.
- Citation style: Vancouver (numbered in order of first appearance, e.g. [1], [2-4]).

## Accuracy rules
- Never invent papers, authors, findings, or citations; cite only papers actually retrieved from PubMed.
- Every claim drawn from the literature must have a citation.
- If evidence is thin or conflicting, say so rather than overstating it.

## Code style (user is a Python beginner)
- Keep code simple and readable: plain functions, clear names, short files.
- Add brief comments explaining what each part does and why.
- Prefer few, well-known libraries (e.g. `requests`, `python-dotenv`).
- Explain how to run anything new, with exact commands.
- Explain errors in plain language before fixing them.

## Workflow
- Install packages with `pip install`; track them in `requirements.txt`.
- Commit with clear messages; do not push (git push is blocked in settings).
- Do not delete files with `rm` (blocked); ask the user instead.
