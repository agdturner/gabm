#!/bin/bash -l
#
# =============================================================================
# GABM — Calder chat ensemble launcher
# =============================================================================
#
# Submit with:
#   sbatch scripts/hpc/calder/run_chat_ensemble.sh
#
# Override defaults, for example:
#   sbatch scripts/hpc/calder/run_chat_ensemble.sh --start-seed 100 --n-runs 20 --year 2027
#
# Any unknown flags are forwarded to scripts/hpc/calder/run.sh.

#SBATCH --job-name=LLM-gabm-chat-ens
#SBATCH --partition=calder-gpu-hopper
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4
#SBATCH --cpus-per-task=32
#SBATCH --mem=256G
#SBATCH --time=08:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

set -euo pipefail
set -x

MODEL_NAME="Apertus-v1.5-70B"
SIF_FILE="apertus15.sif"
WORKING_DIR="/flash-calder/users/${USER}/gabm"
CONDA_ENV="gabm"
YEAR="2026"
START_SEED="42"
N_RUNS="5"

FORWARDED_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ -z "${2:-}" ]] && { echo "Missing value for --model"; exit 1; }
      MODEL_NAME="$2"
      shift 2
      ;;
    --sif)
      [[ -z "${2:-}" ]] && { echo "Missing value for --sif"; exit 1; }
      SIF_FILE="$2"
      shift 2
      ;;
    --working-dir)
      [[ -z "${2:-}" ]] && { echo "Missing value for --working-dir"; exit 1; }
      WORKING_DIR="$2"
      shift 2
      ;;
    --conda-env)
      [[ -z "${2:-}" ]] && { echo "Missing value for --conda-env"; exit 1; }
      CONDA_ENV="$2"
      shift 2
      ;;
    --year)
      [[ -z "${2:-}" ]] && { echo "Missing value for --year"; exit 1; }
      YEAR="$2"
      shift 2
      ;;
    --start-seed)
      [[ -z "${2:-}" ]] && { echo "Missing value for --start-seed"; exit 1; }
      START_SEED="$2"
      shift 2
      ;;
    --n-runs)
      [[ -z "${2:-}" ]] && { echo "Missing value for --n-runs"; exit 1; }
      N_RUNS="$2"
      shift 2
      ;;
    *)
      FORWARDED_ARGS+=("$1")
      shift
      ;;
  esac
done

REPO_DIR="${SLURM_SUBMIT_DIR:-$PWD}"

bash "${REPO_DIR}/scripts/hpc/calder/run.sh" \
  --model "${MODEL_NAME}" \
  --sif "${SIF_FILE}" \
  --working-dir "${WORKING_DIR}" \
  --conda-env "${CONDA_ENV}" \
  --example chat_ensemble \
  --year "${YEAR}" \
  --start-seed "${START_SEED}" \
  --n-runs "${N_RUNS}" \
  "${FORWARDED_ARGS[@]}"
