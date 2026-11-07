# Contributing

## Submitting a system

ProposalBench compares systems that write research proposals: bare models given one prompt,
agents and coding CLIs with tools, and grant-writing products. Model labs and tool makers are
welcome to submit theirs.

1. Open an issue with the **System submission** template: what the system is, how it is run
   (API, CLI or product), the exact version, and who can run it.
2. A system is described by a YAML file in [`configs/systems/`](configs/systems/). The kinds are
   `direct` (one request to a model API), `cli` (Claude Code or Codex, headless), `agent` (the
   open reference agent) and adapters for products that take a call and documents as input. A new
   kind needs a class in `src/proposalbench/systems/` and a test.
3. Every system receives exactly the bundle `pb tasks export <task_id>` writes, and nothing else:
   no task-specific settings, no access to the hidden `*.yaml` answer keys, no human editing. A
   product is run with the defaults its users get.
4. We agree on who generates the proposals (we run the system, or you send the outputs in the
   submission format of `src/proposalbench/systems/base.py`, with `meta.json`). Judging costs
   about $3 per proposal on the current panel; accepted submissions join the next scheduled run
   and are judged with the same panel and harness version as the published results.

A system built by the ProposalBench maintainers, or tuned on the public tasks, is reported only on
tasks it was not developed on, and the disclosure says so.

## Reporting a problem with a task or a score

Open an issue naming the task id, the system and sample, and the item or deduction in question.
Every change to tasks, rubrics or scoring that could favour or disfavour a participant is recorded
in [`docs/decision-log.md`](docs/decision-log.md) with its reason; changes that alter published
scores are released as a new version with the affected numbers recomputed.

## Code

```bash
uv sync
uv run ruff format && uv run ruff check
uv run pytest
```

Keep changes small and tested. Nothing in a pull request may call a paid API in the tests.
