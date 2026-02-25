import re
from typing import Dict, Tuple, List

REQUIRED_FIELDS = [
    "customer_name",
    "weight_kg",
    "pickup_location",
    "drop_location",
    "pickup_time_window",
]

DEFAULT_PATTERNS = {
    "customer_name": r"(?:name|customer)\s*[:\-]\s*(.+)",
    "weight_kg": r"(?:weight)\s*[:\-]\s*([\d\.]+)\s*(?:kg|kgs)?",
    "pickup_location": r"(?:pickup|from)\s*(?:location)?\s*[:\-]\s*(.+)",
    "drop_location": r"(?:drop|to|destination)\s*(?:location)?\s*[:\-]\s*(.+)",
    "pickup_time_window": r"(?:time|pickup time|schedule|when)\s*[:\-]\s*(.+)",
}

def extract_with_regex(text: str, patterns: Dict[str, str] | None = None) -> Tuple[Dict, List[str]]:
    patterns = patterns or DEFAULT_PATTERNS
    data: Dict[str, str] = {}

    for field, pat in patterns.items():
        m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip()
            val = re.sub(r"\s+$", "", val)
            data[field] = val

    missing = [f for f in REQUIRED_FIELDS if f not in data or not str(data[f]).strip()]
    return data, missing