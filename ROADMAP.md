# Roadmap


## Table of Contents
1. [Overview](#overview)
2. [1.0](#10)
3. [0.4](#04)


## Overview
This file outlines planned next steps and future goals.


## 1.0
- Criteria and features to be determined...


## 0.4
- Fix any reported bugs.
- Add platform-agnostic reproducibility comparison tooling in Python.
- Translate Calder comparison helpers from shell to Python CLI tools with feature parity:
	- `scripts/hpc/calder/compare_chat_runs.sh`
	- `scripts/hpc/calder/generate_concurrency_rows.sh`
- Package Python comparison tools so they can run on Linux/macOS/Windows (including non-HPC environments).
- Add tests for comparison outputs (determinism summaries, metadata normalization, markdown row generation).
- Document user-facing workflows for local and HPC run comparison in the user guide.