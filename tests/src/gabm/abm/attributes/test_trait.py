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
    """
    Test the TraitTopicID class.
    """
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
    """
    Test the TraitTopic class.
    """
    tid = TraitTopicID(0)
    tt = TraitTopic(tid, "neuroticism", "A neuroticism trait.")
    assert tt.id == tid
    assert tt.trait_topic == "neuroticism"
    assert tt.description == "A neuroticism trait."
    assert "TraitTopic" in str(tt)
    assert "TraitTopic" in repr(tt)

def test_trait_value():
    """
    Test the TraitValue class.
    """
    tid = TraitTopicID(0)
    tv = TraitValue(tid, 2, "very high")
    assert tv.trait_topic_id == tid
    assert tv.value == 2
    assert tv.description == "very high"
    assert "TraitValue" in str(tv)
    assert "TraitValue" in repr(tv)

def test_trait_value_map():
    """
    Test the TraitValueMap class.
    """
    tid = TraitTopicID(0)
    tv = TraitValue(tid, 2, "very high")
    values = TraitValueMap({tid: tv})
    assert values.values[tid] == tv
    assert "TraitValueMap" in str(values)

def test_trait():
    """
    Test the Trait class.
    """
    tid = TraitTopicID(0)
    tv = TraitValue(tid, 2, "very high")
    tvm = TraitValueMap({tid: tv})
    trait = Trait(tid, tvm, 2)
    assert trait.id == tid
    assert trait.trait_values == tvm
    assert trait.value == 2
    assert "Trait" in str(trait)
    assert trait.get_description() == "very high"
    trait2 = Trait(tid, tvm, -999)  # Value not represented for this trait topic
    assert trait2.get_description() is None
