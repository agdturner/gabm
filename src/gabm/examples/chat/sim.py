"""Chat simulation example module."""

import argparse
import importlib
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Local imports
from gabm.abm.environment import Environment
from gabm.abm.data.names_ons import get_default_ons_name_paths
from gabm.io.read_data import read_api_keys

_DEFAULT_ONS_MALE_FILE, _DEFAULT_ONS_FEMALE_FILE = get_default_ons_name_paths()
_DEFAULT_API_KEY_FILE = Path("data/api_key.csv")
_DEFAULT_OUTPUT_ROOT = Path("data/output/examples/chat")

_LLM_SERVICE_MODULES = {
	"openai": ("gabm.io.llm.openai", "OpenAIService"),
	"genai": ("gabm.io.llm.genai", "GenAIService"),
	"deepseek": ("gabm.io.llm.deepseek", "DeepSeekService"),
	"publicai": ("gabm.io.llm.publicai", "PublicAIService"),
}


def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
	"""Parse command-line options for the chat simulation script."""
	parser = argparse.ArgumentParser(description="Run chat simulation example.")
	parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducible simulation output.")
	parser.add_argument("--year", type=int, default=2026, help="Simulation year used by the environment.")
	parser.add_argument(
		"--ons-male-file",
		type=Path,
		default=_DEFAULT_ONS_MALE_FILE,
		help="Path to ONS male names CSV file.",
	)
	parser.add_argument(
		"--ons-female-file",
		type=Path,
		default=_DEFAULT_ONS_FEMALE_FILE,
		help="Path to ONS female names CSV file.",
	)
	parser.add_argument(
		"--llm-service",
		type=str,
		choices=sorted(_LLM_SERVICE_MODULES.keys()),
		default=None,
		help="Optional LLM service to use for dialogue generation.",
	)
	parser.add_argument("--model", type=str, default=None, help="Optional model name for the selected LLM service.")
	parser.add_argument(
		"--llm-seed",
		type=int,
		default=None,
		help="Optional provider request seed (currently used by OpenAI for best-effort reproducibility).",
	)
	parser.add_argument("--api-key", type=str, default=None, help="Optional API key override for the selected LLM service.")
	parser.add_argument(
		"--api-key-file",
		type=Path,
		default=_DEFAULT_API_KEY_FILE,
		help="Path to CSV file containing API keys (api,key).",
	)
	parser.add_argument(
		"--output-root",
		type=Path,
		default=_DEFAULT_OUTPUT_ROOT,
		help="Directory under which per-run output folders are created.",
	)
	parser.add_argument(
		"--run-id",
		type=str,
		default=None,
		help="Optional explicit run directory name (otherwise auto-generated).",
	)
	parser.add_argument(
		"--no-cache",
		action="store_true",
		help="Disable LLM cache replay and force live prompting on every request.",
	)
	return parser.parse_args(argv)


def resolve_ons_male_file(cli_path: Path | None) -> Path:
	"""Resolve ONS male CSV path from CLI or environment."""
	if cli_path:
		return cli_path
	env_path = os.getenv("GABM_CHAT_ONS_MALE_FILE", "").strip()
	if env_path:
		return Path(env_path)
	return _DEFAULT_ONS_MALE_FILE


def resolve_ons_female_file(cli_path: Path | None) -> Path:
	"""Resolve ONS female CSV path from CLI or environment."""
	if cli_path:
		return cli_path
	env_path = os.getenv("GABM_CHAT_ONS_FEMALE_FILE", "").strip()
	if env_path:
		return Path(env_path)
	return _DEFAULT_ONS_FEMALE_FILE


def resolve_llm_service_name(cli_name: str | None) -> str | None:
	"""Resolve LLM service name from CLI or environment."""
	if cli_name:
		return cli_name.strip().lower()
	env_name = os.getenv("GABM_CHAT_LLM_SERVICE", "").strip().lower()
	return env_name or None


