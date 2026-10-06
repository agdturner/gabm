"""
Tests for trait module.
"""
# Metadata
__author__ = ["Andy Turner <agdturner@gmail.com>"]
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2026 GABM contributors, University of Leeds"


# Third-party imports
import pytest
# Local imports
from gabm.abm.attributes.trait import TraitTopicID, TraitTopic, TraitValue, TraitValueMap, Trait
from gabm.abm.attributes.gender import GenderID
from gabm.core.id import GABMID

def test_trait_topic_id():
    itid0 = TraitTopicID(0)
    itid1 = TraitTopicID(1)
    itid00 = TraitTopicID(0)
    gid0 = GenderID(0)
    gabmid0 = GABMID(0)
    assert str(itid0) == "TraitTopicID(0)"
    assert itid0 == itid00
    assert itid0 != itid1
    assert itid0 != gid0
    assert itid0 != gabmid0

def test_trait_topic():
    tid = TraitTopicID(0)
    topic = TraitTopic(tid, "high", "A high trait.")
    assert topic.id == tid
    assert topic.topic == "high"
    assert topic.description == "A high trait."
    assert "TraitTopic" in str(topic)
    assert "TraitTopic" in repr(topic)

def test_trait_value():
    tid = TraitTopicID(0)
    val = TraitValue(tid, 2, "Very high")
    assert val.trait_topic_id == tid
    assert val.value == 2
    assert val.description == "Very high"
    assert "TraitValue" in str(val)
    assert "TraitValue" in repr(val)

def test_trait_value_map():
    tid = TraitTopicID(0)
    val = TraitValue(tid, 2, "Very high")
    values = TraitValueMap({tid: val})
    assert values.values[tid] == val
    assert "TraitValueMap" in str(values)

def test_trait():
    tid = TraitTopicID(0)
    val = TraitValue(tid, 2, "Very high")
    values = TraitValueMap({tid: val})
    trait = Trait(tid, values, 2)
    assert trait.id == tid
    assert trait.trait_values == values
    assert trait.value == 2
    assert "Trait" in str(trait)
    assert trait.get_description() == "Very high"
    trait2 = Trait(tid, values, 99)
    assert trait2.get_description() is None
