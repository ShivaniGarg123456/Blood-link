import re

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ==========================================
# 1. Structured Output Schema
# ==========================================

class BloodRequestParseResult(BaseModel):

    blood_group: Optional[
        Literal["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
    ] = None

    units: Optional[int] = Field(default=None, ge=1, le=10)

    hospital: Optional[str] = None

    urgency: Literal["critical", "high", "normal"] = "normal"

    language: Literal["hi", "en"]

    missing_fields: list[str] = Field(default_factory=list)


# ==========================================
# 2. Blood Group Extraction
# ==========================================

def extract_blood_group(text: str) -> Optional[str]:

    text = text.lower()

    blood_group_patterns = {

        "AB+": [
            r"\bab\s*\+",
            r"\bab\s+positive\b",
            r"\bab\s+pos\b",
            r"\bab\s+plus\b"
        ],

        "AB-": [
            r"\bab\s*-",
            r"\bab\s+negative\b",
            r"\bab\s+neg\b",
            r"\bab\s+minus\b"
        ],

        "A+": [
            r"\ba\s*\+",
            r"\ba\s+positive\b",
            r"\ba\s+pos\b",
            r"\ba\s+plus\b"
        ],

        "A-": [
            r"\ba\s*-",
            r"\ba\s+negative\b",
            r"\ba\s+neg\b",
            r"\ba\s+minus\b"
        ],

        "B+": [
            r"\bb\s*\+",
            r"\bb\s+positive\b",
            r"\bb\s+pos\b",
            r"\bb\s+plus\b"
        ],

        "B-": [
            r"\bb\s*-",
            r"\bb\s+negative\b",
            r"\bb\s+neg\b",
            r"\bb\s+minus\b"
        ],

        "O+": [
            r"\bo\s*\+",
            r"\bo\s+positive\b",
            r"\bo\s+pos\b",
            r"\bo\s+plus\b"
        ],

        "O-": [
            r"\bo\s*-",
            r"\bo\s+negative\b",
            r"\bo\s+neg\b",
            r"\bo\s+minus\b"
        ]
    }

    for group, patterns in blood_group_patterns.items():

        for pattern in patterns:

            if re.search(pattern, text):

                return group

    return None


# ==========================================
# 3. Units Extraction
# ==========================================

def extract_units(text: str) -> Optional[int]:

    patterns = [
        r"\b(\d+)\s*units?\b",
        r"\b(\d+)\s*bags?\b",
        r"\b(\d+)\s*unit\b",
        r"\b(\d+)\s*bag\b"
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:

            units = int(match.group(1))

            if 1 <= units <= 10:

                return units

    return None


# ==========================================
# 4. Urgency Detection
# ==========================================

def extract_urgency(text: str) -> str:

    text = text.lower()

    critical_keywords = [
        "emergency",
        "urgent",
        "critical",
        "immediately",
        "asap",
        "turant",
        "emergency hai"
    ]

    high_keywords = [
        "soon",
        "high priority",
        "jaldi",
        "priority"
    ]

    if any(keyword in text for keyword in critical_keywords):

        return "critical"

    if any(keyword in text for keyword in high_keywords):

        return "high"

    return "normal"


# ==========================================
# 5. Hospital Extraction
# ==========================================

def extract_hospital(text: str) -> Optional[str]:

    text = text.lower()

    patterns = [
        r"\bat\s+(.+)",
        r"\bin\s+(.+)",
        r"\bmein\s+(.+)",
        r"\bme\s+(.+)",
        r"\bpar\s+(.+)"
    ]

    for pattern in patterns:

        match = re.search(pattern, text)

        if match:

            hospital = match.group(1).strip()

            hospital = re.sub(
                r"\b(please|urgently|urgent|immediately|chahiye|hai|blood)\b",
                "",
                hospital
            ).strip()

            if hospital:

                return hospital

    return None


# ==========================================
# 6. Language Detection
# ==========================================

def detect_language(text: str) -> Literal["hi", "en"]:

    text = text.lower()

    hindi_keywords = [
        "chahiye",
        "zarurat",
        "khoon",
        "mujhe",
        "turant",
        "mein",
        "hain",
        "hai",
        "bhejo",
        "madad",
        "jaldi"
    ]

    for keyword in hindi_keywords:

        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(pattern, text):

            return "hi"

    return "en"


# ==========================================
# 7. Main Request Parser
# ==========================================

def parse_blood_request(text: str) -> BloodRequestParseResult:

    text = text.strip()

    normalized_text = text.lower()

    blood_group = extract_blood_group(normalized_text)

    units = extract_units(normalized_text)

    urgency = extract_urgency(normalized_text)

    hospital = extract_hospital(normalized_text)

    language = detect_language(normalized_text)

    # Missing information detection

    missing_fields = []

    if blood_group is None:

        missing_fields.append("blood_group")

    if units is None:

        missing_fields.append("units")

    if hospital is None:

        missing_fields.append("hospital")

    # Structured response

    return BloodRequestParseResult(

        blood_group=blood_group,

        units=units,

        hospital=hospital,

        urgency=urgency,

        language=language,

        missing_fields=missing_fields
    )


# ==========================================
# 8. Testing
# ==========================================

if __name__ == "__main__":

    test_requests = [

        "Need 2 units B+ blood urgently at AIIMS Delhi",

        "Need 3 units O- blood immediately at Apollo Hospital",

        "Need blood urgently",

        "Mujhe 2 units A+ khoon chahiye at AIIMS Delhi",

        "Need 1 unit AB- blood at Fortis Hospital",

        "Mujhe 4 units O+ blood turant chahiye at Civil Hospital",

        "Need 2 bags B- blood at Max Hospital",

        "Mujhe A positive khoon chahiye",

        "Need B negative blood",

        "Need O positive blood urgently",

        "Mujhe AB negative blood chahiye",

        "Need 2 units A plus blood"
    ]

    for i, request in enumerate(test_requests, start=1):

        print(f"\nTest Case {i}")
        print("=" * 50)

        print("Input:", request)

        result = parse_blood_request(request)

        print("Output:", result)

        print("\nJSON:")

        print(result.model_dump_json(indent=2))