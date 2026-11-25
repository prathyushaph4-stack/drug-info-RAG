"""Step 2: download official FDA drug labels from openFDA and save them as JSON.

Run from the project root:
    python src/fetch_labels.py

openFDA is free and needs no API key for light use (about 40 requests/minute).
Each drug is saved to data/raw/<drug>.json containing only the sections we use.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from drugs import DRUGS  # noqa: E402

API_URL = "https://api.fda.gov/drug/label.json"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# openFDA field name -> friendly section name used everywhere else in the project
SECTIONS = {
    "indications_and_usage": "Indications and Usage",
    "dosage_and_administration": "Dosage and Administration",
    "contraindications": "Contraindications",
    "warnings_and_cautions": "Warnings",
    "warnings": "Warnings",          # older labels use this name instead
    "adverse_reactions": "Adverse Reactions",
    "drug_interactions": "Drug Interactions",
}


def first(openfda: dict, key: str) -> str:
    values = openfda.get(key, [])
    return values[0] if values else ""


def is_single_ingredient(label: dict, drug: str) -> bool:
    """True only for a label whose ONLY active ingredient is this drug.

    openFDA's generic_name search also returns combination products
    (e.g. a sitagliptin + metformin pill comes back for "metformin"),
    which would put the wrong drug's text under the wrong name.
    """
    openfda = label.get("openfda", {})
    substances = [s.lower() for s in openfda.get("substance_name", [])]
    if substances:
        return len(substances) == 1 and drug.lower() in substances[0]
    generics = [g.lower() for g in openfda.get("generic_name", [])]
    return (
        len(generics) == 1
        and drug.lower() in generics[0]
        and not re.search(r"\band\b|,|/|\+", generics[0])
    )


def label_score(label: dict) -> tuple:
    """Higher is better: most sections, then prescription labels, then longest text."""
    sections = sum(f in label for f in SECTIONS)
    is_rx = "PRESCRIPTION" in first(label.get("openfda", {}), "product_type").upper()
    text_length = sum(len(" ".join(label[f])) for f in SECTIONS if f in label and isinstance(label[f], list))
    return (sections, is_rx, text_length)


def pick_label(results: list[dict], drug: str) -> tuple[dict | None, bool]:
    """Choose the best single-ingredient label. Returns (label, is_single_ingredient)."""
    single = [r for r in results if is_single_ingredient(r, drug)]
    if single:
        return max(single, key=label_score), True
    return (max(results, key=label_score) if results else None), False


def search_label(drug: str, retries: int = 3) -> tuple[dict | None, bool]:
    """Download candidate labels for a drug and pick the best single-ingredient one."""
    params = {
        "search": f'openfda.generic_name:"{drug}"',
        "limit": 100,   # many combination products exist; look at plenty of candidates
    }
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, timeout=90)
            if resp.status_code == 404:
                return None, False  # no match
            resp.raise_for_status()
            return pick_label(resp.json().get("results", []), drug)
        except requests.RequestException as err:
            print(f"  attempt {attempt + 1} failed for {drug}: {err}")
            time.sleep(2 * (attempt + 1))
    return None, False


def extract_sections(label: dict) -> dict:
    """Keep only the sections we need, as {friendly name: text}."""
    sections = {}
    for field, name in SECTIONS.items():
        if field in label and name not in sections:
            text = label[field]
            sections[name] = " ".join(text) if isinstance(text, list) else str(text)
    return sections


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    saved, missing, combos = 0, [], []
    for drug in DRUGS:
        label, single = search_label(drug)
        if label is None:
            print(f"[skip] {drug}: no label found")
            missing.append(drug)
            continue
        openfda = label.get("openfda", {})
        sections = extract_sections(label)
        record = {
            "drug": drug,
            "brand_name": first(openfda, "brand_name"),
            "generic_name": first(openfda, "generic_name"),
            "substance_names": openfda.get("substance_name", []),
            "set_id": label.get("set_id", ""),
            "effective_time": label.get("effective_time", ""),
            "source_url": f"https://api.fda.gov/drug/label.json?search=set_id:{label.get('set_id', '')}",
            "sections": sections,
        }
        (RAW_DIR / f"{drug.replace(' ', '_')}.json").write_text(json.dumps(record, indent=2))
        flag = "" if single else "   <-- CHECK: no single-ingredient label found"
        if not single:
            combos.append(drug)
        print(f"[ok]   {drug}: {len(sections)} sections | {record['brand_name']} | {record['generic_name']}{flag}")
        saved += 1
        time.sleep(1.6)  # stay under the free rate limit
    print(f"\nSaved {saved}/{len(DRUGS)} labels. Missing: {missing or 'none'}")
    print(f"Possible combination-product labels: {combos or 'none'}")


if __name__ == "__main__":
    main()