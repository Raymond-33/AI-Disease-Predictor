"""
Medical Disease Predictor Engine
----------------------------------
A robust NLP-driven engine that:
1. Extracts symptoms from natural language queries
2. Matches symptoms to known diseases using fuzzy + cosine similarity
3. Returns top disease predictions with descriptions and diagnoses
"""

import json
import re
import logging
import math
from pathlib import Path
from fuzzywuzzy import fuzz
import nltk

# NLTK data is expected to be pre-downloaded; no network call at startup.
# If missing packages are found, they are silently skipped with a fallback.

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Safe tokenizer that handles punkt_tab OSError on older NLTK data paths
def _safe_tokenize(text: str) -> list[str]:
    """Tokenize text, falling back to simple split if punkt fails."""
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)
    except (LookupError, OSError):
        # Fallback: split on whitespace/punctuation
        return re.findall(r"[a-zA-Z']+", text)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Load Knowledge Base ────────────────────────────────────────────────────

DATA_PATH = Path(__file__).parent / "data" / "medical_knowledge.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    KNOWLEDGE_BASE = json.load(f)["diseases"]

# Build a flat master-symptom list  (symptom -> disease indices)
ALL_SYMPTOMS: list[str] = []
SYMPTOM_TO_DISEASES: dict[str, list[int]] = {}

for idx, disease in enumerate(KNOWLEDGE_BASE):
    for symptom in disease["symptoms"]:
        if symptom not in SYMPTOM_TO_DISEASES:
            SYMPTOM_TO_DISEASES[symptom] = []
            ALL_SYMPTOMS.append(symptom)
        SYMPTOM_TO_DISEASES[symptom].append(idx)

# ─── NLP Helpers ────────────────────────────────────────────────────────────

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()

# Medical negation phrases
NEGATION_PHRASES = [
    r"no\s+\w+",
    r"without\s+\w+",
    r"not\s+\w+",
    r"denies\s+\w+",
    r"absence\s+of\s+\w+",
]

# Synonym / abbreviation normalization map
SYNONYM_MAP = {
    "temp": "fever",
    "temperature": "fever",
    "running nose": "runny nose",
    "stuffy nose": "congestion",
    "blocked nose": "congestion",
    "throwing up": "vomiting",
    "threw up": "vomiting",
    "puking": "vomiting",
    "puke": "vomiting",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "tummy ache": "abdominal pain",
    "tummy pain": "abdominal pain",
    "abdominal ache": "abdominal pain",
    "bellyache": "abdominal pain",
    "loose stools": "diarrhea",
    "loose motions": "diarrhea",
    "loose motion": "diarrhea",
    "watery stool": "diarrhea",
    "cant breathe": "shortness of breath",
    "can't breathe": "shortness of breath",
    "difficulty breathing": "shortness of breath",
    "hard to breathe": "shortness of breath",
    "heart racing": "rapid heartbeat",
    "heart pounding": "rapid heartbeat",
    "palpitations": "irregular heartbeat",
    "fits": "seizures",
    "shivering": "chills",
    "sweats": "sweating",
    "night sweats": "sweating",
    "peeing a lot": "frequent urination",
    "pee often": "frequent urination",
    "frequent pee": "frequent urination",
    "skin rash": "rash",
    "spots": "rash",
    "blisters": "itchy blisters",
    "weight gain unexplained": "unexplained weight gain",
    "losing weight": "unexplained weight loss",
    "losing appetite": "loss of appetite",
    "no hunger": "loss of appetite",
    "no appetite": "loss of appetite",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "exhausted": "fatigue",
    "exhaustion": "fatigue",
    "lethargic": "fatigue",
    "lethargy": "fatigue",
    "weak": "weakness",
    "feeling weak": "weakness",
    "red eye": "red eyes",
    "pink eye": "red eyes",
    "burning in chest": "heartburn",
    "acid in throat": "acid reflux",
    "regurgitate": "regurgitation",
    "groin pain": "pain radiating to groin",
    "back ache": "back pain",
    "backache": "back pain",
    "sore muscles": "muscle pain",
    "muscle soreness": "muscle pain",
    "body pain": "body aches",
    "body sore": "body aches",
    "bones aching": "bone pain",
    "joints hurt": "joint pain",
    "joint hurt": "joint pain",
    "swollen joint": "joint swelling",
    "joint swelling morning": "joint stiffness in morning",
    "morning stiffness": "joint stiffness in morning",
    "no taste": "loss of taste",
    "cannot taste": "loss of taste",
    "no smell": "loss of smell",
    "cannot smell": "loss of smell",
    "sad": "persistent sadness",
    "sadness": "persistent sadness",
    "depressed": "persistent sadness",
    "hopeless": "hopelessness",
    "worried": "excessive worry",
    "excessive worrying": "excessive worry",
    "panic": "panic attacks",
    "butterfly rash": "butterfly rash on face",
    "malar rash": "butterfly rash on face",
    "sun sensitive": "photosensitivity",
    "sensitive to sun": "photosensitivity",
    "sensitive to light": "sensitivity to light",
    "light sensitivity": "sensitivity to light",
    "noise sensitivity": "sensitivity to sound",
    "sensitive to sound": "sensitivity to sound",
    "blurry vision": "blurred vision",
    "blurry eyes": "blurred vision",
    "diarreoha": "diarrhea",
    "stomach ulcer": "stomach ulcer",
    "mouth ulcer": "mouth ulcer",
    "low pressure": "hypotension",
    "low blood pressure": "hypotension",
    "thyroid": "thyroid problem",
    "eye cataracts": "cataracts",
}


