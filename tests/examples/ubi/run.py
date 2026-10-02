#!/usr/bin/env python3
"""
Reproducible UBI simulation example.

This script loads initial agents from tests/examples/ubi/data/input/people_ubi.csv,
then runs deterministic pair-wise conversation rounds about UBI.

The default backend is a deterministic mock LLM for reproducible tests.
You can also use configured GABM LLM services (openai, genai, deepseek,
publicai) or a local OpenAI-compatible server.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import random
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Allow running this script directly from the repository checkout.
REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

EXAMPLE_ROOT = Path(__file__).resolve().parent

from gabm.abm.agent import Person
from gabm.abm.attributes.opinion import Opinion, OpinionTopic, OpinionTopicID, OpinionValue, OpinionValueMap
from gabm.abm.environment import Environment
from gabm.abm.group import Group, GroupID
from gabm.io.read_data import read_api_keys


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration used to keep runs reproducible and explicit."""

    seed: int = 20261002
    rounds: int = 10
    year: int = 2026
    input_file: Path = EXAMPLE_ROOT / "data" / "input" / "people_ubi.csv"
    provider: str = "mock"
    model: Optional[str] = None
    local_base_url: str = "http://localhost:8080/v1"
    local_api_key: str = "local"
    write_transcript: bool = False
    transcript_out: Optional[Path] = None


UBI_TOPIC_ID = OpinionTopicID(100)


@dataclass
class AgentContext:
    """Container for agent entity and its persona text."""

    person: Person
    persona: str
    source_row: dict[str, str] = field(repr=False)


def _numeric_agent_id(agent: Person) -> int:
    """Return agent ID as an int, handling both int and AgentID storage."""
    return agent.id.id if hasattr(agent.id, "id") else int(agent.id)


def _extract_text(response: Any) -> str:
    """Best-effort extraction of text content from service responses."""
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if hasattr(response, "choices"):
        choices = getattr(response, "choices", None)
        if choices:
            first = choices[0]
            message = getattr(first, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
                if isinstance(content, str):
                    return content
    if isinstance(response, dict):
        try:
            return response["choices"][0]["message"]["content"]
        except Exception:
            return json.dumps(response, sort_keys=True)
    return str(response)


def _build_persona(row: dict[str, str], simulation_year: int) -> str:
    """Build a concise persona statement from CSV attributes."""
    age = row.get("Age", "unknown")
    gender = row.get("Gender", "unknown")
    education = row.get("Education", "unknown")
    employment = row.get("Employment", "unknown")
    ethnicity = row.get("Ethnicity", "unknown")
    family = row.get("Family", "unknown")
    health = row.get("Health", "unknown")
    income = row.get("Income", "unknown")
    return (
        f"I am a {age} year old {gender} living in the UK in {simulation_year}. "
        f"My education is {education}. I am {employment}. "
        f"My ethnicity is {ethnicity}. I am {family}. "
        f"My health is {health}. My income is {income}."
    )


class LLMBackend:
    """Abstract backend used by the UBI example for conversational turns."""

    def ask(self, prompt: str) -> str:
        raise NotImplementedError()


class MockLLMBackend(LLMBackend):
    """Deterministic mock backend for reproducible tests."""

    def ask(self, prompt: str) -> str:
        speaker_match = re.search(r"SPEAKER_VIEW\s*=\s*(-?\d+)", prompt)
        listener_match = re.search(r"LISTENER_VIEW\s*=\s*(-?\d+)", prompt)
        speaker_view = int(speaker_match.group(1)) if speaker_match else 0
        listener_view = int(listener_match.group(1)) if listener_match else 0

        if speaker_view < listener_view:
            updated = speaker_view + 1
        elif speaker_view > listener_view:
            updated = speaker_view - 1
        else:
            updated = speaker_view

        updated = max(-1, min(1, updated))
        message = (
            "I think UBI can improve stability, but we should phase it carefully "
            "and monitor costs and fairness."
        )
        payload = {
            "message": message,
            "new_ubi": updated,
            "reason": "Adjusted one step toward counterpart position.",
        }
        return json.dumps(payload, sort_keys=True)


class ServiceLLMBackend(LLMBackend):
    """Wrapper for GABM LLM services."""

    _SERVICE_IMPORTS = {
        "openai": ("gabm.io.llm.openai", "OpenAIService"),
        "genai": ("gabm.io.llm.genai", "GenAIService"),
        "deepseek": ("gabm.io.llm.deepseek", "DeepSeekService"),
        "publicai": ("gabm.io.llm.publicai", "PublicAIService"),
    }

    def __init__(self, provider: str, model: Optional[str] = None):
        provider = provider.lower()
        if provider not in self._SERVICE_IMPORTS:
            valid = ", ".join(sorted(self._SERVICE_IMPORTS))
            raise ValueError(f"Unsupported service provider '{provider}'. Valid providers: {valid}")

        module_name, class_name = self._SERVICE_IMPORTS[provider]
        from importlib import import_module

        service_cls = getattr(import_module(module_name), class_name)
        self.service = service_cls()
        self.provider = provider
        self.model = model

        api_keys = read_api_keys(REPO_ROOT / "data" / "api_key.csv")
        self.api_key = api_keys.get(provider)
        if not self.api_key or str(self.api_key).startswith("YOUR_"):
            raise RuntimeError(
                f"API key for provider '{provider}' not configured in data/api_key.csv"
            )

    def ask(self, prompt: str) -> str:
        response = self.service.send(self.api_key, prompt, model=self.model) if self.model else self.service.send(self.api_key, prompt)
        return _extract_text(response)


class LocalOpenAICompatibleBackend(LLMBackend):
    """Local backend for OpenAI-compatible LLM servers (vLLM/Ollama/etc.)."""

    def __init__(self, model: str, base_url: str, api_key: str = "local"):
        if not model:
            raise ValueError("A model must be provided for local-openai backend.")
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def ask(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are simulating a UK resident discussing UBI."},
                {"role": "user", "content": prompt},
            ],
        )
        return _extract_text(response)


