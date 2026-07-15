# Tool-selection regression harness (A/B)

A lightweight, **A/B** check for *which tool the model picks and how it fills the
key arguments*, given only this server's tool schemas + the `instructions=` block.
It complements the end-to-end accuracy suite in [`../rcsb_pdb_eval.xml`](../rcsb_pdb_eval.xml):
that one measures whether an agent can fully *answer* real PDB questions; this one
isolates the cheaper, earlier signal — **routing** — and is built to be run
**before vs. after** a change (e.g. a docstring trim) to catch behavioral drift the
schema can't show.

- `eval_cases.py` — natural-language prompts, each with a tolerant predicate over the
  model's first tool call. Cases target the gotchas most at risk when docstrings are
  shortened (ontology routing, `group_by` needs `polymer_entity`, `sort_by`
  sortability, the "empty result is valid" rule, strucmotif-vs-structure routing, …).
- `eval_run.py` — loads tools + instructions from any `--src` checkout, asks a model
  to act on each prompt, grades the first tool call, `--k` samples per case. Backends:
  `anthropic` (needs `ANTHROPIC_API_KEY`) or `openai` (any OpenAI-compatible endpoint,
  e.g. a local vLLM — usually no key). The RCSB API is never called; only the tool
  *decision* is graded.
- `eval_diff.py` — diffs two result files and prints only the deltas + a verdict.

## Running an A/B (before vs. after a change)

```bash
# from repo root; OLD = the committed state, NEW = your working tree
git worktree add /tmp/rcsb-old HEAD

python evals/tool_selection/eval_run.py --backend anthropic --model claude-haiku-4-5-20251001 \
    --temperature 1.0 --k 5 --src /tmp/rcsb-old/src --out /tmp/old.json
python evals/tool_selection/eval_run.py --backend anthropic --model claude-haiku-4-5-20251001 \
    --temperature 1.0 --k 5 --src src              --out /tmp/new.json
python evals/tool_selection/eval_diff.py /tmp/old.json /tmp/new.json

git worktree remove /tmp/rcsb-old
```

Point `--backend openai --base-url http://<host>:<port> --model <id>` at your target
(e.g. self-hosted) model — that's the run that matters for deployment, since small
models are the most sensitive to guidance thinned out of a docstring.

## How to read it

- It's a **regression** check: look for a case whose rate DROPS old→new. A case already
  <100% on both is a pre-existing model/predicate limitation, not caused by the change.
- Pick **Haiku** (or your target small model) — strong models are too forgiving to
  surface a subtle over-trim.
- Interpret **rates over K samples**, not single runs: tool selection is stochastic, so
  small single-sample flips (3/5↔4/5) are noise. Bump `--k` before believing a delta.
- It grades the **first tool call only** — a coarse routing signal, not end-to-end task
  success (that's what `../rcsb_pdb_eval.xml` is for).
- Grow `eval_cases.py` as you dedup: every load-bearing "keep" line you preserve should
  get a case that asserts the behavior it protects.

## The cheap deterministic gate

This harness needs a model + a key/endpoint, so it's a *deliberate* check, not a CI gate.
The CI gate is [`../../tests/test_tool_descriptions.py`](../../tests/test_tool_descriptions.py):
a free, deterministic `pytest` that asserts the load-bearing phrases still exist in each
tool description (or in the instructions block). Run that on every change; run this
harness at milestones.
