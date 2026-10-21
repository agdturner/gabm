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

	# 1. Create 32 people and 1 environment
	#    Each person will have traits, interests and opinions that are randomly generated.
	# 2. Randomly assign people to one of two groups.
	# 3. Randomly pair people in each group.
	# 4. Each pair chats to learn about each others traits, interests and opinions.
	# 5. Repeat Step 3 and 4 four times.
	# 6. Survey the people in each group about if they want to leave this group and join the other group.
	# 5. Repeat Step 2 to 4 for a 2 rounds.
	# 6. Compare the surveys from the rounds.
	# 7. Repeat Steps 2 to 6 again.
	# 8. Compare the final surveys.

	for ite in range(2):
		# Create people and environment
		for ite in range(2):
			for round in range(4):
				# Randomly pair people to have a brief chat.
	 			# They learn each others name and something about each others traits, interests and opinions.
				# They reflect on what they learned and how they feel about the other person.
			# Survey the people about their interests and opinions.
		# Compare the surveys from the rounds.
	# Compare the final surveys.
				pass
		transcript_lines = generate_transcript_lines(seed=seed, year=year)
		if output_dir is None:
			output_dir = Path(__file__).parent / "output"
		output_dir.mkdir(parents=True, exist_ok=True)
		output_file = output_dir / f"transcript_seed{seed}_round{ite}.txt"
		with open(output_file, "w") as f:
			for line in transcript_lines:
				f.write(line + "\n")

if __name__ == "__main__":
	written = run()
	print(f"Wrote transcript: {written}")
