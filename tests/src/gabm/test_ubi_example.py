"""
Tests for reproducible UBI example simulation.
"""
# Metadata
__author__ = ["Andy Turner <agdturner@gmail.com>"]
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2026 GABM contributors, University of Leeds"

# Standard library imports
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
UBI_EXAMPLE_PATH = REPO_ROOT / "tests" / "examples" / "ubi" / "run.py"
UBI_INPUT_PATH = REPO_ROOT / "tests" / "examples" / "ubi" / "data" / "input" / "people_ubi.csv"


spec = importlib.util.spec_from_file_location("tests.examples.ubi", UBI_EXAMPLE_PATH)
ubi = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules[spec.name] = ubi
spec.loader.exec_module(ubi)


def test_ubi_simulation_is_reproducible_with_same_seed():
    """Running the same config twice should produce identical signatures."""
    config = ubi.SimulationConfig(seed=20261002, rounds=10, input_file=UBI_INPUT_PATH)

    first = ubi.run_simulation(config)
    second = ubi.run_simulation(config)

    assert first["n_agents"] == 100
    assert first["n_against"] == 33
    assert first["n_neutral"] == 34
    assert first["n_support"] == 33
    assert first["pair_ids"] == [0, 1]
    assert first["turns"] == 20
    assert first["pair_initial_views"] == [0, 1]
    assert first["pair_final_views"] == [1, 1]
    assert first["signature_initial"] == second["signature_initial"]
    assert first["signature_final"] == second["signature_final"]


def test_ubi_simulation_changes_with_different_seed():
    """Different seeds should be allowed and still produce valid summaries."""
    a = ubi.run_simulation(ubi.SimulationConfig(seed=1, rounds=10, input_file=UBI_INPUT_PATH))
    b = ubi.run_simulation(ubi.SimulationConfig(seed=2, rounds=10, input_file=UBI_INPUT_PATH))

    assert a["n_agents"] == b["n_agents"] == 100
    assert a["n_against"] == b["n_against"] == 33
    assert a["n_neutral"] == b["n_neutral"] == 34
    assert a["n_support"] == b["n_support"] == 33
    assert a["pair_ids"] == b["pair_ids"] == [0, 1]
    assert a["turns"] == b["turns"] == 20
    assert len(a["signature_final"]) == 16
    assert len(b["signature_final"]) == 16
