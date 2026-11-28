import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from drug_classes import DRUG_CLASSES  # noqa: E402
from drugs import DRUGS  # noqa: E402


def test_every_drug_has_class_terms():
    assert set(DRUG_CLASSES) == set(DRUGS)
    assert all(terms and all(isinstance(t, str) and t.strip() for t in terms) for terms in DRUG_CLASSES.values())


def test_key_label_vocabulary_is_present():
    assert "NSAIDs" in DRUG_CLASSES["ibuprofen"]
    assert "benzodiazepines" in DRUG_CLASSES["alprazolam"]
    assert "opioids" in DRUG_CLASSES["tramadol"]
    assert "serotonin reuptake inhibitors" in DRUG_CLASSES["sertraline"]