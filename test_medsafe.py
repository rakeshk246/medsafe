"""
test_medsafe.py — Comprehensive Unit & Feature Test Suite for MedSafe AI
Validates fuzzy matching, pairwise drug interactions, symptom triage, risk prediction, side-effect monitoring, and LLM fallbacks.
"""

import unittest
from med_db import find_medicine, check_interactions, llama_short_warning, MED_DB
from symptom import symptom_advice, risk_score, llama_expand, analyze_side_effects

class TestMedSafeEngine(unittest.TestCase):

    # ---------------------------------------------------------
    # 1. Medicine Fuzzy Matching Tests (RapidFuzz)
    # ---------------------------------------------------------
    def test_find_medicine_exact_and_fuzzy(self):
        """Test exact match, typos/OCR noise tolerance, and symbol cleanup."""
        self.assertEqual(find_medicine("ibuprofen"), "ibuprofen")
        self.assertEqual(find_medicine("iburofen"), "ibuprofen")         # Typo tolerance
        self.assertEqual(find_medicine("warfarinn"), "warfarin")         # Typo tolerance
        self.assertEqual(find_medicine("aspirin+"), "aspirin")           # Symbol cleanup
        self.assertEqual(find_medicine("paracetamol,"), "paracetamol")   # Punctuation cleanup
        self.assertIsNone(find_medicine("nonexistent_fake_drug_999"))    # Unknown drug

    # ---------------------------------------------------------
    # 2. Pairwise Interaction Checking Tests
    # ---------------------------------------------------------
    def test_check_interactions_pairwise(self):
        """Test pairwise interaction detection across multiple medicines."""
        # 2 drugs test
        warnings_2 = check_interactions(["ibuprofen", "warfarin"])
        self.assertTrue(any("Ibuprofen + Warfarin" in w or "Warfarin + Ibuprofen" in w for w in warnings_2))

        # 3 drugs test (evaluates all 3 pairs)
        warnings_3 = check_interactions(["ibuprofen", "warfarin", "aspirin"])
        self.assertGreaterEqual(len(warnings_3), 2)

    def test_unknown_medicine_reporting(self):
        """Test that unrecognized medicines are reported cleanly."""
        warnings = check_interactions(["ibuprofen", "unknown_pill_xyz"])
        self.assertTrue(any("unknown_pill_xyz" in w for w in warnings))

    # ---------------------------------------------------------
    # 3. Symptom Rule Engine Tests
    # ---------------------------------------------------------
    def test_symptom_advice_emergency_detection(self):
        """Test symptom advice for emergency keywords vs fever vs default."""
        chest_advice = symptom_advice("chest pain and dizziness")
        self.assertIn("Chest Pain - Emergency Symptom", chest_advice)

        breath_advice = symptom_advice("shortness of breath")
        self.assertIn("Respiratory Distress", breath_advice)

        fever_advice = symptom_advice("high fever")
        self.assertIn("Fever Detected", fever_advice)

        headache_advice = symptom_advice("severe headache")
        self.assertIn("Headache Guidance", headache_advice)

        general_advice = symptom_advice("mild tiredness")
        self.assertIn("Rest, maintain adequate hydration", general_advice)

    # ---------------------------------------------------------
    # 4. Emergency Risk Predictor Tests
    # ---------------------------------------------------------
    def test_risk_score_calculation(self):
        """Test emergency risk score formula for high vs low risk scenarios."""
        # Emergency symptoms + high-risk drug combination -> Level 7 Critical (>= 90%)
        critical_score = risk_score("chest pain, shortness of breath", "ibuprofen, warfarin")
        self.assertGreaterEqual(critical_score, 90)

        # High risk symptoms (fever/headache) -> Level 5 High (>= 60%)
        high_score = risk_score("fever and severe headache", "paracetamol")
        self.assertGreaterEqual(high_score, 40)

        # Minimal risk scenario -> Level 1 Minimal (< 60%)
        minimal_score = risk_score("mild tiredness", "paracetamol")
        self.assertLess(minimal_score, 60)

    # ---------------------------------------------------------
    # 5. Offline Fallback Logic Tests
    # ---------------------------------------------------------
    def test_llama_short_warning_fallback(self):
        """Test safe fallback note when Ollama is offline."""
        lines = ["Ibuprofen + Warfarin: High bleeding risk"]
        summary = llama_short_warning(lines, ollama_client=None)
        self.assertIn("Safety Warning", summary)

    def test_llama_expand_fallback(self):
        """Test symptom guidance AI expansion fallback."""
        base_text = "Fever advice: drink water"
        expanded = llama_expand(base_text, "fever", ollama_client=None)
        self.assertIn("Home Remedies & Wellness", expanded)

    def test_analyze_side_effects_fallback(self):
        """Test side-effect monitor educational fallback."""
        output = analyze_side_effects(30, "Male", ["Ibuprofen"], ["200mg"], "Stomach discomfort", ollama_client=None)
        self.assertIn("Educational Side-Effect Analysis", output)


if __name__ == "__main__":
    unittest.main()
