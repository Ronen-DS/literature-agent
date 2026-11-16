# Literature Review Agent

An AI agent that searches PubMed, screens the results for relevance, and writes a
cited narrative literature review — with a hard guarantee that every citation
corresponds to a paper it actually retrieved.

Built for biomedical research, currently scoped to HLA immunopeptidomics,
neoantigens, T-cell receptors, and T-cell based cancer immunotherapy.

## The problem

A thorough literature review takes a researcher one to three weeks. Most of that
time is not writing. It is retrieval and triage: building searches that find the
right papers without drowning in irrelevant ones, reading hundreds of abstracts
to decide what matters, tracking which paper said what, and keeping the citations
straight. The writing is the last and smallest part.

Large language models are good at exactly the judgment-heavy middle of that
process, and catastrophically bad at the bookkeeping: they invent plausible
papers, misattribute findings, and produce citations that do not exist. A review
with one fabricated reference is worse than no review, because it has to be
checked line by line anyway.

This project is an attempt to get the speed without the fabrication, by splitting
the work between deterministic scripts and model judgment, and then mechanically
verifying the result.

## What it does

From a single command and a review question, the agent:

1. **Searches PubMed** via NCBI E-utilities, running several complementary
   queries rather than one, because a single query reliably misses in-scope work.
2. **Merges** the result sets, removing duplicate PMIDs.
3. **Filters** by publication age and citation count, and annotates each paper
   with its journal's OpenAlex 2-year mean citedness.
4. **Screens** every surviving abstract against a written research scope,
   recording include / maybe / exclude with a reason, a subtopic and a study type.
5. **Writes** a themed narrative review of 3,000–5,000 words with Vancouver
   numbered citations, organised by theme rather than paper by paper.
6. **Verifies** every citation against the screening results, and refuses to
   hand over a review that fails.

Output is a Word document, a machine-checkable JSON reference list, and a CSV of
every screening decision.

## The pipeline

```
  review question
        │
        ▼
  ┌───────────┐   2–3 complementary PubMed queries
  │  SEARCH   │   (narrow + broader; recall over precision)
  └─────┬─────┘   →  results/<date>_<topic>.json
        │
        ▼
  ┌───────────┐   dedupe by PMID, filter by age + citations,
  │   MERGE   │   add journal metric from OpenAlex
  └─────┬─────┘   →  ..._filtered.json
        │
        ▼
  ┌───────────┐   every abstract judged against the research scope
  │  SCREEN   │   include / maybe / exclude + reason + subtopic
  └─────┬─────┘   →  ..._screened.csv
        │
        ▼
  ┌───────────┐   pick papers, group into themes, draft with
  │   WRITE   │   [[pmid]] markers, then auto-number references
  └─────┬─────┘   →  ..._review.docx  +  ..._references.json
        │
        ▼
  ┌───────────┐   every cited PMID must exist in the CSV as "include"
  │   CHECK   │   enforced by a hook — a failure blocks and reports back
  └───────────┘
```

Each stage writes a file the next stage reads, so any run can be inspected,
resumed, or audited after the fact.

## How to run it

