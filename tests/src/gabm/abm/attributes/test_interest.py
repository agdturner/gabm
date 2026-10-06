"""
Tests for interest module.
"""
# Metadata
__author__ = ["Andy Turner <agdturner@gmail.com>"]
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2026 GABM contributors, University of Leeds"


# Third-party imports
import pytest
# Local imports
from gabm.abm.attributes.interest import InterestTopicID, InterestTopic, InterestValue, InterestValueMap, Interest
from gabm.abm.attributes.gender import GenderID
from gabm.core.id import GABMID

def test_interest_topic_id():
    itid0 = InterestTopicID(0)
    itid1 = InterestTopicID(1)
    itid00 = InterestTopicID(0)
    gid0 = GenderID(0)
    gabmid0 = GABMID(0)
    assert str(itid0) == "InterestTopicID(0)"
    assert itid0 == itid00
    assert itid0 != itid1
    assert itid0 != gid0
    assert itid0 != gabmid0

def test_interest_topic():
    tid = InterestTopicID(0)
    topic = InterestTopic(tid, "high", "A high interest.")
    assert topic.id == tid
    assert topic.topic == "high"
    assert topic.description == "A high interest."
    assert "InterestTopic" in str(topic)
    assert "InterestTopic" in repr(topic)

def test_interest_value():
    tid = InterestTopicID(0)
    val = InterestValue(tid, 2, "Very high")
    assert val.interest_topic_id == tid
    assert val.value == 2
    assert val.description == "Very high"
    assert "InterestValue" in str(val)
    assert "InterestValue" in repr(val)

def test_interest_value_map():
    tid = InterestTopicID(0)
    val = InterestValue(tid, 2, "Very high")
    values = InterestValueMap({tid: val})
    assert values.values[tid] == val
    assert "InterestValueMap" in str(values)

def test_interest():
    tid = InterestTopicID(0)
    val = InterestValue(tid, 2, "Very high")
    values = InterestValueMap({tid: val})
    interest = Interest(tid, values, 2)
    assert interest.id == tid
    assert interest.interest_values == values
    assert interest.value == 2
    assert "Interest" in str(interest)
    assert interest.get_description() == "Very high"
    interest2 = Interest(tid, values, 99)
    assert interest2.get_description() is None
