#!/usr/bin/env bash
#
# Generate markdown rows for the "Concurrency/stress summary" table in
# REPRODUCIBILITY_QWEN3_14B.md from Calder launcher outputs.
#
# Examples:
#   scripts/hpc/calder/generate_concurrency_rows.sh --job-id 494869
#   scripts/hpc/calder/generate_concurrency_rows.sh --job-id 494869 --job-id 494970
#   scripts/hpc/calder/generate_concurrency_rows.sh --run /flash-calder/users/$USER/gabm/gabm_runs/run_494869
#

set -euo pipefail

WORKING_DIR="/flash-calder/users/${USER}/gabm"
INCLUDE_HEADER=false

JOB_IDS=()
RUN_INPUTS=()

usage() {
  cat <<'USAGE'
Usage:
  scripts/hpc/calder/generate_concurrency_rows.sh [options]

Options:
  --job-id <id>         Slurm job ID (repeatable).
  --run <path|run_id>   Run directory path or run_12345 (repeatable).
  --working-dir <path>  Base working directory for job ID resolution.
  --header              Print markdown header + separator before rows.
  -h, --help            Show this help text.

Output columns:
  | Job ID | Concurrency | N runs | Successful runs | Failed runs | Mean runtime per run (if measured) | Error pattern |
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-id)
      [[ -z "${2:-}" ]] && { echo "Missing value for --job-id" >&2; exit 1; }
      JOB_IDS+=("$2")
      shift 2
      ;;
    --run)
      [[ -z "${2:-}" ]] && { echo "Missing value for --run" >&2; exit 1; }
      RUN_INPUTS+=("$2")
      shift 2
      ;;
    --working-dir)
      [[ -z "${2:-}" ]] && { echo "Missing value for --working-dir" >&2; exit 1; }
      WORKING_DIR="$2"
      shift 2
      ;;
    --header)
      INCLUDE_HEADER=true
      shift
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

if [[ ${#JOB_IDS[@]} -eq 0 && ${#RUN_INPUTS[@]} -eq 0 ]]; then
  echo "Provide at least one --job-id or --run input." >&2
  usage
  exit 1
fi

resolve_run_dir() {
  local v="$1"
  local candidate=""

  if [[ -d "$v" ]]; then
    candidate="$v"
  elif [[ "$v" =~ ^run_[0-9]+$ ]]; then
    candidate="${WORKING_DIR}/gabm_runs/${v}"
  elif [[ "$v" =~ ^[0-9]+$ ]]; then
    candidate="${WORKING_DIR}/gabm_runs/run_${v}"
  else
    candidate="$v"
  fi

  if [[ ! -d "$candidate" ]]; then
    echo "Run directory not found: $candidate" >&2
    exit 1
  fi

  realpath "$candidate"
}

get_value() {
  local file="$1"
  local key="$2"
  local val
  val=$(grep -E "^${key}=" "$file" | tail -n 1 | cut -d '=' -f2- || true)
  if [[ -z "$val" ]]; then
    echo ""
  else
    echo "$val"
  fi
}

extract_error_pattern() {
  local run_dir="$1"
  local failed="$2"
  local clients_dir="${run_dir}/clients"

  if [[ "$failed" == "0" ]]; then
    echo "none"
    return
  fi

  if [[ ! -d "$clients_dir" ]]; then
    echo "see logs"
    return
  fi

  local first_match
  first_match=$(rg -n "Traceback|Exception|ERROR|RuntimeError|ConnectionError|timed out" "$clients_dir"/*.log 2>/dev/null | head -n 1 || true)

  if [[ -z "$first_match" ]]; then
    echo "failed_workers_no_signature"
  else
    # Keep the row concise and markdown-safe.
    echo "$first_match" | sed 's/|/\\|/g'
  fi
}

run_dirs=()
for id in "${JOB_IDS[@]}"; do
  run_dirs+=("$(resolve_run_dir "$id")")
done
for item in "${RUN_INPUTS[@]}"; do
  run_dirs+=("$(resolve_run_dir "$item")")
done

if $INCLUDE_HEADER; then
  echo "| Job ID | Concurrency | N runs | Successful runs | Failed runs | Mean runtime per run (if measured) | Error pattern |"
  echo "|---:|---:|---:|---:|---:|---|---|"
fi

for run_dir in "${run_dirs[@]}"; do
  summary="${run_dir}/launcher_summary.log"
  if [[ ! -f "$summary" ]]; then
    echo "Missing launcher summary: $summary" >&2
    exit 1
  fi

  job_id=$(basename "$run_dir" | sed -n 's/^run_//p')
  concurrency=$(get_value "$summary" "CONCURRENCY")
  n_runs=$(get_value "$summary" "N_RUNS")
  success=$(get_value "$summary" "SUCCESSFUL_RUNS")
  failed=$(get_value "$summary" "FAILED_RUNS")

  [[ -z "$concurrency" ]] && concurrency="?"
  [[ -z "$n_runs" ]] && n_runs="?"
  [[ -z "$success" ]] && success="?"
  [[ -z "$failed" ]] && failed="?"

  error_pattern=$(extract_error_pattern "$run_dir" "$failed")

  # Mean runtime is not currently emitted by the launcher.
  mean_runtime="n/a"

  echo "| ${job_id} | ${concurrency} | ${n_runs} | ${success} | ${failed} | ${mean_runtime} | ${error_pattern} |"
done
