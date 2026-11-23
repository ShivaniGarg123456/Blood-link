import re
from difflib import SequenceMatcher


# Words that do not contribute much to request identity
STOP_WORDS = {
    "need",
    "required",
    "requirement",
    "request",
    "urgent",
    "urgently",
    "immediately",
    "please",
    "for",
    "at",
    "in",
    "the",
    "of",
    "a",
    "an",
    "blood",
    "units",
    "unit",
}


NUMBER_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
}


def normalize_text(text: str) -> str:
    """Normalize text before comparison."""

    if not isinstance(text, str):
        return ""

    text = text.lower().strip()

    replacements = {
        "b positive": "b+",
        "b negative": "b-",
        "a positive": "a+",
        "a negative": "a-",
        "o positive": "o+",
        "o negative": "o-",
        "ab positive": "ab+",
        "ab negative": "ab-",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Convert number words to digits
    for word, number in NUMBER_WORDS.items():
        text = re.sub(r"\b" + word + r"\b", number, text)

    # Remove punctuation
    text = re.sub(r"[^\w\s+]", " ", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_tokens(text: str) -> set:
    """Return meaningful tokens from normalized text."""

    normalized = normalize_text(text)

    return {
        word
        for word in normalized.split()
        if word not in STOP_WORDS
    }


def calculate_similarity(request1: str, request2: str) -> float:
    """
    Calculate similarity using character and token overlap.

    Returns a score between 0 and 1.
    """

    text1 = normalize_text(request1)
    text2 = normalize_text(request2)

    if not text1 or not text2:
        return 0.0

    # Identical normalized requests should have 100% similarity
    if text1 == text2:
        return 1.0

    # Character-level similarity
    sequence_score = SequenceMatcher(
        None,
        text1,
        text2
    ).ratio()

    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)

    # Token-level similarity
    if tokens1 or tokens2:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        token_score = len(intersection) / len(union)
    else:
        token_score = 0.0

    # Combine both similarity scores
    similarity = (
        0.4 * sequence_score
        + 0.6 * token_score
    )

    return similarity


def detect_duplicate(
    request1: str,
    request2: str,
    threshold: float = 0.60
) -> dict:
    """
    Flag potentially similar requests for review.

    Similarity does not confirm a duplicate.
    The system does not reject requests automatically.
    """

    similarity = calculate_similarity(
        request1,
        request2
    )

    is_similar = similarity >= threshold

    return {
        "is_similar": is_similar,
        "similarity_score": round(similarity, 2),
        "review_required": is_similar,
    }


if __name__ == "__main__":

    test_requests = [
        (
            "Need 2 units of B positive blood at AIIMS Delhi urgently",
            "Urgent requirement of two units B+ blood at AIIMS Delhi"
        ),
        (
            "Need 3 units O negative blood at Apollo Hospital",
            "Need 2 units B positive blood at AIIMS Delhi"
        ),
        (
            "Need blood urgently",
            "Need blood urgently"
        ),
    ]

    for request1, request2 in test_requests:

        result = detect_duplicate(
            request1,
            request2
        )

        print("\nRequest 1:", request1)
        print("Request 2:", request2)
        print("Result:", result)