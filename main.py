"""
main.py — MedSafe AI (Intelligent Medicine Safety Assistant)
Upgraded with robust OCR fallback, configurable Tesseract path, unique Streamlit keys, empty default inputs, and system status indicators.
"""

import os
import json
import shutil
import streamlit as st
from PIL import Image
import pytesseract
from ollama import Client

# Local module imports
from med_db import MED_DB, find_medicine, check_interactions, llama_short_warning
from symptom import symptom_advice, llama_expand, analyze_side_effects, risk_score

# ---------------------------------------------------------
# Dynamic Tesseract OCR Configuration
# ---------------------------------------------------------
TESSERACT_ENV_PATH = os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

if shutil.which("tesseract"):
    TESSERACT_STATUS = True
elif os.path.exists(TESSERACT_ENV_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_ENV_PATH
    TESSERACT_STATUS = True
else:
    TESSERACT_STATUS = False

# ---------------------------------------------------------
# Safe Ollama Client Initialization
# ---------------------------------------------------------
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "LLaMA3")
try:
    ollama = Client()
    # Test ping connection
    OLLAMA_STATUS = True
except Exception:
    ollama = None
    OLLAMA_STATUS = False

# ---------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------
st.set_page_config(page_title="MedSafe AI", layout="wide", page_icon="🏥")
st.title("MedSafe AI - Intelligent Medicine Safety Assistant")

# Sidebar System Status Indicator
with st.sidebar:
    st.header("⚙️ System Status")
    if TESSERACT_STATUS:
        st.success("✅ Tesseract OCR: Active")
    else:
        st.warning("⚠️ Tesseract OCR: Not Found (Install Tesseract-OCR)")
        
    if OLLAMA_STATUS:
        st.success(f"✅ Ollama AI ({OLLAMA_MODEL}): Connected")
    else:
        st.info("💡 Ollama AI: Offline (Using Rule-Based Engine)")


# ---------------------------------------------------------
# Helper: Prescription OCR with Rule-Based Fallback
# ---------------------------------------------------------
def extract_medicines_with_salts(img):
    """
    Extracts raw text via Tesseract OCR and parses JSON via Ollama or falls back to RapidFuzz matching.
    """
    try:
        text = pytesseract.image_to_string(img)
    except Exception as e:
        return [], f"OCR Execution Error: {str(e)}"

    if not text.strip():
        return [], "No readable text detected in prescription image."

    prompt = f"""
You are a strict JSON generator.

Extract medicines and their active drug/salt from the prescription.

Rules:
- Output ONLY JSON
- No markdown
- No explanation
- Double quotes only
- If drug unknown, use null

Text:
{text}
"""
    data = []
    if ollama is not None:
        try:
            response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
            raw = response["response"].strip()
            if raw.startswith("```"):
                raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
        except Exception:
            data = []

    # Rule-based fallback parsing if LLM JSON is empty
    if not data:
        lines = text.split("\n")
        detected_items = []
        for line in lines:
            for word in line.split():
                clean_word = "".join(filter(str.isalnum, word))
                matched_key = find_medicine(clean_word, score_cutoff=85.0)
                if matched_key:
                    med_info = MED_DB[matched_key]
                    item = {"medicine": med_info["name"], "drug": med_info["drug_salt"]}
                    if item not in detected_items:
                        detected_items.append(item)
        data = detected_items

    return data, text


# ---------------------------------------------------------
# 5 Navigation Tabs Architecture
# ---------------------------------------------------------
tabs = st.tabs([
    "Medicine Interaction Checker",
    "Prescription OCR",
    "Symptom & Doubt Solver",
    "Side-Effect Monitor",
    "Emergency Risk Predictor"
])

# ---------------------------------------------------------
# TAB 0: Medicine Interaction Checker
# ---------------------------------------------------------
with tabs[0]:
    st.header("Medicine Interaction Checker")

    meds = st.text_input("Enter medicines (comma-separated):", "", placeholder="e.g. ibuprofen, warfarin, aspirin", key="input_inter_meds")

    if st.button("Check Interactions", key="btn_check_inter"):
        if not meds.strip():
            st.warning("Please enter at least one medicine name to evaluate.")
        else:
            med_list = [m.strip() for m in meds.split(",") if m.strip()]
            inter = check_interactions(med_list)

            if inter:
                st.warning("\n\n".join(inter))
                ai_note = llama_short_warning(inter, ollama_client=ollama, model_name=OLLAMA_MODEL)
                st.info(f"💡 **AI Safety Note:** {ai_note}")
            else:
                st.success("✅ No critical drug interaction warnings detected for entered medicines in database.")

