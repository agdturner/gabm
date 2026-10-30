#!/usr/bin/env bash
#
# Compare two GABM Calder chat run outputs and report exact-match status.
#
# Examples:
#   scripts/hpc/calder/compare_chat_runs.sh --run-a 494869 --run-b 494970
#   scripts/hpc/calder/compare_chat_runs.sh --run-a /path/to/run_494869 --run-b /path/to/run_494970
#
# A run value can be:
#   - a numeric Slurm job ID (e.g., 494869)
#   - a run directory name (e.g., run_494869)
#   - an absolute/relative filesystem path to the run directory

set -euo pipefail

WORKING_DIR="/flash-calder/users/${USER}/gabm"
RUN_A=""
RUN_B=""

usage() {
  cat <<'USAGE'
Usage:
  scripts/hpc/calder/compare_chat_runs.sh --run-a <run|jobid|path> --run-b <run|jobid|path> [--working-dir <path>]

Options:
  --run-a        First run identifier/path.
  --run-b        Second run identifier/path.
  --working-dir  Base working directory used for job-id/run-name resolution.
  -h, --help     Show this help message.
USAGE
}

resolve_run_path() {
  local value="$1"
  local candidate=""

  if [[ -d "$value" ]]; then
    candidate="$value"
  elif [[ "$value" =~ ^[0-9]+$ ]]; then
    candidate="${WORKING_DIR}/gabm_runs/run_${value}"
  elif [[ "$value" =~ ^run_[0-9]+$ ]]; then
    candidate="${WORKING_DIR}/gabm_runs/${value}"
  else
    candidate="$value"
  fi

  if [[ ! -d "$candidate" ]]; then
    echo "Run directory not found: $candidate" >&2
    exit 1
  fi

  realpath "$candidate"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-a)
      [[ -z "${2:-}" ]] && { echo "Missing value for --run-a" >&2; exit 1; }
      RUN_A="$2"
      shift 2
      ;;
    --run-b)
      [[ -z "${2:-}" ]] && { echo "Missing value for --run-b" >&2; exit 1; }
      RUN_B="$2"
      shift 2
      ;;
    --working-dir)
      [[ -z "${2:-}" ]] && { echo "Missing value for --working-dir" >&2; exit 1; }
      WORKING_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$RUN_A" || -z "$RUN_B" ]]; then
  usage
  exit 1
fi

RUN_A_PATH="$(resolve_run_path "$RUN_A")"
RUN_B_PATH="$(resolve_run_path "$RUN_B")"

echo "Comparing runs:"
echo "  A: ${RUN_A_PATH}"
echo "  B: ${RUN_B_PATH}"

python3 - "$RUN_A_PATH" "$RUN_B_PATH" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

run_a = Path(sys.argv[1])
run_b = Path(sys.argv[2])

VOLATILE_METADATA_KEYS = {
    "created_at",
    "run_dir",
    "cache_jsonl_path",
}


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_normalized_metadata(path: Path):
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return data
    return {k: v for k, v in sorted(data.items()) if k not in VOLATILE_METADATA_KEYS}


def discover_runs(root: Path):
    # Concurrency launcher outputs to <run>/clients/<run_id>/..., while older runs
    # can write directly under <run>/<run_id>/....
    base = root / "clients" if (root / "clients").is_dir() else root
    found = {}
    for transcript in sorted(base.rglob("conversation_transcript.txt")):
        run_dir = transcript.parent
        key = run_dir.relative_to(base).as_posix()
        found[key] = {
            "run_dir": run_dir,
            "transcript": transcript,
            "metadata": run_dir / "run_metadata.json",
            "cache_delta": run_dir / "prompt_response_cache_delta.jsonl",
        }
    return base, found


a_base, a_runs = discover_runs(run_a)
b_base, b_runs = discover_runs(run_b)

if not a_runs:
    print(f"No run artifacts found under A base: {a_base}")
    sys.exit(2)
if not b_runs:
    print(f"No run artifacts found under B base: {b_base}")
    sys.exit(2)

all_keys = sorted(set(a_runs) | set(b_runs))
shared_keys = sorted(set(a_runs) & set(b_runs))
only_a = sorted(set(a_runs) - set(b_runs))
only_b = sorted(set(b_runs) - set(a_runs))

print("\nDiscovery summary")
print(f"  A run count: {len(a_runs)}")
print(f"  B run count: {len(b_runs)}")
print(f"  Shared run IDs: {len(shared_keys)}")
print(f"  Only in A: {len(only_a)}")
print(f"  Only in B: {len(only_b)}")

if only_a:
    print("\nRun IDs only in A:")
    for key in only_a:
        print(f"  - {key}")

if only_b:
    print("\nRun IDs only in B:")
    for key in only_b:
        print(f"  - {key}")

transcript_equal = 0
metadata_equal = 0
cache_equal = 0
cache_na = 0

transcript_mismatches = []
metadata_mismatches = []
cache_mismatches = []

for key in shared_keys:
    a = a_runs[key]
    b = b_runs[key]

    if sha256_of_file(a["transcript"]) == sha256_of_file(b["transcript"]):
        transcript_equal += 1
    else:
        transcript_mismatches.append(key)

    a_meta = load_normalized_metadata(a["metadata"])
    b_meta = load_normalized_metadata(b["metadata"])
    if a_meta == b_meta:
        metadata_equal += 1
    else:
        metadata_mismatches.append(key)

    a_cache = a["cache_delta"]
    b_cache = b["cache_delta"]
    if a_cache.exists() and b_cache.exists():
        if sha256_of_file(a_cache) == sha256_of_file(b_cache):
            cache_equal += 1
        else:
            cache_mismatches.append(key)
    else:
        cache_na += 1

print("\nComparison summary (shared run IDs)")
print(f"  Transcript exact matches: {transcript_equal}/{len(shared_keys)}")
print(f"  Metadata core matches: {metadata_equal}/{len(shared_keys)}")
if len(shared_keys) - cache_na > 0:
    print(f"  Cache delta exact matches: {cache_equal}/{len(shared_keys) - cache_na}")
else:
    print("  Cache delta exact matches: n/a")

if transcript_mismatches:
    print("\nTranscript mismatches:")
    for key in transcript_mismatches:
        print(f"  - {key}")

if metadata_mismatches:
    print("\nMetadata mismatches (after volatile-key filtering):")
    for key in metadata_mismatches:
        print(f"  - {key}")

if cache_mismatches:
    print("\nCache-delta mismatches:")
    for key in cache_mismatches:
        print(f"  - {key}")

if shared_keys and transcript_equal == len(shared_keys):
    print("\nDeterminism signal: all shared transcripts match exactly.")
    sys.exit(0)

if not shared_keys:
    print("\nDeterminism signal: inconclusive (no shared run IDs to compare).")
    sys.exit(3)

print("\nDeterminism signal: one or more shared transcripts differ.")
sys.exit(1)
PY
