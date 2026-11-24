"""The 40 drugs used in this project (generic names, as openFDA lists them).

Mix of diabetes, heart/blood pressure, pain, antibiotics, mental health,
respiratory and a few well-known interaction pairs (e.g. warfarin + ibuprofen,
lisinopril + spironolactone, sertraline + tramadol).
"""

DRUGS = [
    # Diabetes
    "metformin", "glipizide", "sitagliptin", "insulin glargine",
    # Heart / blood pressure / cholesterol
    "lisinopril", "amlodipine", "losartan", "metoprolol", "atenolol",
    "hydrochlorothiazide", "furosemide", "spironolactone",
    "atorvastatin", "simvastatin",
    # Blood thinners
    "warfarin", "clopidogrel", "aspirin",
    # Pain / inflammation
    "ibuprofen", "acetaminophen", "naproxen", "diclofenac", "tramadol",
    "prednisone",
    # Antibiotics
    "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline",
    # Stomach / thyroid
    "omeprazole", "pantoprazole", "ondansetron", "levothyroxine",
    # Mental health / neurology
    "sertraline", "fluoxetine", "escitalopram", "alprazolam", "gabapentin",
    # Allergy / respiratory
    "cetirizine", "loratadine", "montelukast", "albuterol",
]

assert len(DRUGS) == len(set(DRUGS)) == 40, len(DRUGS)