def resolve_llm_model(cli_model: str | None) -> str | None:
	"""Resolve model name from CLI or environment."""
	if cli_model:
		candidate = cli_model.strip()
		if candidate:
			return candidate
	env_model = os.getenv("GABM_CHAT_LLM_MODEL", "").strip()
	return env_model or None


def resolve_llm_seed(cli_seed: int | None) -> int | None:
	"""Resolve provider request seed from CLI or environment."""
	if cli_seed is not None:
		return cli_seed
	env_seed = os.getenv("GABM_CHAT_LLM_SEED", "").strip()
	if not env_seed:
		return None
	try:
		return int(env_seed)
	except ValueError:
		return None


def build_llm_service(service_name: str | None):
	"""Build and return an LLM service instance for the given service name."""
	if not service_name:
		return None
	service_key = service_name.strip().lower()
	module_and_class = _LLM_SERVICE_MODULES.get(service_key)
	if module_and_class is None:
		raise ValueError(f"Unsupported llm service '{service_name}'.")
	module_name, class_name = module_and_class
	module = importlib.import_module(module_name)
	service_cls = getattr(module, class_name)
	return service_cls()


def resolve_llm_api_key(cli_api_key: str | None, service_name: str | None, api_key_file: Path) -> str | None:
	"""Resolve API key from CLI override, environment, or API key CSV."""
	if cli_api_key:
		candidate = cli_api_key.strip()
		if candidate:
			return candidate

	if not service_name:
		return None

	env_var = f"{service_name.strip().upper()}_API_KEY"
	env_api_key = os.getenv(env_var, "").strip()
	if env_api_key:
		return env_api_key

	try:
		api_keys = read_api_keys(api_key_file)
	except (FileNotFoundError, ValueError, StopIteration):
		return None

	return api_keys.get(service_name.strip().lower())


def build_first_turn_prompt(
	speaker_name: str,
	other_name: str,
	speaker_persona: str,
	speaker_interests: str,
	speaker_values: str,
	other_persona: str,
) -> str:
	"""Build the first-turn prompt for the conversation LLM."""
	return (
		"You are helping simulate a conversation between two person agents.\n"
		"Goal: find shared interests through a natural, friendly conversation.\n"
		f"You are Speaker: {speaker_name}\n"
		f"About you: {speaker_persona} {speaker_interests} {speaker_values}\n"
		f"Other person: {other_name}. {other_persona}\n"
		"Conversation so far: none\n"
		"Write one short line that Speaker would say first, focusing on introducing "
		"yourself or asking the other person's name, then asking about interests. "
		"Do not prefix the line with the speaker's name."
	)


def build_follow_up_prompt(
	speaker_name: str,
	other_name: str,
	speaker_persona: str,
	speaker_interests: str,
	speaker_values: str,
	other_persona: str,
	history_lines: list[str],
) -> str:
	"""Build a follow-up turn prompt using conversation history."""
	history_text = "\n".join(history_lines) if history_lines else "none"
	return (
		"You are helping simulate a conversation between two person agents.\n"
		"Goal: keep the conversation natural while trying to find shared interests.\n"
		f"You are Speaker: {speaker_name}\n"
		f"About you: {speaker_persona} {speaker_interests} {speaker_values}\n"
		f"Other person: {other_name}. {other_persona}\n"
		f"Conversation so far:\n{history_text}\n"
		"Write one short reply for Speaker. Ask or respond in a way that helps identify shared interests. "
		"Do not prefix the line with the speaker's name."
	)


