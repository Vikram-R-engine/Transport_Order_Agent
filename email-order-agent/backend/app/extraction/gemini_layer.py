from typing import Dict, List, Tuple
from .regex_layer import REQUIRED_FIELDS

def _safe_float(x: str):
    try:
        return float(x)
    except Exception:
        return None

def extract_with_gemini(email_text: str, partial: Dict, api_key: str, model_name: str) -> Tuple[Dict, List[str]]:
    """
    Minimal Gemini hook. If GEMINI_API_KEY is empty, it simply returns partial.
    You can enable Gemini by putting GEMINI_API_KEY in backend/.env
    """
    if not api_key:
        merged = dict(partial)
        missing = [f for f in REQUIRED_FIELDS if f not in merged or not str(merged[f]).strip()]
        return merged, missing

    # Minimal real implementation (kept simple for client delivery)
    import json
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = f"""
Extract logistics order details from the email into JSON with keys:
customer_name, weight_kg, pickup_location, drop_location, pickup_time_window.
If unknown, set as empty string. Return ONLY JSON.

EMAIL:
{email_text}

PARTIAL (regex extracted):
{partial}
""".strip()

    resp = model.generate_content(prompt)
    text = resp.text.strip()
    ai_fields = json.loads(text)

    merged = {**partial, **{k: v for k, v in ai_fields.items() if str(v).strip()}}
    if "weight_kg" in merged and isinstance(merged["weight_kg"], str):
        w = _safe_float(merged["weight_kg"])
        if w is not None:
            merged["weight_kg"] = w

    missing = [f for f in REQUIRED_FIELDS if f not in merged or not str(merged[f]).strip()]
    return merged, missing