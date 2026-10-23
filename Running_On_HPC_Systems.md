# Running On HPC Systems

Some LLM workloads need more compute than a typical laptop or desktop can provide. This guide outlines a general approach for running GABM-related model serving and experiments on High Performance Computing (HPC) systems.

The examples in this repository currently use:
- Slurm for job scheduling
- Apptainer for container runtime
- vLLM for model serving

You can adapt the same pattern to your institution's HPC environment.

## Recommended Script Location

Keep HPC scripts under:
- `scripts/hpc/`

Current example:
- [Apertus 70B Slurm script](scripts/hpc/run_Apertus_70B_Calder.sh)

Compatibility note:
- The repository-root `run_Apertus_70B_Calder.sh` is retained as a wrapper for legacy paths.
- Prefer using scripts directly from `scripts/hpc/` for new workflows.

## Typical Workflow

1. Prepare environment and model assets
- Confirm access to GPUs and scheduler partition/queue.
- Confirm model files are available on shared or node-local storage.
- Confirm container image availability and path.

2. Submit model-serving job
- Use a Slurm script in `scripts/hpc/` as the starting template.
- Tune resources: GPUs, CPUs, memory, walltime.
- Set model-serving options such as tensor parallel size and max context length.

3. Validate service health
- Check scheduler output/error logs.
- Verify GPU utilization and memory.
- Confirm endpoint reachability from your experiment environment.

4. Run GABM experiments
- Run small pilot sweeps first.
- Capture run metadata and output artifacts for reproducibility.
- Compare hosted vs local/HPC behavior using ensemble comparison tools.

## Portability Checklist

When moving between HPC systems, review these items:
- Module names and versions (CUDA, NCCL, etc.)
- Container runtime options (`apptainer` flags)
- Filesystem paths for models and logs
- Scheduler directives (`#SBATCH` lines)
- Available GPU types and counts
- Network and firewall constraints for service ports

## Operational Guidance

- Start with conservative resource settings, then scale.
- Prefer explicit environment variables for tunables.
- Keep memory and GPU monitoring enabled for long runs.
- Record exact model, runtime, and scheduler settings with experiment outputs.

## Security and Cost Notes

- Treat API keys and credentials as secrets; do not hardcode them in scripts.
- For large ensemble runs, local/HPC inference can be more cost-effective than repeated hosted API calls.
- Pilot with small `N_RUNS` before scaling to larger sweeps.
