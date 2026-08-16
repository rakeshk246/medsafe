"""
med_db.py — Curated Medicine Database & Interaction Checker Engine
Fixed: Pairwise interaction checking across all entered medicines, warning deduplication, unknown medicine detection, and expanded drug catalog.
"""

from rapidfuzz import process, fuzz

# Expanded Local Medicine Database
MED_DB = {
    "ibuprofen": {
        "name": "Ibuprofen",
        "standard_dose_mg": {"adult": 200},
        "drug_salt": "Ibuprofen",
        "category": "NSAID / Anti-inflammatory",
        "interactions": {
            "warfarin": "High - severe bleeding risk; avoid concomitant NSAIDs and anticoagulants.",
            "aspirin": "Moderate - additive GI ulceration risk and reduced cardioprotective effect.",
            "methotrexate": "Moderate - may decrease renal clearance of methotrexate leading to toxicity.",
            "lisinopril": "Moderate - NSAIDs may reduce the antihypertensive effect of ACE inhibitors."
        }
    },
    "warfarin": {
        "name": "Warfarin",
        "standard_dose_mg": {"adult": 5},
        "drug_salt": "Warfarin Sodium",
        "category": "Anticoagulant (Blood Thinner)",
        "interactions": {
            "ibuprofen": "High - severe bleeding risk; avoid concomitant NSAIDs.",
            "aspirin": "High - additive antiplatelet/anticoagulant bleeding risk.",
            "clopidogrel": "High - major bleeding hazard with dual antithrombotic therapy.",
            "amoxicillin": "Moderate - broad-spectrum antibiotics may increase Warfarin's anticoagulant effect."
        }
    },
    "aspirin": {
        "name": "Aspirin",
        "standard_dose_mg": {"adult": 75},
        "drug_salt": "Acetylsalicylic Acid",
        "category": "NSAID / Antiplatelet",
        "interactions": {
            "warfarin": "High - severe gastrointestinal and systemic bleeding risk.",
            "ibuprofen": "Moderate - increased GI irritation; Ibuprofen may block Aspirin's antiplatelet action.",
            "methotrexate": "High - displaces methotrexate from plasma proteins, increasing toxicity risk."
        }
    },
    "paracetamol": {
        "name": "Paracetamol",
        "standard_dose_mg": {"adult": 500},
        "drug_salt": "Acetaminophen",
        "category": "Analgesic / Antipyretic",
        "interactions": {
            "alcohol": "Moderate - increased potential for severe hepatotoxicity with heavy alcohol intake.",
            "warfarin": "Low-Moderate - prolonged high-dose paracetamol may slightly enhance anticoagulant effect."
        }
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "standard_dose_mg": {"adult": 500},
        "drug_salt": "Amoxicillin Trihydrate",
        "category": "Antibiotic (Penicillin)",
        "interactions": {
            "warfarin": "Moderate - may alter gut flora and prolong prothrombin time / INR."
        }
    },
    "metformin": {
        "name": "Metformin",
        "standard_dose_mg": {"adult": 500},
        "drug_salt": "Metformin Hydrochloride",
        "category": "Antidiabetic (Biguanide)",
        "interactions": {
            "cimetidine": "Moderate - reduced renal clearance of metformin, increasing lactic acidosis risk."
        }
    },
    "lisinopril": {
        "name": "Lisinopril",
        "standard_dose_mg": {"adult": 10},
        "drug_salt": "Lisinopril",
        "category": "ACE Inhibitor / Antihypertensive",
        "interactions": {
            "ibuprofen": "Moderate - reduced blood pressure control and potential renal function decline.",
            "spironolactone": "High - risk of severe hyperkalemia (high serum potassium levels)."
        }
    },
    "methotrexate": {
        "name": "Methotrexate",
        "standard_dose_mg": {"adult": 7.5},
        "drug_salt": "Methotrexate Sodium",
        "category": "Antimetabolite / Immunosuppressant",
        "interactions": {
            "ibuprofen": "High - increased risk of methotrexate toxicity due to decreased renal excretion.",
            "aspirin": "High - enhanced bone marrow suppression and GI toxicity."
        }
    },
    "clopidogrel": {
        "name": "Clopidogrel",
        "standard_dose_mg": {"adult": 75},
        "drug_salt": "Clopidogrel Bisulfate",
        "category": "Antiplatelet Agent",
        "interactions": {
            "warfarin": "High - severe bleeding risk.",
            "omeprazole": "Moderate - PPI may diminish clopidogrel's antiplatelet activity via CYP2C19."
        }
    },
    "omeprazole": {
        "name": "Omeprazole",
        "standard_dose_mg": {"adult": 20},
        "drug_salt": "Omeprazole",
        "category": "Proton Pump Inhibitor (PPI)",
        "interactions": {
            "clopidogrel": "Moderate - reduced active metabolite conversion of clopidogrel."
        }
    }
}


