"""Step 2: download official FDA drug labels from openFDA and save them as JSON.

Run from the project root:
    python src/fetch_labels.py

openFDA is free and needs no API key for light use (about 40 requests/minute).
Each drug is saved to data/raw/<drug>.json containing only the sections we use.
"""
import json
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


def search_label(drug: str, retries: int = 3) -> dict | None:
    """Return the most complete label found for a generic drug name."""
    params = {
        "search": f'openfda.generic_name:"{drug}"',
        "limit": 5,
    }
    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, timeout=30)
            if resp.status_code == 404:
                return None  # no match
            resp.raise_for_status()
            results = resp.json().get("results", [])
            # choose the label that has the most of our sections filled in
            return max(results, key=lambda r: sum(f in r for f in SECTIONS), default=None)
        except requests.RequestException as err:
            print(f"  attempt {attempt + 1} failed for {drug}: {err}")
            time.sleep(2 * (attempt + 1))
    return None


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
    saved, missing = 0, []
    for drug in DRUGS:
        label = search_label(drug)
        if label is None:
            print(f"[skip] {drug}: no label found")
            missing.append(drug)
            continue
        sections = extract_sections(label)
        record = {
            "drug": drug,
            "set_id": label.get("set_id", ""),
            "effective_time": label.get("effective_time", ""),
            "source_url": f"https://api.fda.gov/drug/label.json?search=set_id:{label.get('set_id', '')}",
            "sections": sections,
        }
        (RAW_DIR / f"{drug.replace(' ', '_')}.json").write_text(json.dumps(record, indent=2))
        print(f"[ok]   {drug}: {len(sections)} sections")
        saved += 1
        time.sleep(1.6)  # stay under the free rate limit
    print(f"\nSaved {saved}/{len(DRUGS)} labels. Missing: {missing or 'none'}")


if __name__ == "__main__":
    main()
