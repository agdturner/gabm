"""
Tests for chat simulation example reproducibility.
"""
# Metadata
__author__ = ["Andy Turner <agdturner@gmail.com>"]
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2026 GABM contributors, University of Leeds"

# Local imports
from gabm.examples.chat.sim import run, generate_transcript_lines


def test_chat_sim_writes_output_file(tmp_path):
    """
    Test that the chat simulation writes an output file.

    Args:
        tmp_path: Temporary directory provided by pytest for file output.
    """
    output_file = run(output_dir=tmp_path, seed=42)

    assert output_file.exists()
    contents = output_file.read_text(encoding="utf-8")
    assert "Simple conversation transcript" in contents
    assert "seed=42" in contents
    assert "Shared interest topic IDs:" in contents


def test_chat_sim_reproducible_for_same_seed(tmp_path):
    """
    Test that running the chat simulation with the same seed produces identical output.

    Args:
        tmp_path: Temporary directory provided by pytest for file output.
    """
    first = run(output_dir=tmp_path, seed=123)
    first_text = first.read_text(encoding="utf-8")

    second = run(output_dir=tmp_path, seed=123)
    second_text = second.read_text(encoding="utf-8")

    assert first_text == second_text


def test_chat_sim_changes_for_different_seeds():
    """
    Test that running the chat simulation with different seeds produces different output.
    """
    transcript_1 = generate_transcript_lines(seed=1)
    transcript_2 = generate_transcript_lines(seed=2)

    assert transcript_1 != transcript_2
