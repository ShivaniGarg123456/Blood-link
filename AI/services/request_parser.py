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

    component: Literal["whole_blood", "rbc"] = "whole_blood"

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
# 4. Component Extraction
# ==========================================

def extract_component(text: str) -> Literal["whole_blood", "rbc"]:

    text = text.lower()

    rbc_patterns = [
        r"\brbc\b",
        r"\bred\s+blood\s+cells?\b",
        r"\bred\s+cell(s)?\b",
        r"\bpacked\s+red\s+cells?\b",
        r"\bpacked\s+rbc\b"
    ]

    for pattern in rbc_patterns:

        if re.search(pattern, text):

            return "rbc"

    whole_blood_patterns = [
        r"\bwhole\s+blood\b",
        r"\bwhole\s+blood\s+unit(s)?\b"
    ]

    for pattern in whole_blood_patterns:

        if re.search(pattern, text):

            return "whole_blood"

    # Default component
    return "whole_blood"


# ==========================================
# 5. Urgency Detection
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
        "abhi",
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
# 6. Hospital Extraction
# ==========================================

def extract_hospital(text: str) -> Optional[str]:

    text = text.lower().strip()

    hospital = None

    # Hospital after English markers

    patterns_after = [
        r"\bat\s+(.+)$",
        r"\bin\s+(.+)$"
    ]

    for pattern in patterns_after:

        match = re.search(pattern, text)

        if match:

            hospital = match.group(1).strip()

            break

    # Hospital before Hindi markers

    if hospital is None:

        patterns_before = [
            r"(.+?)\s+\bmein\b",
            r"(.+?)\s+\bme\b",
            r"(.+?)\s+\bpar\b"
        ]

        for pattern in patterns_before:

            matches = list(re.finditer(pattern, text))

            if matches:

                hospital = matches[-1].group(1).strip()

                break

    # Hospital name at end

    if hospital is None:

        hospital_patterns = [
            r"\b(?:hospital|hospitals)\b",
            r"\b(?:medical college)\b",
            r"\b(?:medical center|medical centre)\b",
            r"\b(?:clinic)\b",
            r"\b(?:aiims)\b"
        ]

        for pattern in hospital_patterns:

            matches = list(re.finditer(pattern, text))

            if matches:

                last_match = matches[-1]

                hospital = text[:last_match.end()].strip()

                break

    # Clean extracted hospital

    if hospital:

        hospital = hospital.strip(" .,!?")

        # Remove text before blood/component keywords

        hospital = re.sub(
            r".*\b(?:blood|khoon|rbc|red blood cells?|whole blood)\b\s*",
            "",
            hospital
        )

        cleanup_words = [
            "please",
            "urgently",
            "urgent",
            "immediately",
            "asap",
            "chahiye",
            "zarurat",
            "hai",
            "hain",
            "needed",
            "required",
            "need",
            "want",
            "mujhe",
            "bhejo",
            "madad",
            "turant",
            "soon",
            "priority"
        ]

        for word in cleanup_words:

            hospital = re.sub(
                rf"\b{re.escape(word)}\b",
                "",
                hospital
            )

        # Remove numbers

        hospital = re.sub(
            r"\b\d+\b",
            "",
            hospital
        )

        # Remove blood group

        hospital = re.sub(
            r"\b(?:a|b|ab|o)\s*[+-]\b",
            "",
            hospital
        )

        # Remove component names

        hospital = re.sub(
            r"\b(?:rbc|red blood cells?|whole blood)\b",
            "",
            hospital
        )

        # Normalize spaces

        hospital = re.sub(
            r"\s+",
            " ",
            hospital
        ).strip()

        hospital = hospital.strip(" .,!?")

        if hospital:

            return hospital

    return None


# ==========================================
# 7. Language Detection
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
        "jaldi",
        "par",
        "abhi"
    ]

    for keyword in hindi_keywords:

        pattern = r"\b" + re.escape(keyword) + r"\b"

        if re.search(pattern, text):

            return "hi"

    return "en"


# ==========================================
# 8. Main Request Parser
# ==========================================

def parse_blood_request(text: str) -> BloodRequestParseResult:

    text = text.strip()

    normalized_text = text.lower()

    blood_group = extract_blood_group(normalized_text)

    units = extract_units(normalized_text)

    urgency = extract_urgency(normalized_text)

    hospital = extract_hospital(normalized_text)

    component = extract_component(normalized_text)

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
        component=component,
        urgency=urgency,
        language=language,
        missing_fields=missing_fields
    )


# ==========================================
# 9. Testing
# ==========================================

if __name__ == "__main__":

    test_requests = [

        # English requests

        "Need 2 units B+ blood urgently at AIIMS Delhi",

        "Need 3 units O- blood immediately at Apollo Hospital",

        "Need blood urgently",

        "Need 1 unit AB- blood at Fortis Hospital",

        "Need 2 bags B- blood at Max Hospital",

        "Urgently need blood at Civil Hospital",

        "3 units A+ required in Fortis Hospital",

        # RBC requests

        "Need 2 units B+ RBC at AIIMS Delhi",

        "Need 3 units O- red blood cells at Apollo Hospital",

        "Need 2 units A+ packed red cells at Fortis Hospital",

        # Whole blood requests

        "Need 2 units B+ whole blood at AIIMS Delhi",

        "Need 3 units O- whole blood urgently at Apollo Hospital",

        # Hindi/Hinglish requests

        "Mujhe 2 units A+ khoon chahiye at AIIMS Delhi",

        "Mujhe 4 units O+ blood turant chahiye at Civil Hospital",

        "Mujhe A positive khoon chahiye",

        "Mujhe AB negative blood chahiye",

        "Mujhe 2 units B+ RBC AIIMS Delhi mein urgently chahiye",

        "B+ blood chahiye Max Hospital mein",

        "AIIMS Delhi mein B+ blood ki zarurat hai",

        "Apollo Hospital par O+ blood chahiye",

        # Missing information

        "Need B negative blood",

        "Need O positive blood urgently",

        "Need 2 units A plus blood",

        "Blood required at AIIMS Delhi"
    ]

    for i, request in enumerate(test_requests, start=1):

        print(f"\nTest Case {i}")
        print("=" * 50)

        print("Input:", request)

        result = parse_blood_request(request)

        print("Output:", result)

        print("\nJSON:")

        print(result.model_dump_json(indent=2))