def build_backend(config: SimulationConfig) -> LLMBackend:
    """Create the requested backend."""
    provider = config.provider.lower()
    if provider == "mock":
        return MockLLMBackend()
    if provider == "local-openai":
        return LocalOpenAICompatibleBackend(
            model=config.model or "gpt-4o-mini",
            base_url=config.local_base_url,
            api_key=config.local_api_key,
        )
    return ServiceLLMBackend(provider=provider, model=config.model)


def _opinion_from_ubi_value(value: int) -> Opinion:
    """Create an Opinion object for the UBI topic from an integer value."""
    return Opinion(
        UBI_TOPIC_ID,
        OpinionValueMap({UBI_TOPIC_ID: OpinionValue(UBI_TOPIC_ID, value, f"UBI score {value}")}),
        value,
    )


def load_initial_agents(config: SimulationConfig) -> tuple[Environment, Group, Group, Group, dict[int, AgentContext]]:
    """Load agents from CSV and place them into initial UBI groups."""
    env = Environment(year=config.year, place="UK")
    env.opinions = {UBI_TOPIC_ID: OpinionTopic(UBI_TOPIC_ID, "ubi", "Opinion on universal basic income")}
    contexts: dict[int, AgentContext] = {}

    group_against = Group(GroupID(1), "Against UBI")
    group_neutral = Group(GroupID(2), "Neutral")
    group_support = Group(GroupID(3), "Support UBI")
    env.groups_active[group_against.id] = group_against
    env.groups_active[group_neutral.id] = group_neutral
    env.groups_active[group_support.id] = group_support

    if not config.input_file.is_file():
        raise FileNotFoundError(f"Input file not found: {config.input_file}")

    with config.input_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_columns = {"ID", "Age", "UBI"}
        header_columns = set(reader.fieldnames or [])
        missing = required_columns - header_columns
        if missing:
            missing_sorted = ", ".join(sorted(missing))
            raise ValueError(f"Missing required CSV column(s): {missing_sorted}")

        loaded = 0
        for row in reader:
            agent_id = int(row["ID"])
            age = int(row["Age"])
            year_of_birth = env.year - age
            ubi_value = int(row["UBI"])

            person = Person(
                id=agent_id,
                environment=env,
                year_of_birth=year_of_birth,
                opinions={UBI_TOPIC_ID: _opinion_from_ubi_value(ubi_value)},
            )
            env.agents_active[agent_id] = person
            contexts[agent_id] = AgentContext(
                person=person,
                persona=_build_persona(row, simulation_year=env.year),
                source_row=row,
            )

            if ubi_value < 0:
                group_against.add_member(person)
            elif ubi_value > 0:
                group_support.add_member(person)
            else:
                group_neutral.add_member(person)

            loaded += 1

        if loaded == 0:
            raise ValueError(f"CSV file has no data rows: {config.input_file}")

    return env, group_against, group_neutral, group_support, contexts


def _mean_ubi(group: Group) -> float:
    """Return mean UBI opinion for group members."""
    if not group.members:
        return 0.0
    total = sum(member.opinions[UBI_TOPIC_ID].value for member in group.members)
    return total / len(group.members)


