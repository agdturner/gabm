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

def run(seed: int = 42, year: int = 2026):
	"""
	Run the simulation and write transcript output.

	Args:
		seed: Random seed used for deterministic output.
		year: Simulation year used by the environment.
	"""

	# 1. Create environment
	# 2. Create two people with random traits, interests and opinions.
	# 3. Randomly select a person to start the chat.
	# 4. Initialize a 
	# 5. Repeat until a total of 4 rounds of dialogue have occurred.

	# Initialize random number generator for deterministic output
	rng = random.Random(seed)

	# 1. Create environment
	env = Environment(year=year)

	likert_scale = {
		-2: "strongly dislike",
		-1: "dislike",
		0: "neutral",
		1: "like",
		2: "strongly like"
	}

	# 2. Create people
	people = env.create_random_people(
		count=50,
		start_person_id=1,
		seed=seed,
		with_interests=True,
	)
	
	# 3. Randomly select a person to start the chat.
	first_speaker_index = rng.randint(0, len(people) - 1)
	second_speaker_index = (first_speaker_index + 1) % len(people)

	# 4. Get the first and second speaker objects
	# First speaker
	first_speaker = people[first_speaker_index]
	print(first_speaker)
	first_speaker_persona = first_speaker.get_persona()
	print(first_speaker_persona)
	first_speaker_interests = first_speaker.get_interests_summary()
	print(first_speaker_interests)
	first_speaker_values = first_speaker.get_values_summary()
	print(first_speaker_values)
	
	# Second speaker
	second_speaker = people[second_speaker_index]
	print(second_speaker)
	second_speaker_persona = second_speaker.get_persona()
	print(second_speaker_persona)
	second_speaker_interests = second_speaker.get_interests_summary()
	print(second_speaker_interests)
	second_speaker_values = second_speaker.get_values_summary()
	print(second_speaker_values)

	# 5. Set up the LLM
	
	
if __name__ == "__main__":
	run()