def _extract_text_from_llm_response(response: Any) -> str:
	"""Extract best-effort text from a typical chat-completion style response."""
	if response is None:
		return ""
	if isinstance(response, str):
		return response.strip()
	if isinstance(response, dict):
		choices = response.get("choices")
		if isinstance(choices, list) and choices:
			message = choices[0].get("message") if isinstance(choices[0], dict) else None
			if isinstance(message, dict):
				content = message.get("content")
				if isinstance(content, str):
					return content.strip()
		text = response.get("text")
		if isinstance(text, str):
			return text.strip()

	# Handle object responses from SDKs (e.g., OpenAI ChatCompletion objects).
	choices = getattr(response, "choices", None)
	if isinstance(choices, list) and choices:
		first_choice = choices[0]
		message_obj = getattr(first_choice, "message", None)
		if message_obj is not None:
			content = getattr(message_obj, "content", None)
			if isinstance(content, str):
				return content.strip()
		# Some SDKs may expose text directly on the choice.
		choice_text = getattr(first_choice, "text", None)
		if isinstance(choice_text, str):
			return choice_text.strip()

	text_attr = getattr(response, "text", None)
	if isinstance(text_attr, str):
		return text_attr.strip()
	return str(response).strip()


def _normalize_utterance(speaker_name: str, utterance: str) -> str:
	"""Normalize generated utterances to avoid duplicated speaker labels."""
	text = (utterance or "").strip()
	if not text:
		return text

	# Models sometimes prefix replies with "Name:" which duplicates our own formatter.
	pattern = re.compile(rf"^{re.escape(speaker_name)}\s*:\s*", flags=re.IGNORECASE)
	while True:
		updated = pattern.sub("", text, count=1).strip()
		if updated == text:
			break
		text = updated

	return text


def _extract_system_fingerprint(response: Any) -> str | None:
	"""Extract OpenAI-like system_fingerprint from dict/object responses."""
	if response is None:
		return None
	if isinstance(response, dict):
		value = response.get("system_fingerprint")
		return value if isinstance(value, str) and value.strip() else None
	value = getattr(response, "system_fingerprint", None)
	if isinstance(value, str) and value.strip():
		return value
	return None


def _fallback_turn_line(rng: random.Random, round_num: int, speaker_name: str, other_name: str) -> str:
	"""Return deterministic fallback dialogue when no LLM is configured."""
	if round_num == 1:
		return f"Hi {other_name}, I'm {speaker_name}. What's your name and what are you interested in?"
	options = [
		f"Thanks {other_name}. I would like to hear more about what you enjoy.",
		f"Nice to meet you, {other_name}. What topics do you like discussing?",
		f"Great to chat, {other_name}. Are there interests we have in common?",
	]
	return rng.choice(options)


def _build_run_dir_name(seed: int, llm_service_name: str | None, run_id: str | None = None) -> str:
	"""Build a stable directory name for this simulation run."""
	if run_id:
		return run_id
	ts = datetime.now().strftime("%Y%m%d_%H%M%S")
	service = llm_service_name or "no-llm"
	return f"run_{ts}_seed{seed}_{service}"


def _jsonl_line_count(path: Path | None) -> int:
	"""Return line count for a JSONL file, or 0 when missing/unreadable."""
	if path is None or not path.exists() or not path.is_file():
		return 0
	try:
		with path.open("r", encoding="utf-8") as handle:
			return sum(1 for _ in handle)
	except OSError:
		return 0


def _read_jsonl_slice(path: Path | None, start_index: int) -> list[str]:
	"""Read JSONL lines starting from start_index."""
	if path is None or not path.exists() or not path.is_file():
		return []
	try:
		with path.open("r", encoding="utf-8") as handle:
			lines = handle.readlines()
		return lines[start_index:]
	except OSError:
		return []


def _write_run_artifacts(
	run_dir: Path,
	console_lines: list[str],
	history_lines: list[str],
	metadata: dict,
	cache_delta_lines: list[str],
):
	"""Persist chat run artifacts for later reproducibility comparisons."""
	run_dir.mkdir(parents=True, exist_ok=True)

	console_path = run_dir / "console_output.txt"
	console_text = "\n".join(console_lines)
	if console_text:
		console_text += "\n"
	console_path.write_text(console_text, encoding="utf-8")

	transcript_path = run_dir / "conversation_transcript.txt"
	transcript_text = "\n".join(history_lines)
	if transcript_text:
		transcript_text += "\n"
	transcript_path.write_text(transcript_text, encoding="utf-8")

	metadata_path = run_dir / "run_metadata.json"
	metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

	cache_delta_path = run_dir / "prompt_response_cache_delta.jsonl"
	cache_delta_path.write_text("".join(cache_delta_lines), encoding="utf-8")


