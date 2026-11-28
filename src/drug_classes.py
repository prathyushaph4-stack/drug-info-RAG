"""Drug-class vocabulary used to expand two-drug questions.

FDA labels often name the CLASS of an interacting drug (NSAIDs, benzodiazepines,
opioids, serotonin reuptake inhibitors) and not the specific drug. When a question
names two drugs, retrieval for drug A also searches with drug B's class terms, so
A's label sections that mention B's class are found.

The terms below use the wording labels tend to use. DRAFT: needs a pharmacist's review.
"""

SSRI = ["SSRIs", "selective serotonin reuptake inhibitors", "serotonin reuptake inhibitors", "antidepressants"]
NSAID = ["NSAIDs", "nonsteroidal anti-inflammatory drugs"]
STATIN = ["statins", "HMG-CoA reductase inhibitors"]
ANTIBIOTIC = ["antibacterial drugs", "antibiotics"]

DRUG_CLASSES: dict[str, list[str]] = {
    "metformin": ["biguanide"],
    "glipizide": ["sulfonylurea"],
    "sitagliptin": ["DPP-4 inhibitor", "dipeptidyl peptidase-4 inhibitor"],
    "insulin glargine": ["insulin"],
    "lisinopril": ["ACE inhibitors", "angiotensin converting enzyme inhibitors"],
    "amlodipine": ["calcium channel blocker"],
    "losartan": ["angiotensin receptor blockers", "ARBs"],
    "metoprolol": ["beta-blockers"],
    "atenolol": ["beta-blockers"],
    "hydrochlorothiazide": ["thiazide diuretics", "diuretics"],
    "furosemide": ["loop diuretics", "diuretics"],
    "spironolactone": ["potassium-sparing diuretics", "diuretics", "aldosterone antagonist"],
    "atorvastatin": STATIN,
    "simvastatin": STATIN,
    "warfarin": ["anticoagulants", "coumarin"],
    "clopidogrel": ["antiplatelet agents"],
    "aspirin": NSAID + ["salicylates", "antiplatelet agents"],
    "ibuprofen": NSAID,
    "acetaminophen": ["analgesics"],
    "naproxen": NSAID,
    "diclofenac": NSAID,
    "tramadol": ["opioids", "opioid analgesics"],
    "prednisone": ["corticosteroids"],
    "amoxicillin": ["penicillins"] + ANTIBIOTIC,
    "azithromycin": ["macrolides"] + ANTIBIOTIC,
    "ciprofloxacin": ["fluoroquinolones"] + ANTIBIOTIC,
    "doxycycline": ["tetracyclines"] + ANTIBIOTIC,
    "omeprazole": ["proton pump inhibitors"],
    "pantoprazole": ["proton pump inhibitors"],
    "ondansetron": ["5-HT3 receptor antagonists", "antiemetics"],
    "levothyroxine": ["thyroid hormones"],
    "sertraline": SSRI,
    "fluoxetine": SSRI,
    "escitalopram": SSRI,
    "alprazolam": ["benzodiazepines"],
    "gabapentin": ["gabapentinoids", "antiepileptic drugs"],
    "cetirizine": ["antihistamines"],
    "loratadine": ["antihistamines"],
    "montelukast": ["leukotriene receptor antagonists"],
    "albuterol": ["beta-agonists", "bronchodilators"],
}