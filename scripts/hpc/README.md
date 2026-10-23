# HPC Run Scripts

This directory contains scripts for running GABM-related workloads on High Performance Computing (HPC) systems.

## Conventions
- Keep cluster-specific scripts in this directory.
- Use clear names that include model and cluster where relevant.
- Prefer environment-variable overrides for paths and tunables.
- Keep a short header in each script documenting tested module/tool versions.

## Current Scripts
- `run_Apertus_70B_Calder.sh`: Calder Slurm script for serving Apertus-v1.5-70B with vLLM via Apptainer.

## Notes for ClimateAction-GABM (CAG)
As CAG adopts newer GABM patterns, scripts from CAG can be ported here and kept versioned alongside GABM release changes.