def _state_signature(env: Environment) -> str:
    """Stable hash of all agent UBI opinions for reproducibility checks."""
    rows = [f"{agent_id}:{env.agents_active[agent_id].opinions[UBI_TOPIC_ID].value}" for agent_id in sorted(env.agents_active)]
    joined = "|".join(rows)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _build_turn_prompt(
    speaker: AgentContext,
    listener: AgentContext,
    speaker_view: int,
    listener_view: int,
    round_index: int,
    last_message: str,
) -> str:
    """Build a constrained prompt for a single conversational turn."""
    return (
        "Topic: Universal Basic Income (UBI) in the UK.\n"
        f"ROUND={round_index}\n"
        f"SPEAKER_ID={_numeric_agent_id(speaker.person)}\n"
        f"LISTENER_ID={_numeric_agent_id(listener.person)}\n"
        f"SPEAKER_VIEW={speaker_view}\n"
        f"LISTENER_VIEW={listener_view}\n"
        f"LISTENER_LAST_MESSAGE={last_message or 'None'}\n"
        "SPEAKER_PERSONA:\n"
        f"{speaker.persona}\n"
        "LISTENER_PERSONA:\n"
        f"{listener.persona}\n"
        "Return strict JSON only with keys: message, new_ubi, reason. "
        "new_ubi must be one of -1, 0, 1 and should be your updated view after reflection."
    )


def _parse_turn_response(raw_text: str, fallback_value: int) -> tuple[str, int]:
    """Parse model response into (message, new_ubi) with safe fallback."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    try:
        payload = json.loads(text)
        message = str(payload.get("message", ""))
        candidate = int(payload.get("new_ubi", fallback_value))
        new_ubi = max(-1, min(1, candidate))
        return message, new_ubi
    except Exception:
        pass

    parsed_message = text
    number_match = re.search(r"-?\d+", text)
    if number_match:
        candidate = int(number_match.group(0))
        return parsed_message, max(-1, min(1, candidate))
    return parsed_message, fallback_value


def _write_transcript_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    """Write transcript records to JSONL for reproducibility audits."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def run_simulation(config: SimulationConfig) -> dict:
    """Run iterative pairwise UBI discussion using an LLM backend."""
    random.seed(config.seed)
    env, group_against, group_neutral, group_support, contexts = load_initial_agents(config)
    backend = build_backend(config)

    initial_signature = _state_signature(env)
    initial_mean = _mean_ubi(group_neutral)
    transcript: list[dict[str, Any]] = []

    ordered_ids = sorted(contexts)
    if len(ordered_ids) < 2:
        raise ValueError("At least two agents are required for pair discussion.")

    a_id = ordered_ids[0]
    b_id = ordered_ids[1]
    agent_a = contexts[a_id]
    agent_b = contexts[b_id]
    last_a_message = ""
    last_b_message = ""

    for round_index in range(1, config.rounds + 1):
        a_view = agent_a.person.opinions[UBI_TOPIC_ID].value
        b_view = agent_b.person.opinions[UBI_TOPIC_ID].value

        prompt_a = _build_turn_prompt(
            speaker=agent_a,
            listener=agent_b,
            speaker_view=a_view,
            listener_view=b_view,
            round_index=round_index,
            last_message=last_b_message,
        )
        raw_a = backend.ask(prompt_a)
        msg_a, new_a_view = _parse_turn_response(raw_a, fallback_value=a_view)
        agent_a.person.opinions[UBI_TOPIC_ID].value = new_a_view
        last_a_message = msg_a
        transcript.append(
            {
                "round": round_index,
                "turn": "A_to_B",
                "speaker": a_id,
                "listener": b_id,
                "prompt": prompt_a,
                "raw_response": raw_a,
                "message": msg_a,
                "old_view": a_view,
                "new_view": new_a_view,
            }
        )

        a_view_after = agent_a.person.opinions[UBI_TOPIC_ID].value
        b_view_current = agent_b.person.opinions[UBI_TOPIC_ID].value
        prompt_b = _build_turn_prompt(
            speaker=agent_b,
            listener=agent_a,
            speaker_view=b_view_current,
            listener_view=a_view_after,
            round_index=round_index,
            last_message=last_a_message,
        )
        raw_b = backend.ask(prompt_b)
        msg_b, new_b_view = _parse_turn_response(raw_b, fallback_value=b_view_current)
        agent_b.person.opinions[UBI_TOPIC_ID].value = new_b_view
        last_b_message = msg_b
        transcript.append(
            {
                "round": round_index,
                "turn": "B_to_A",
                "speaker": b_id,
                "listener": a_id,
                "prompt": prompt_b,
                "raw_response": raw_b,
                "message": msg_b,
                "old_view": b_view_current,
                "new_view": new_b_view,
            }
        )

    final_signature = _state_signature(env)
    final_mean = _mean_ubi(group_neutral)

    summary = {
        "seed": config.seed,
        "rounds": config.rounds,
        "n_agents": len(env.agents_active),
        "n_against": len(group_against.members),
        "n_neutral": len(group_neutral.members),
        "n_support": len(group_support.members),
        "neutral_mean_initial": round(initial_mean, 3),
        "neutral_mean_final": round(final_mean, 3),
        "pair_ids": [a_id, b_id],
        "pair_initial_views": [
            transcript[0]["old_view"] if transcript else agent_a.person.opinions[UBI_TOPIC_ID].value,
            transcript[1]["old_view"] if len(transcript) > 1 else agent_b.person.opinions[UBI_TOPIC_ID].value,
        ],
        "pair_final_views": [
            agent_a.person.opinions[UBI_TOPIC_ID].value,
            agent_b.person.opinions[UBI_TOPIC_ID].value,
        ],
        "provider": config.provider,
        "model": config.model,
        "turns": len(transcript),
        "signature_initial": initial_signature,
        "signature_final": final_signature,
    }

    if config.write_transcript:
        out_path = config.transcript_out
        if out_path is None:
            out_path = EXAMPLE_ROOT / "data" / "output" / (
                f"transcript_provider-{config.provider}_seed-{config.seed}_rounds-{config.rounds}.jsonl"
            )
        created_at = datetime.now(timezone.utc).isoformat()
        run_header = {
            "record_type": "run_header",
            "created_at_utc": created_at,
            "provider": config.provider,
            "model": config.model,
            "seed": config.seed,
            "rounds": config.rounds,
            "input_file": str(config.input_file),
            "signature_initial": summary["signature_initial"],
            "signature_final": summary["signature_final"],
            "pair_ids": summary["pair_ids"],
        }
        records = [run_header]
        records.extend({"record_type": "turn", **turn} for turn in transcript)
        records.append({"record_type": "run_summary", **summary})
        _write_transcript_jsonl(out_path, records)
        summary["transcript_path"] = str(out_path)

    return summary