def run(
	seed: int = 42,
	year: int = 2026,
	llm_service=None,
	api_key: str | None = None,
	model: str | None = None,
	llm_seed: int | None = None,
	ons_male_file: Path | None = None,
	ons_female_file: Path | None = None,
	output_root: Path | None = None,
	run_id: str | None = None,
):
	"""
	Run the simulation and write transcript output.

	Args:
		seed: Random seed used for deterministic output.
		year: Simulation year used by the environment.
		llm_service: Optional object with a send(api_key, message, model) method.
		api_key: API key for the selected llm_service.
		model: Optional model name for the llm_service.
		llm_seed: Optional provider request seed for best-effort reproducibility.
		ons_male_file: Optional path to ONS male names CSV.
		ons_female_file: Optional path to ONS female names CSV.
		output_root: Root directory for per-run output artifact directories.
		run_id: Optional run directory name.

	Returns:
		Path to the created run output directory.
	"""

	# 1. Create environment
	# 2. Create two people with random traits, interests and opinions.
	# 3. Randomly select a person to start the chat.
	# 4. Instigate a conversation between the people using an LLM Service.

	# Initialize random number generator for deterministic output
	rng = random.Random(seed)
	console_lines: list[str] = []

	service_name = None
	if llm_service is not None:
		service_name = getattr(llm_service, "SERVICE_NAME", None)
	if service_name is None:
		service_name = "no-llm"

	resolved_output_root = Path(output_root) if output_root is not None else _DEFAULT_OUTPUT_ROOT
	run_dir_name = _build_run_dir_name(seed=seed, llm_service_name=service_name, run_id=run_id)
	run_dir = resolved_output_root / run_dir_name

	cache_jsonl_path = None
	if llm_service is not None:
		jsonl_raw = getattr(llm_service, "jsonl_path", None)
		if jsonl_raw:
			cache_jsonl_path = Path(jsonl_raw)
	cache_line_count_before = _jsonl_line_count(cache_jsonl_path)

	def emit(line: str):
		print(line)
		console_lines.append(line)

	# 1. Create environment
	env = Environment(year=year)

	# 2. Create people
	people = env.create_random_people(
		count=2,
		start_person_id=1,
		seed=seed,
		with_interests=True,
		ons_male_file=ons_male_file or _DEFAULT_ONS_MALE_FILE,
		ons_female_file=ons_female_file or _DEFAULT_ONS_FEMALE_FILE,
	)
	name_1, name_2 = people[0].get_name(), people[1].get_name()

	# 3. Randomly select a person to start the chat.
	first_speaker_index = rng.randint(0, len(people) - 1)
	second_speaker_index = (first_speaker_index + 1) % len(people)

	# 4. Instigate a conversation between the people using an LLM Service.
	# Get the first and second speaker objects
	# First speaker
	first_speaker = people[first_speaker_index]
	first_speaker_name = name_1 if first_speaker_index == 0 else name_2
	emit(str(first_speaker))
	first_speaker_persona = first_speaker.get_persona()
	emit(first_speaker_persona)
	first_speaker_interests = first_speaker.get_interests_summary()
	emit(first_speaker_interests)
	first_speaker_values = first_speaker.get_values_summary()
	emit(first_speaker_values)

	# Second speaker
	second_speaker = people[second_speaker_index]
	second_speaker_name = name_1 if second_speaker_index == 0 else name_2
	emit(str(second_speaker))
	second_speaker_persona = second_speaker.get_persona()
	emit(second_speaker_persona)
	second_speaker_interests = second_speaker.get_interests_summary()
	emit(second_speaker_interests)
	second_speaker_values = second_speaker.get_values_summary()
	emit(second_speaker_values)
	emit(f"Participants: {first_speaker_name} and {second_speaker_name}")

	# Simulate a conversation between the two speakers with a fixed number of rounds.
	num_rounds = 4
	history_lines: list[str] = []
	request_options = {"seed": llm_seed} if llm_seed is not None else None
	openai_system_fingerprints: set[str] = set()
	for round_num in range(1, num_rounds + 1):
		speaker, other = (
			(first_speaker, second_speaker) if round_num % 2 == 1 else (second_speaker, first_speaker)
		)
		speaker_name, other_name = (
			(first_speaker_name, second_speaker_name) if round_num % 2 == 1 else (second_speaker_name, first_speaker_name)
		)
		speaker_persona = speaker.get_persona()
		speaker_interests = speaker.get_interests_summary()
		speaker_values = speaker.get_values_summary()
		other_persona = other.get_persona()

		utterance = ""
		if llm_service is not None and api_key:
			if round_num == 1:
				prompt = build_first_turn_prompt(
					speaker_name=speaker_name,
					other_name=other_name,
					speaker_persona=speaker_persona,
					speaker_interests=speaker_interests,
					speaker_values=speaker_values,
					other_persona=other_persona,
				)
			else:
				prompt = build_follow_up_prompt(
					speaker_name=speaker_name,
					other_name=other_name,
					speaker_persona=speaker_persona,
					speaker_interests=speaker_interests,
					speaker_values=speaker_values,
					other_persona=other_persona,
					history_lines=history_lines,
				)
			response = llm_service.send(api_key, prompt, model=model, request_options=request_options)
			utterance = _extract_text_from_llm_response(response)
			fingerprint = _extract_system_fingerprint(response)
			if fingerprint:
				openai_system_fingerprints.add(fingerprint)

		if not utterance:
			utterance = _fallback_turn_line(rng, round_num, speaker_name, other_name)

		utterance = _normalize_utterance(speaker_name, utterance)

		line = f"Round {round_num}: {speaker_name}: {utterance}"
		emit(line)
		history_lines.append(line)

	cache_delta_lines = _read_jsonl_slice(cache_jsonl_path, cache_line_count_before)
	metadata = {
		"seed": seed,
		"year": year,
		"llm_service": service_name,
		"llm_seed": llm_seed,
		"cache_enabled": None if llm_service is None else bool(getattr(llm_service, "use_cache", True)),
		"model": model,
		"openai_system_fingerprints": sorted(openai_system_fingerprints),
		"ons_male_file": str(ons_male_file or _DEFAULT_ONS_MALE_FILE),
		"ons_female_file": str(ons_female_file or _DEFAULT_ONS_FEMALE_FILE),
		"participants": [first_speaker_name, second_speaker_name],
		"run_dir": str(run_dir),
		"cache_jsonl_path": str(cache_jsonl_path) if cache_jsonl_path is not None else None,
		"cache_delta_line_count": len(cache_delta_lines),
		"created_at": datetime.now().isoformat(timespec="seconds"),
	}
	_write_run_artifacts(
		run_dir=run_dir,
		console_lines=console_lines,
		history_lines=history_lines,
		metadata=metadata,
		cache_delta_lines=cache_delta_lines,
	)

	return run_dir

if __name__ == "__main__":
	args = parse_cli_args()
	llm_service_name = resolve_llm_service_name(args.llm_service)
	llm_service = build_llm_service(llm_service_name)
	if llm_service is not None and args.no_cache:
		llm_service.use_cache = False
	api_key = resolve_llm_api_key(args.api_key, llm_service_name, args.api_key_file)
	model = resolve_llm_model(args.model)
	llm_seed = resolve_llm_seed(args.llm_seed)
	run(
		seed=args.seed,
		year=args.year,
		llm_service=llm_service,
		api_key=api_key,
		model=model,
		llm_seed=llm_seed,
		ons_male_file=resolve_ons_male_file(args.ons_male_file),
		ons_female_file=resolve_ons_female_file(args.ons_female_file),
		output_root=args.output_root,
		run_id=args.run_id,
	)
