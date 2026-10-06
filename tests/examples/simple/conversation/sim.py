# Simple conversation simulation
# This script simulates a conversation between two people agents.

# Create An environment
env = Environment()

# Create a list of interest topics
# tid_0
tid_0 = InterestTopicID(0)
i_0_n2 = InterestValue(tid_0, -2, "very uninterested")
i_0_n1 = InterestValue(tid_0, -1, "uninterested")
i_0_0 = InterestValue(tid_0, 0, "no interest")
i_0_1 = InterestValue(tid_0, 1, "interested")
i_0_2 = InterestValue(tid_0, 2, "very interested")

# tid_1
tid_1 = InterestTopicID(1)
i_1_n2 = InterestValue(tid_1, -2, "very uninterested")
i_1_n1 = InterestValue(tid_1, -1, "uninterested")
i_1_0 = InterestValue(tid_1, 0, "no interest")
i_1_1 = InterestValue(tid_1, 1, "interested")
i_1_2 = InterestValue(tid_1, 2, "very interested")

# tid_2
tid_2 = InterestTopicID(2)
i_2_n2 = InterestValue(tid_2, -2, "very uninterested")
i_2_n1 = InterestValue(tid_2, -1, "uninterested")
i_2_0 = InterestValue(tid_2, 0, "no interest")
i_2_1 = InterestValue(tid_2, 1, "interested")
i_2_2 = InterestValue(tid_2, 2, "very interested")


values = InterestValueMap({tid: val})
    interest = Interest(tid, values, 2)
    assert interest.id == tid
    assert interest.opinion_values == values
    assert interest.value == 2
    assert "Interest" in str(interest)
    assert interest.get_description() == "Strongly positive"
    interest2 = Interest(tid, values, 99)
    assert interest2.get_description() is None
interest_topics = [
    InterestTopic(InterestTopicID(0), "sport", "Interest in sport."),
    InterestTopic(InterestTopicID(1), "music", "Interest in music."),
    InterestTopic(InterestTopicID(2), "reading", "Interest in reading."),
    InterestTopic(InterestTopicID(3), "travel", "Interest in travel."),
    InterestTopic(InterestTopicID(4), "cooking", "Interest in cooking."),
    InterestTopic(InterestTopicID(5), "gardening", "Interest in gardening."),
    InterestTopic(InterestTopicID(6), "art", "Interest in art."),
    InterestTopic(InterestTopicID(7), "nature", "Interest in nature."),
    InterestTopic(InterestTopicID(8), "technology", "Interest in technology."),
    InterestTopic(InterestTopicID(9), "history", "Interest in history."),
    InterestTopic(InterestTopicID(10), "politics", "Interest in politics."),
    InterestTopic(InterestTopicID(11), "science", "Interest in science.")
]

# Create two Person agents with different profiles
year_of_birth1 = 1975
gender_id1 = GenderID(0)  # Male
# This person likes most interests, but dislikes gardening and politics.

interests1 = {
    InterestTopicID(0): Interest(InterestTopicID(0), "sports", "Interest in sports."),
    InterestTopicID(1): Interest(InterestTopicID(1), "music", "Interest in music."),
}
person1 = Person(1975, GenderID_0,):
            The GenderID attributed.
        interests (Dict[InterestTopicID, Interest]):
            A dictionary of Interests.
            The keys are InterestTopicIDs, and the values are Interest objects.
            These are deep copied when the Person is initialised, so that the Person has their own
        opinions (Dict[OpinionTopicID, Opinion]):
            A dictionary of Opinions.
            The keys are OpinionTopicIDs, and the values are Opinion objects.
            These are deep cop


person1 = Person(, interests=["sports", "music"]))
person2 = Person(name="Bob", profile=Profile(persona="curious