# ---------------------------------------------------------
# TAB 1: Prescription OCR
# ---------------------------------------------------------
with tabs[1]:
    st.header("Extract Medicines From Prescription Image")

    file = st.file_uploader("Upload prescription image", type=["jpg", "jpeg", "png"], key="uploader_ocr")

    if file:
        img = Image.open(file)
        st.image(img, caption="Uploaded Prescription", width=400)

        if st.button("Run Prescription OCR", key="btn_run_ocr"):
            with st.spinner("Extracting prescription text and matching drugs..."):
                extracted, raw_text = extract_medicines_with_salts(img)
                st.session_state["ocr_extracted"] = extracted
                st.session_state["ocr_raw"] = raw_text

        if "ocr_extracted" in st.session_state:
            st.subheader("Detected Medicines & Drugs")
            extracted = st.session_state["ocr_extracted"]
            if extracted:
                for item in extracted:
                    st.write(
                        f"- **{item.get('medicine', 'Unknown')}** "
                        f"-> _{item.get('drug', 'Not specified')}_"
                    )
            else:
                st.info("No specific medicine matches extracted from prescription.")

        if "ocr_raw" in st.session_state:
            with st.expander("Raw OCR Text"):
                st.code(st.session_state["ocr_raw"])

# ---------------------------------------------------------
# TAB 2: Symptom & Doubt Solver
# ---------------------------------------------------------
with tabs[2]:
    st.header("AI Health Assistant")

    query = st.text_area("Describe your symptom:", placeholder="e.g. chest pain, fever, severe headache", key="input_symptom_text")

    if st.button("Get Advice", key="btn_symptom_advice"):
        if not query.strip():
            st.warning("Please enter a description of your symptoms.")
        else:
            symptoms_list = [
                s.strip() for s in query.replace(" and ", ",").split(",") if s.strip()
            ]

            base_advices = []
            for symptom in symptoms_list:
                advice = symptom_advice(symptom)
                base_advices.append(f"**{symptom.title()}**:\n{advice}")

            base = "\n\n".join(base_advices)
            st.info("Basic Advice:\n\n" + base)

            detailed = llama_expand(base, query, ollama_client=ollama, model_name=OLLAMA_MODEL)
            st.success("AI Enhanced Advice:\n\n" + detailed)

# ---------------------------------------------------------
# TAB 3: Side-Effect Monitor
# ---------------------------------------------------------
with tabs[3]:
    st.header("Experience & Side-Effect Monitor")

    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Enter your age:", min_value=0, max_value=120, value=25, key="input_age")
        gender = st.selectbox("Select your gender:", ["Male", "Female", "Other"], key="input_gender")
    with col2:
        medicine_taken = st.text_input("Enter medicine(s) taken (comma-separated):", placeholder="e.g. Ibuprofen, Paracetamol", key="input_med_taken")
        dose_taken = st.text_input("Enter dose(s) taken (mg, comma-separated if multiple):", placeholder="e.g. 200mg", key="input_dose_taken")

    experience = st.text_area("Describe what you felt after taking the medicine(s):", placeholder="e.g. Stomach burning and dizziness 30 minutes after taking medicine", key="input_exp")

    if st.button("Analyze Experience", key="side_effect_analyze"):
        if not medicine_taken.strip() or not experience.strip():
            st.warning("Please enter both the medicines taken and a description of your experience.")
        else:
            med_list = [m.strip() for m in medicine_taken.split(",") if m.strip()]
            dose_list = [d.strip() for d in dose_taken.split(",") if d.strip()]
            analysis = analyze_side_effects(age, gender, med_list, dose_list, experience, ollama_client=ollama, model_name=OLLAMA_MODEL)
            st.info(analysis)

# ---------------------------------------------------------
# TAB 4: Emergency Risk Predictor
# ---------------------------------------------------------
with tabs[4]:
    st.header("Emergency Risk Predictor")

    s = st.text_area("Describe symptoms:", placeholder="e.g. severe chest pain, shortness of breath", key="input_risk_symptom")
    m = st.text_input("Medicines taken:", "", placeholder="e.g. ibuprofen, warfarin", key="input_risk_meds")

    if st.button("Calculate Risk Score", key="emergency_risk"):
        if not s.strip() and not m.strip():
            st.warning("Please enter symptoms or medicines to evaluate emergency risk score.")
        else:
            score = risk_score(s, m)
            st.metric("Emergency Risk Score", f"{score}%")

            if score >= 90:
                level = "LEVEL 7 - CRITICAL RISK"
                msg = "Immediate medical emergency. Call emergency services (911/112) immediately."
                st.error(f"**{level}**\n\n{msg}")
            elif score >= 60:
                level = "LEVEL 5 - HIGH RISK"
                msg = "Strong warning signs present. Seek prompt medical evaluation."
                st.warning(f"**{level}**\n\n{msg}")
            else:
                level = "LEVEL 1 - MINIMAL RISK"
                msg = "No significant immediate emergency warning signs detected."
                st.success(f"**{level}**\n\n{msg}")
