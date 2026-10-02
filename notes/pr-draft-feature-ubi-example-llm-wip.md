# PR Draft: UBI Example with Iterative LLM Conversation

## Title
WIP: Add iterative two-agent UBI example with reproducibility test harness

## Summary
This PR adds a new UBI example workflow under `tests/examples/ubi/` to support iterative LLM-mediated agent conversations and reproducibility checks.

The example is intended as a stepping stone for refactoring Climate-Action-GABM patterns into core GABM in a more general form.

## What Changed
- Added example runner at `tests/examples/ubi/run.py`.
- Added colocated UBI fixture data at `tests/examples/ubi/data/input/people_ubi.csv`.
- Added optional transcript capture (JSONL) for full prompt/response audit trails.
- Added support for multiple backends in the example:
  - deterministic `mock` backend (default, test-safe)
  - service providers (`openai`, `genai`, `deepseek`, `publicai`)
  - local OpenAI-compatible endpoint (`local-openai`) for HPC/local model workflows
- Added unit tests at `tests/src/gabm/test_ubi_example.py` to assert reproducibility and expected summary fields.
- Updated documentation guidance for test fixture placement (test data under tests tree).

## Why
- Enable deterministic development/testing while preserving an easy path to HPC/local-LLM reproducibility runs.
- Keep all assets for each example together (`tests/examples/ubi/...`) so additional examples can be added cleanly.
- Provide auditable outputs that make cross-environment reproducibility checks straightforward.

## Reproducibility Workflow
- Local development: run with hosted service providers to iterate quickly.
- HPC validation: run with `--provider local-openai` against a pinned local model/server.
- Compare signatures and JSONL transcripts between repeated runs.

## Example Commands
```bash
# deterministic baseline
python tests/examples/ubi/run.py --write-transcript

# local OpenAI-compatible server run (HPC)
python tests/examples/ubi/run.py \
  --provider local-openai \
  --model <LOCAL_MODEL_ID> \
  --local-base-url http://localhost:8080/v1 \
  --write-transcript
```

## Current Scope / Limitations
- Conversation loop currently uses the first two agents only.
- Opinion update parsing is constrained to UBI values in `{-1, 0, 1}`.
- This is intentionally a WIP branch and not ready for merge into `main`.

## Validation Performed
- Example runner executes successfully with transcript output.
- Unit tests pass:
  - `pytest -q tests/src/gabm/test_ubi_example.py`

## Follow-up Work (Planned)
- Expand from first pair to broader pairing/selection strategies.
- Introduce richer persona/prompt assembly abstractions.
- Add transcript comparison utility for automated drift detection across runs.
- Align/abstract conversation pipeline with Climate-Action-GABM reusable components.
