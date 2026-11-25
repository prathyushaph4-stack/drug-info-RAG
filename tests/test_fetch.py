import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fetch_labels import is_single_ingredient, pick_label  # noqa: E402


def label(substances, brand="X", product_type="HUMAN PRESCRIPTION DRUG", sections=6, size=100) -> dict:
    fields = ["indications_and_usage", "dosage_and_administration", "contraindications",
              "warnings_and_cautions", "adverse_reactions", "drug_interactions"]
    out: dict = {"openfda": {"substance_name": substances, "generic_name": [" AND ".join(substances)],
                       "brand_name": [brand], "product_type": [product_type]}}
    for f in fields[:sections]:
        out[f] = ["text " * size]
    return out


def test_combination_product_is_rejected():
    zituvimet = label(["SITAGLIPTIN", "METFORMIN HYDROCHLORIDE"], brand="ZITUVIMET")
    assert not is_single_ingredient(zituvimet, "metformin")
    assert is_single_ingredient(label(["METFORMIN HYDROCHLORIDE"]), "metformin")


def test_single_ingredient_wins_even_if_combo_has_more_text():
    combo = label(["SITAGLIPTIN", "METFORMIN HYDROCHLORIDE"], brand="ZITUVIMET", size=900)
    plain = label(["METFORMIN HYDROCHLORIDE"], brand="GLUCOPHAGE", size=50)
    chosen, single = pick_label([combo, plain], "metformin")
    assert chosen is not None
    assert single and chosen["openfda"]["brand_name"] == ["GLUCOPHAGE"]


def test_prefers_more_sections_then_prescription():
    thin_otc = label(["ASPIRIN"], product_type="HUMAN OTC DRUG", sections=3)
    full_rx = label(["ASPIRIN"], product_type="HUMAN PRESCRIPTION DRUG", sections=6, brand="RX")
    chosen, single = pick_label([thin_otc, full_rx], "aspirin")
    assert chosen is not None
    assert single and chosen["openfda"]["brand_name"] == ["RX"]


def test_falls_back_and_flags_when_only_combinations_exist():
    combo = label(["AMLODIPINE", "BENAZEPRIL"])
    chosen, single = pick_label([combo], "amlodipine")
    assert chosen is combo and single is False


def test_no_results():
    assert pick_label([], "metformin") == (None, False)