def normalize_text(text: str) -> str:
    """Lowercase, remove special chars, apply synonym map."""
    text = text.lower().strip()
    # Replace multi-word synonyms first
    sorted_syns = sorted(SYNONYM_MAP.keys(), key=len, reverse=True)
    for syn in sorted_syns:
        if syn in text:
            text = text.replace(syn, SYNONYM_MAP[syn])
    return text


def remove_negations(text: str) -> str:
    """Remove negated phrases so they don't count as positive symptoms."""
    for pattern in NEGATION_PHRASES:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    return text


def extract_symptom_candidates(text: str) -> list[str]:
    """
    Extract candidate symptom tokens/bigrams/trigrams from the normalized query.
    Returns a deduplicated list.
    """
    text = normalize_text(text)
    text = remove_negations(text)

    candidates: list[str] = []

    # --- Add full normalized text as single candidate (captures multi-word)
    candidates.append(text)

    # --- Tokenize and add meaningful single tokens
    tokens = _safe_tokenize(text)

    meaningful = [
        LEMMATIZER.lemmatize(t) for t in tokens
        if t.isalpha() and t not in STOP_WORDS and len(t) > 2
    ]
    candidates.extend(meaningful)

    # --- Build bigrams and trigrams
    for i in range(len(meaningful) - 1):
        candidates.append(f"{meaningful[i]} {meaningful[i+1]}")
    for i in range(len(meaningful) - 2):
        candidates.append(f"{meaningful[i]} {meaningful[i+1]} {meaningful[i+2]}")

    # Chunk sentences by comma/and/or/with
    parts = re.split(r"[,;]|and|or|with|also|along|besides|plus", text)
    for part in parts:
        part = part.strip()
        if 2 < len(part) < 60:
            candidates.append(part)

    return list(dict.fromkeys(candidates))  # deduplicate preserving order


def match_symptoms(candidates: list[str], threshold: int = 85) -> list[str]:
    """
    For each candidate, find matching known symptoms using strict matching.
    Returns a deduplicated list of matched known symptoms.
    """
    matched: set[str] = set()
    
    # Words to ignore for substring matching if they are the ONLY match
    VAGUE_WORDS = {"pain", "ache", "feeling", "symptom", "problem", "issue", "severe", "mild"}

    for candidate in candidates:
        candidate_lower = candidate.lower().strip()
        if not candidate_lower:
            continue

        for known_sym in ALL_SYMPTOMS:
            known_lower = known_sym.lower()
            
            # 1. Exact match
            if candidate_lower == known_lower:
                matched.add(known_sym)
                continue
                
            # 2. Substring matching (only for multi-word or non-vague)
            if candidate_lower in known_lower and candidate_lower not in VAGUE_WORDS:
                # If candidate is a word in the known symptom
                if re.search(rf"\b{re.escape(candidate_lower)}\b", known_lower):
                    matched.add(known_sym)
                    continue

            # 3. Fuzzy ratio (Strict)
            # Use Token Sort Ratio which is better for mismatched word orders
            ratio = fuzz.token_sort_ratio(candidate_lower, known_lower)
            if ratio >= threshold:
                matched.add(known_sym)
            
            # Special case for "stomach pain" -> "abdominal pain" etc handled by SYNONYM_MAP
            # which happens BEFORE candidate extraction.
            
    return list(matched)


