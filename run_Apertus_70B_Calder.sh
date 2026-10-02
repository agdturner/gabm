#!/bin/bash
#SBATCH --job-name=cag_70B
#SBATCH --nodes=1
#SBATCH --partition=gpu_hopper
#SBATCH --ntasks-per-node=1
#SBATCH --gpus-per-node=4       # Max is 8 # Set --tensor-parallel-size to match in the apptainer launch. This should be matched by $SLURM_GPUS_ON_NODE
#SBATCH --cpus-per-task=112     # Theoretical Max is 128 but some are needed for system processes so most tested with is 112
#SBATCH --mem=200G              # This probably does not matter as there is 1.4T which seems fully available (it is not cgroup restricted).
#SBATCH --time=04:00:00
#SBATCH --output=run_apertus_70B_%j.out
#SBATCH --error=run_apertus_70B_%j.err

export PYTHONUNBUFFERED=1
export APPTAINERENV_PYTHONUNBUFFERED=1
export APPTAINERENV_CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES

# Load Leeds verified architecture drivers
module load calder/hopper
module load cuda/13.3.0
module load nccl/2.29.7-1

echo "=== Node information ==="
echo "=== GPU Information ==="
nvidia-smi -L
echo "=== CPU Information ==="
lscpu | grep "^CPU(s):"
echo "=== Memory Information ==="
free -h

echo "=== Job details ==="
echo "Job ID: $SLURM_JOBID"
echo "Number of GPUs: $SLURM_GPUS_ON_NODE"
echo "Number of CPUs: $SLURM_CPUS_ON_NODE"

echo "=== Start memory logging ==="
MEMORY_LOG="run_apertus_70B_${SLURM_JOBID}.log"
echo "MEMORY_LOG: $MEMORY_LOG"
(
while true
do
  date
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu \
             --format=csv,noheader
  sleep 5
done
) > $MEMORY_LOG &
MONITOR_PID=$!

MODEL_DIR="/users/$USER/.cache/huggingface/hub/Apertus-v1.5-70B"
echo "=== MODEL_DIR ==="
echo $MODEL_DIR

echo "=== Starting Grace Hopper Production Inference Execution ==="
echo "Assigned Compute Node: $(hostname)"
echo "Visible Slurm GPU Indices: $CUDA_VISIBLE_DEVICES"

echo "=== Start Apptainer ==="

START=$(date +%s)

# --max-model-len limits the size of prompts and reponses.
# The default --max-model-len is 262144
# The larger the value, the more resources are required and the more context that can be provided in prompts and detail given in responses.


apptainer exec \
  --cleanenv \
  --nv \
  --env CUDA_HOME=/usr/local/cuda \
  --env CUDACXX=/usr/local/cuda/bin/nvcc \
  apertus15.sif \
  vllm serve $MODEL_DIR \
  --tensor-parallel-size $SLURM_GPUS_ON_NODE \
  --compilation-config.pass_config.fuse_allreduce_rms=false \
  --chat-template-content-format string \
  --gpu-memory-utilization 0.8 \
  --max-model-len 262144 \
  --port 8000 2>&1

# Capture exit code of apptainer vllm serve process
EXIT_CODE=$?

END=$(date +%s)

echo "Elapsed: $((END-START)) seconds"

echo "=== End Apptainer ==="
echo "Apptainer exited with code: ${EXIT_CODE}"

echo "=== End memory logging ==="
kill $MONITOR_PID