def find_medicine(name: str, score_cutoff: float = 80.0):
    """
    Normalizes user input and performs RapidFuzz fuzzy matching against known DB keys.
    Returns matched canonical key or None.
    """
    if not name or not isinstance(name, str):
        return None

    cleaned = name.lower().replace("+", " ").replace(",", " ").replace(".", " ").replace("-", " ").strip()
    if not cleaned:
        return None

    names = list(MED_DB.keys())
    match_result = process.extractOne(cleaned, names, scorer=fuzz.WRatio)

    if match_result and match_result[1] >= score_cutoff:
        return match_result[0]
    return None


def check_interactions(medicines: list):
    """
    Evaluates drug-drug interactions pairwise across ALL entered medicines.
    Returns a deduplicated list of formatted interaction warning strings.
    """
    if not medicines:
        return []

    # Map inputs to canonical DB keys
    canonical_keys = []
    unknowns = []

    for med in medicines:
        if not med or not str(med).strip():
            continue
        key = find_medicine(str(med).strip())
        if key:
            if key not in canonical_keys:
                canonical_keys.append(key)
        else:
            unknowns.append(str(med).strip())

    warnings = []

    # Pairwise comparison across all resolved medicines
    for i in range(len(canonical_keys)):
        for j in range(i + 1, len(canonical_keys)):
            k1 = canonical_keys[i]
            k2 = canonical_keys[j]

            med1_data = MED_DB[k1]
            med2_data = MED_DB[k2]

            # Check direct interactions in k1's record for k2
            k1_interactions = med1_data.get("interactions", {})
            if k2 in k1_interactions:
                warn_text = f"{med1_data['name']} + {med2_data['name']}: {k1_interactions[k2]}"
                if warn_text not in warnings:
                    warnings.append(warn_text)

            # Check reverse interactions in k2's record for k1
            k2_interactions = med2_data.get("interactions", {})
            if k1 in k2_interactions:
                warn_text = f"{med2_data['name']} + {med1_data['name']}: {k2_interactions[k1]}"
                if warn_text not in warnings:
                    warnings.append(warn_text)

    # Append note for unknown medicines if any were entered
    if unknowns:
        unknown_str = ", ".join(unknowns)
        warnings.append(f"Note: '{unknown_str}' not found in local drug database for automated pairwise checking.")

    return warnings


def llama_short_warning(lines: list, ollama_client=None, model_name: str = "LLaMA3") -> str:
    """
    Summarizes interaction warnings into ONE short, clear educational sentence using LLaMA3.
    """
    if not lines:
        return "No specific medicine safety warnings detected."

    prompt = f"""
Medicines safety note:

{chr(10).join(lines)}

Summarize into ONE short, clear safety sentence.
No diagnosis. Educational only.
"""
    if ollama_client:
        try:
            response = ollama_client.generate(model=model_name, prompt=prompt)
            return response["response"].strip()
        except Exception:
            pass

    # Safe fallback response when Ollama is offline
    relevant_lines = [l for l in lines if not l.startswith("Note:")]
    if relevant_lines:
        return f"Safety Warning: Co-administering these medications presents risk ({relevant_lines[0]}). Please consult your prescribing physician."
    return "Ensure you verify all new medications with a licensed pharmacist or physician."