def _tf_idf_score(matched_symptoms: list[str], disease: dict, disease_idx: int) -> float:
    """
    Compute a TF-IDF-like relevance score for a disease given matched symptoms.
    """
    disease_symptoms = [s.lower() for s in disease["symptoms"]]
    n_total = len(KNOWLEDGE_BASE)

    score = 0.0
    for sym in matched_symptoms:
        sym_lower = sym.lower()
        if sym_lower in disease_symptoms:
            # TF: frequency within disease (normalized)
            tf = disease_symptoms.count(sym_lower) / len(disease_symptoms)
            # IDF: how disease-specific is this symptom
            diseases_with_sym = len(SYMPTOM_TO_DISEASES.get(sym_lower, []))
            idf = math.log((n_total + 1) / (diseases_with_sym + 1)) + 1.0
            score += tf * idf

    # Bonus: coverage ratio (what fraction of disease symptoms are matched)
    matched_set = {s.lower() for s in matched_symptoms}
    coverage = len(matched_set & set(disease_symptoms)) / max(len(disease_symptoms), 1)
    score += coverage * 2.0

    return score


def predict_diseases(query: str, top_n: int = 2) -> dict:
    """
    Main prediction function.
    
    Args:
        query:  Natural language description of symptoms
        top_n:  Maximum number of diseases to return
    """
    if not query or not query.strip():
        return {"error": "Please describe your symptoms."}

    # Step 1: Extract and match symptoms
    candidates = extract_symptom_candidates(query)
    matched_symptoms = match_symptoms(candidates)

    # Step 2: Score each disease
    scored = []
    for idx, disease in enumerate(KNOWLEDGE_BASE):
        # Check if 2 or more symptoms match for this disease
        disease_symptoms = [s.lower() for s in disease["symptoms"]]
        matched_set = {s.lower() for s in matched_symptoms}
        intersect = matched_set & set(disease_symptoms)
        
        if len(intersect) >= 2:
            s = _tf_idf_score(matched_symptoms, disease, idx)
            if s > 0:
                scored.append((s, disease))

    # Step 3: Sort by score, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    top_diseases = scored[:top_n]

    # Step 4: Compute confidence percentages
    total_score = sum(s for s, _ in top_diseases) or 1.0
    predictions = []
    for rank, (score, disease) in enumerate(top_diseases, start=1):
        confidence = round((score / total_score) * 100, 1)
        # Cap first-place at 92%, spread rest proportionally
        if rank == 1:
            confidence = min(confidence, 92.0)

        # Which matched symptoms triggered this disease
        triggering = [
            s for s in matched_symptoms
            if s.lower() in [x.lower() for x in disease["symptoms"]]
        ]

        predictions.append({
            "rank": rank,
            "disease": disease["name"],
            "category": disease["category"],
            "confidence": confidence,
            "severity": disease["severity"],
            "description": disease["description"],
            "diagnosis": disease["diagnosis"],
            "treatment": disease["treatment"],
            "when_to_see_doctor": disease["when_to_see_doctor"],
            "matching_symptoms": triggering,
        })

    # Fallback when no match found
    if not predictions:
        return {
            "query": query,
            "symptoms_detected": matched_symptoms,
            "predictions": [],
            "disclaimer": _disclaimer(),
            "message": (
                "I couldn't confidently match your description to a specific condition. "
                "Please describe your symptoms in more detail — for example, mention specific "
                "locations of pain, duration, or accompanying symptoms. Always consult a "
                "licensed medical professional for accurate diagnosis."
            )
        }

    return {
        "query": query,
        "symptoms_detected": matched_symptoms,
        "predictions": predictions,
        "disclaimer": _disclaimer(),
    }


def _disclaimer() -> str:
    return (
        "⚠️ IMPORTANT DISCLAIMER: This tool is for informational purposes only and does NOT "
        "constitute medical advice, diagnosis, or treatment. Always seek the advice of your "
        "physician or other qualified health provider with any questions you may have regarding "
        "a medical condition. Never disregard professional medical advice or delay in seeking "
        "it because of something you have read here. If you think you may have a medical "
        "emergency, call your doctor or emergency services immediately."
    )


if __name__ == "__main__":
    # Quick smoke-test
    test_queries = [
        "I have a high fever, severe headache and body aches since yesterday",
        "experiencing chest pain radiating to my left arm, sweating and shortness of breath",
        "I feel extremely tired, keep urinating frequently and feel thirsty all the time",
        "my joints are swollen and very stiff especially in the morning",
        "I can't stop worrying, my heart is racing and I'm having trouble sleeping",
    ]
    for q in test_queries:
        result = predict_diseases(q)
        print(f"\nQuery: {q}")
        if "predictions" in result and result["predictions"]:
            for p in result["predictions"]:
                print(f"  [{p['rank']}] {p['disease']} — {p['confidence']}% confidence")
        else:
            print("  No match found")
