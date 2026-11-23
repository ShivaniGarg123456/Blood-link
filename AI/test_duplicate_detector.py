import pytest

from AI.services.duplicate_detector import (
    normalize_text,
    calculate_similarity,
    detect_duplicate,
)


def test_identical_requests():
    result = detect_duplicate(
        "Need blood urgently",
        "Need blood urgently"
    )

    assert result["is_similar"] is True
    assert result["similarity_score"] == 1.0
    assert result["review_required"] is True


def test_similar_requests():
    result = detect_duplicate(
        "Need 2 units of B positive blood at AIIMS Delhi urgently",
        "Urgent requirement of two units B+ blood at AIIMS Delhi"
    )

    assert result["is_similar"] is True
    assert result["review_required"] is True
    assert result["similarity_score"] > 0.60


def test_different_requests():
    result = detect_duplicate(
        "Need 3 units O negative blood at Apollo Hospital",
        "Need 2 units B positive blood at AIIMS Delhi"
    )

    assert result["is_similar"] is False
    assert result["review_required"] is False


def test_empty_requests():
    result = detect_duplicate("", "")

    assert result["is_similar"] is False
    assert result["similarity_score"] == 0.0


def test_blood_group_normalization():
    normalized = normalize_text("B positive blood")

    assert "b+" in normalized


def test_number_word_normalization():
    normalized = normalize_text("Need two units")

    assert "2" in normalized


def test_similarity_score_range():
    score = calculate_similarity(
        "Need B positive blood",
        "Need B positive blood"
    )

    assert 0.0 <= score <= 1.0


def test_threshold():
    result = detect_duplicate(
        "Need blood at AIIMS Delhi",
        "Need blood at AIIMS Delhi",
        threshold=0.90
    )

    assert result["is_similar"] is True