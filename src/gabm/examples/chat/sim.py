"""
Chat simulation example module.

This module contains runnable example simulation logic that can be imported
from tests to verify deterministic and reproducible outputs.
"""

# Standard library imports
import random
from pathlib import Path

# Local imports
from gabm.abm.agent import Person
from gabm.abm.environment import Environment
from gabm.abm.attributes.gender import GenderID
from gabm.abm.attributes.interest import Interest, InterestTopicID, InterestValue, InterestValueMap


def build_interest(topic_id: int, value: int, label: str) -> Interest:
	"""Create an Interest object for one topic/value pair."""
	interest_topic_id = InterestTopicID(topic_id)
	interest_value = InterestValue(interest_topic_id, value, label)
	return Interest(interest_topic_id, InterestValueMap({interest_topic_id: interest_value}), value)


def build_persona_line(person: Person) -> str:
	"""Create a compact persona line for transcript readability."""
	return (
		f"Person {person.id}: age={person.get_age()}, "
		f"gender={person.get_gender()}, "
		f"interests={len(person.interests)}"
	)


def generate_transcript_lines(seed: int = 42, year: int = 2026) -> list[str]:
	"""
	Generate deterministic transcript lines for a two-person chat simulation.

	Args:
		seed: Random seed controlling deterministic choice of dialogue lines.
		year: Simulation year used by the environment.

	Returns:
		Transcript lines.
	"""
	rng = random.Random(seed)
	env = Environment(year=year)

	person1 = Person(person_id=1, environment=env, year_of_birth=1975, gender_id=GenderID(0))
	person2 = Person(person_id=2, environment=env, year_of_birth=1992, gender_id=GenderID(1))

	person1.interests = {
		InterestTopicID(0): build_interest(0, 2, "very interested"),
		InterestTopicID(1): build_interest(1, 1, "interested"),
		InterestTopicID(2): build_interest(2, 0, "occasionally interested"),
	}
	person2.interests = {
		InterestTopicID(0): build_interest(0, 1, "interested"),
		InterestTopicID(1): build_interest(1, 2, "very interested"),
		InterestTopicID(3): build_interest(3, 1, "interested"),
	}

	env.agents_active[1] = person1
	env.agents_active[2] = person2

	p1_line = build_persona_line(person1)
	p2_line = build_persona_line(person2)

	shared_topics = sorted(
		set(person1.interests.keys()).intersection(person2.interests.keys()),
		key=lambda topic: topic.id,
	)
	shared_text = ", ".join(str(topic.id) for topic in shared_topics) if shared_topics else "none"

	person1_candidates = [
		"I enjoy topics where we both have interest overlap.",
		"Shared interests are a good start for dialogue.",
		"Let us begin with topics where both of us care.",
	]
	person2_candidates = [
		"Same here, maybe we should start with music and sports.",
		"Agreed, overlap helps us communicate better.",
		"Yes, common ground should make this easier.",
	]

	person1_line = rng.choice(person1_candidates)
	person2_line = rng.choice(person2_candidates)

	return [
		"Simple conversation transcript",
		f"seed={seed}",
		p1_line,
		p2_line,
		f"Shared interest topic IDs: {shared_text}",
		f"Person 1: {person1_line}",
		f"Person 2: {person2_line}",
	]


def run(output_dir: Path | None = None, seed: int = 42, year: int = 2026) -> Path:
	"""
	Run the simulation and write transcript output.

	Args:
		output_dir: Directory for transcript output. If None, defaults to
			tests/src/gabm/examples/chat/output relative to repository root.
		seed: Random seed used for deterministic output.
		year: Simulation year used by the environment.

	Returns:
		Path to the output transcript file.
	"""
	lines = generate_transcript_lines(seed=seed, year=year)

	if output_dir is None:
		repo_root = Path(__file__).resolve().parents[4]
		output_dir = repo_root / "tests" / "src" / "gabm" / "examples" / "chat" / "output"

	output_dir.mkdir(parents=True, exist_ok=True)
	output_file = output_dir / "conversation_transcript.txt"
	output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
	return output_file


if __name__ == "__main__":
	written = run()
	print(f"Wrote transcript: {written}")