def main() -> None:
    """Execute a reproducible UBI simulation and print a concise summary."""
    parser = argparse.ArgumentParser(description="Run a reproducible UBI simulation example.")
    parser.add_argument("--seed", type=int, default=20261002, help="Random seed for reproducible partner selection.")
    parser.add_argument("--rounds", type=int, default=10, help="Number of communication rounds.")
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "genai", "deepseek", "publicai", "local-openai"],
        default="mock",
        help="LLM backend provider.",
    )
    parser.add_argument("--model", type=str, default=None, help="Optional model name for selected provider.")
    parser.add_argument(
        "--local-base-url",
        type=str,
        default="http://localhost:8080/v1",
        help="Base URL for local OpenAI-compatible backend (used with --provider local-openai).",
    )
    parser.add_argument(
        "--local-api-key",
        type=str,
        default="local",
        help="API key/token for local OpenAI-compatible backend.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=EXAMPLE_ROOT / "data" / "input" / "people_ubi.csv",
        help="Path to input CSV with ID, Age, and UBI columns.",
    )
    parser.add_argument(
        "--write-transcript",
        action="store_true",
        help="Write a JSONL transcript with prompts and raw responses for each turn.",
    )
    parser.add_argument(
        "--transcript-out",
        type=Path,
        default=None,
        help="Optional explicit output path for transcript JSONL.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")

    config = SimulationConfig(
        seed=args.seed,
        rounds=args.rounds,
        input_file=args.input,
        provider=args.provider,
        model=args.model,
        local_base_url=args.local_base_url,
        local_api_key=args.local_api_key,
        write_transcript=args.write_transcript,
        transcript_out=args.transcript_out,
    )
    summary = run_simulation(config)

    print("UBI reproducible simulation")
    print(
        f"seed={summary['seed']} rounds={summary['rounds']} agents={summary['n_agents']} "
        f"provider={summary['provider']}"
    )
    print(
        "groups="
        f"against:{summary['n_against']} "
        f"neutral:{summary['n_neutral']} "
        f"support:{summary['n_support']}"
    )
    print(
        "pair="
        f"ids:{summary['pair_ids']} "
        f"views:{summary['pair_initial_views']}->{summary['pair_final_views']} "
        f"turns:{summary['turns']}"
    )
    print(
        "neutral_mean="
        f"{summary['neutral_mean_initial']} -> {summary['neutral_mean_final']}"
    )
    print(
        "signature="
        f"{summary['signature_initial']} -> {summary['signature_final']}"
    )
    if "transcript_path" in summary:
        print(f"transcript={summary['transcript_path']}")


if __name__ == "__main__":
    main()