Requires [Claude Code](https://claude.com/claude-code) and Python 3.

```bash
git clone <this repo>
cd lit-review-agent
pip install -r requirements.txt
```

Optionally add an NCBI API key to a local `.env` file to raise the PubMed rate
limit from 3 to 10 requests/second:

```
NCBI_API_KEY=your_key_here
```

Then open Claude Code in the project folder and run:

```
/lit-review What is the contribution of proteasome-spliced peptides to the HLA class I immunopeptidome?
```

That runs the whole pipeline in order and reports counts at each step, the output
paths, and the citation-check result. The individual stages are also available on
their own (`pubmed-search`, `paper-screening`, `review-writing`) when a search
needs refining or a review needs rewriting from an existing screening CSV.

See [`examples/`](examples/) for a complete run with real numbers.

## Design choices

**Scripts for exact steps, the model for judgment.** Anything with a correct
answer is a Python script: query construction is the model's job, but pagination,
deduplication, citation counting, reference numbering and citation checking are
not. Reference numbering is the clearest case — numbering 51 references in order
of first appearance by hand goes wrong, so the model writes `[[41956098]]`
markers and a script converts them to `[1]`, `[2,5]`, `[3-6]` and builds the
reference list from the retrieved records. The model never types a reference.

**A least-privilege screening subagent.** Screening 350 abstracts would flood the
main conversation and crowd out the review-writing context. A dedicated
`screener` subagent does it with only `Read`, `Write` and `Bash` — no web access,
no ability to spawn further agents — and returns a ~20-line summary with counts
and a CSV path. The abstracts stay out of the main thread entirely.

**A citation-check hook, not a polite request.** Asking a model to check its own
citations does not scale, because the request can be forgotten or rationalised.
Instead a `PostToolUse` hook fires whenever a `*_references.json` file is
written, runs `check_citations.py`, and on failure **blocks the write** and sends
the failure report back to the model to fix. The check is enforced by the harness
rather than by the model's good intentions:

```
FAIL - 1 problem(s):
  - Reference 52: PMID 99999999 is NOT in the screened CSV.
    It may be an invented paper - remove it.
```

A second checker, `check_refs.py`, validates the draft itself: PMIDs against the
CSV, in-text citations against the reference list, Vancouver numbering order,
preprints whose published version is also available, and word count.

**An explicit stop rule.** The `/lit-review` command instructs the agent to stop
and report rather than continue past a failure, and defines failure concretely: a
script error, zero usable output, a screener problem, or a check that still fails
after an honest fix attempt. It also forbids the tempting workarounds — editing a
script, the CSV or the decisions to make a check pass, or filling an evidence gap
from memory. This matters more than it sounds: on one run the pipeline correctly
stopped before writing, because the retrieved evidence could not support the
question asked.

**Narrow permissions, checked in.** `.claude/settings.json` allows exactly the
project's own scripts and the web tools, so routine runs do not generate
permission prompts while anything unusual still does. Destructive operations are
not allowed at all.

**Accuracy rules in writing.** `CLAUDE.md` states the research scope and the
accuracy rules — never invent papers or findings, cite only retrieved papers,
every claim carries a citation, describe each paper only from its abstract, and
say so plainly when evidence is thin or conflicting. These are loaded into every
session.

## Limitations

Stated plainly, because they bound what the output is worth.

- **Abstract-only judgment.** Screening and writing both work from titles and
  abstracts, never full text. An abstract that omits a method or overstates a
  result will mislead the agent exactly as it would mislead a human skimming.
- **The citation filter is a popularity proxy.** Papers with fewer than 50 iCite
  citations are dropped unless published within the last 12 months. This is a
  blunt instrument that penalises good work in small subfields and recent work
  just past the exemption window.
- **The date window can remove a field's foundations.** The default keeps the
  current calendar year plus the five before it. For fast-moving topics this is
  right; for a topic whose defining papers and central controversy are older, it
  silently removes the evidence that matters. This happened on a real run and the
  agent reported it rather than papering over it — but it is a property of the
  design, and the window needs adjusting per question.
- **Reviews are reviews, not meta-analyses.** No effect sizes are pooled, no
  study quality is appraised beyond study type, and no risk-of-bias assessment is
  performed.
- **PubMed/MEDLINE only.** No bioRxiv, Scopus, Web of Science or Google Scholar.
  Preprints appear only when indexed in PubMed, and the pipeline detects
  preprint/published duplicate pairs by title similarity rather than by a
  registry link.
- **Requires Claude Code.** The pipeline is built on Claude Code's skills,
  subagents and hooks. The Python scripts run standalone, but the orchestration
  and judgment steps do not.
- **One domain at a time.** The research scope in `CLAUDE.md` is specific to
  immunopeptidomics and neoantigen biology. Other fields need that file rewritten
  and the suggested search vocabulary replaced.

## Cost and run time

Measured on one screening subagent run (32 papers): ~47,000 tokens and about
2.5 minutes. Extrapolating from that, a large run of the kind in `examples/`
(1,048 search hits, 355 screened abstracts, a 4,000-word review) is on the order
of several hundred thousand to roughly a million tokens, and tens of minutes of
wall-clock time, most of it in screening. A narrow question with ~30 surviving
papers is perhaps a fifth of that.

Translating tokens into money depends on your model and plan — a Claude
subscription is not billed per token, API access is — so see
[Anthropic's pricing](https://www.anthropic.com/pricing) rather than trusting a
figure hard-coded here. PubMed and OpenAlex are free; OpenAlex runs on a small
shared daily budget without a key.

## Planned extensions

- **Full-text retrieval** for open-access papers via PubMed Central, so claims
  can be checked against methods and results rather than abstracts.
- **A weekly digest**: a scheduled run that reports only what is new since the
  last run on a standing set of questions.
- **Grant adaptation**: convert a finished review into the background and
  significance sections of a grant application, with the citations carried
  across intact.
- **An SDK version** that runs outside Claude Code, so the pipeline can be
  triggered from CI or a web service, with the hook reimplemented as an
  in-process check.

## Repository layout

```
.claude/
  settings.json              permissions + the citation-check hook
  agents/screener.md         least-privilege screening subagent
  skills/
    lit-review/              /lit-review — runs the whole pipeline
    pubmed-search/           query construction + search.py
    paper-screening/         screen.py (filters, metrics), make_csv.py
    review-writing/          prepare.py, number_refs.py, check_refs.py,
                             check_citations.py, make_docx.py
CLAUDE.md                    research scope, accuracy rules, conventions
examples/                    a complete worked run
requirements.txt
```

`results/` and `scratch/` are git-ignored: runs are reproducible from the scripts,
and the outputs are large.

## License

MIT — see [LICENSE](LICENSE).
