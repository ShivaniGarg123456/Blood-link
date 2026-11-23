import re


# Backend-compatible disease categories
PERMANENT_CONDITIONS = {
    "hiv",
    "hepatitis_b",
    "hepatitis_c",
    "heart_disease",
    "cancer",
    "epilepsy",
}

TEMPORARY_CONDITIONS = {
    "fever",
    "surgery",
    "pregnancy",
    "breastfeeding",
    "tattoo",
}

ALL_CONDITIONS = PERMANENT_CONDITIONS | TEMPORARY_CONDITIONS


# Common text variations mapped to backend categories
DISEASE_ALIASES = {
    "hiv": [
        "hiv",
        "hiv infection",
    ],
    "hepatitis_b": [
        "hepatitis b",
        "hep b",
        "hbv",
    ],
    "hepatitis_c": [
        "hepatitis c",
        "hep c",
        "hcv",
    ],
    "heart_disease": [
        "heart disease",
        "heart condition",
        "heart problem",
        "cardiac disease",
    ],
    "cancer": [
        "cancer",
        "tumour",
        "tumor",
        "malignancy",
    ],
    "epilepsy": [
        "epilepsy",
        "epileptic",
        "seizure disorder",
    ],
    "fever": [
        "fever",
        "high temperature",
    ],
    "surgery": [
        "surgery",
        "operation",
        "surgical procedure",
    ],
    "pregnancy": [
        "pregnancy",
        "pregnant",
    ],
    "breastfeeding": [
        "breastfeeding",
        "breast feeding",
        "nursing mother",
    ],
    "tattoo": [
        "tattoo",
        "tattooing",
    ],
}


def normalize_text(text: str) -> str:
    """Normalize input text for matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def map_condition(text: str) -> list[str]:
    """
    Map free-text condition descriptions to backend categories.

    This function only identifies text categories.
    It does not make medical or donor eligibility decisions.
    """

    if not text or not isinstance(text, str):
        return []

    normalized_text = normalize_text(text)

    matched_conditions = []

    for category, aliases in DISEASE_ALIASES.items():
        for alias in aliases:

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, normalized_text):
                matched_conditions.append(category)
                break

    return list(dict.fromkeys(matched_conditions))


if __name__ == "__main__":

    test_inputs = [
        "I have dengue fever",
        "Patient has heart disease",
        "I recently had surgery",
        "Patient is pregnant",
        "I have hepatitis B",
        "I have epilepsy",
        "I got a tattoo recently",
        "I have an unknown condition",
    ]

    for text in test_inputs:
        result = map_condition(text)

        print(f"\nInput: {text}")
        print(f"Mapped conditions: {result}")