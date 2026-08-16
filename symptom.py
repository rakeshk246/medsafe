"""
symptom.py — Symptom Analysis, Side-Effect Monitoring, and Emergency Risk Scoring Engine
Implements rule-based symptom guidance, expanded LLaMA guidance, side-effect monitor, and emergency risk scoring.
"""

def symptom_advice(symptom: str) -> str:
    """
    Rule-based function identifying symptom keywords and returning predefined guidance.
    Prioritizes emergency symptoms first, then handles common symptoms (fever, headache, rash, stomach, etc.).
    """
    if not symptom or not isinstance(symptom, str):
        return "- Please enter patient symptoms for advice."

    s_lower = symptom.lower().strip()

    if any(key in s_lower for key in ["chest pain", "pressure in chest", "tightness in chest"]):
        return (
            "**Chest Pain - Emergency Symptom**\n"
            "- Could be heart-related, lungs, or gastric issues.\n"
            "- Avoid exertion, sit upright, stay calm.\n"
            "- Perform slow breathing (4 sec inhale, 6 sec exhale).\n"
            "- Do NOT take random painkillers.\n"
            "**Seek immediate medical attention.**"
        )

    if any(key in s_lower for key in ["shortness of breath", "difficulty breathing", "wheezing"]):
        return (
            "**Respiratory Distress - Urgent Warning**\n"
            "- Sit upright in a well-ventilated area.\n"
            "- Loosen tight clothing around throat and chest.\n"
            "- If severe or accompanied by blue lips/fainting, call emergency services immediately."
        )

    if "fever" in s_lower:
        return (
            "**Fever Detected**\n"
            "- Drink warm water or ORS frequently.\n"
            "- Paracetamol 500-650 mg may reduce fever.\n"
            "- Wear light clothing and rest.\n"
            "- If lasts > 3 days or > 102°F, see a doctor."
        )

    if any(key in s_lower for key in ["headache", "migraine"]):
        return (
            "**Headache Guidance**\n"
            "- Rest in a quiet, dark room and ensure adequate hydration.\n"
            "- Apply a cool compress to the forehead.\n"
            "- Seek emergency care if headache is sudden, excruciating ('thunderclap'), or accompanied by slurred speech."
        )

    if any(key in s_lower for key in ["rash", "hives", "itching"]):
        return (
            "**Skin Rash / Possible Medication Allergy**\n"
            "- Avoid scratching or applying harsh chemical soaps.\n"
            "- Monitor for facial or tongue swelling (anaphylaxis warning sign).\n"
            "- Contact your doctor to check if this is a drug-induced allergic reaction."
        )

    if any(key in s_lower for key in ["stomach pain", "nausea", "vomiting", "ulcer"]):
        return (
            "**Gastrointestinal Symptoms**\n"
            "- Sip clear fluids or oral rehydration solution (ORS).\n"
            "- Avoid spicy, acidic, or heavy oily foods.\n"
            "- Avoid NSAID painkillers like Ibuprofen on an empty stomach."
        )

    return "Rest, maintain adequate hydration, and monitor your symptoms. Consult a doctor if symptoms persist or worsen."


def llama_expand(base_text: str, user_query: str, ollama_client=None, model_name: str = "LLaMA3") -> str:
    """
    Expands rule-based symptom advice into a friendly medical guidance paragraph using Ollama LLaMA3.
    """
    prompt = f"""
User symptom: {user_query}
Basic advice: {base_text}

Expand this into a friendly medical guidance paragraph.
Include:
- 2 extra home remedies
- 1 yoga or breathing exercise
- 1 diet suggestion
- 1 warning sign to watch
Keep the tone safe and non-diagnostic.
"""
    if ollama_client:
        try:
            response = ollama_client.generate(model=model_name, prompt=prompt)
            return response["response"].strip()
        except Exception:
            pass

    return (
        f"Based on your reported symptom ('{user_query}'), follow safe home care:\n\n"
        f"**Primary Care:**\n{base_text}\n\n"
        f"**Home Remedies & Wellness:**\n"
        f"1. Drink warm chamomile or ginger tea to soothe systemic discomfort.\n"
        f"2. Ensure complete physical rest with 7-8 hours of sleep.\n"
        f"3. Practice slow diaphragmatic breathing (4s inhale, 6s exhale).\n"
        f"4. Diet: Eat light, easily digestible foods (khichdi, oats, clear soup).\n\n"
        f"**Warning Sign**: Seek immediate emergency care if you experience shortness of breath, chest tightness, or confusion."
    )


def analyze_side_effects(age, gender, med_list: list, dose_list: list, experience: str, ollama_client=None, model_name: str = "LLaMA3") -> str:
    """
    Prepares patient context for side-effect analysis and sends it to Ollama LLaMA3.
    """
    med_str = ", ".join(med_list) if isinstance(med_list, list) else str(med_list)
    dose_str = ", ".join(dose_list) if isinstance(dose_list, list) else str(dose_list)

    user_input = (
        f"Age: {age}, Gender: {gender}, Medicines: {med_str}, "
        f"Dose: {dose_str}, Experience: {experience}"
    )

    prompt = f"""
You are a medical educational assistant.

A user reports the following: {user_input}

Generate a short, clear, educational output:
- Give 2 points on what might be causing these experiences.
- Include 1 warning or precaution the user should watch.
- Keep tone informative, not diagnostic, not too short, not too long.
"""
    if ollama_client:
        try:
            response = ollama_client.generate(model=model_name, prompt=prompt)
            return response["response"].strip()
        except Exception:
            pass

    # Educational fallback
    return (
        f"**Educational Side-Effect Analysis:**\n\n"
        f"**Patient Summary:** Age {age}, {gender} | Medication: {med_str} ({dose_str})\n"
        f"**Reported Experience:** {experience}\n\n"
        f"**Possible Contributing Factors:**\n"
        f"1. Individual gastrointestinal or neurological sensitivity to the active drug compound.\n"
        f"2. Pharmacokinetic variance, dosage timing, or mild additive interaction between taken medications.\n\n"
        f"**Precaution / Warning Sign:**\n"
        f"If you develop skin swelling, difficulty breathing, or severe abdominal cramping, discontinue use and contact your healthcare provider immediately."
    )


def risk_score(symptoms: str, medicines: str) -> int:
    """
    Calculates emergency risk score percentage mapped to severity levels.
    """
    score = 10
    if not symptoms:
        symptoms = ""
    if not medicines:
        medicines = ""

    s_lower = symptoms.lower()
    m_lower = medicines.lower()

    # Emergency symptoms boost
    if any(k in s_lower for k in ["chest pain", "pressure in chest", "shortness of breath", "severe bleeding", "unconscious", "stroke"]):
        score += 80
    elif any(k in s_lower for k in ["fever", "dizziness", "vomiting", "headache", "rash"]):
        score += 35

    # High-risk drug combination boost
    if ("ibuprofen" in m_lower and "warfarin" in m_lower) or ("aspirin" in m_lower and "warfarin" in m_lower) or ("clopidogrel" in m_lower and "warfarin" in m_lower):
        score += 45
    elif "," in m_lower or "and" in m_lower:
        score += 15

    return min(100, max(10, score))
