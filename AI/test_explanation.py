from AI.services.explanation import explain_eligibility, format_date


def test_eligible_explanation():
    result = {
        "status": "eligible",
        "reason": "You can donate.",
        "eligible_after": None
    }

    response = explain_eligibility(result)

    assert response["status"] == "eligible"
    assert "hospital" in response["explanation"].lower()


def test_not_eligible_explanation():
    result = {
        "status": "not_eligible",
        "reason": "Medical condition",
        "eligible_after": None
    }

    response = explain_eligibility(result)

    assert response["status"] == "not_eligible"
    assert "hospital" in response["explanation"].lower()


def test_waiting_period_explanation():
    result = {
        "status": "eligible_after",
        "reason": "You donated recently.",
        "eligible_after": "2027-01-15"
    }

    response = explain_eligibility(result)

    assert response["status"] == "eligible_after"
    assert "15 January 2027" in response["explanation"]


def test_waiting_period_without_date():
    result = {
        "status": "eligible_after",
        "reason": "Waiting period",
        "eligible_after": None
    }

    response = explain_eligibility(result)

    assert "waiting-period" in response["explanation"]


def test_unknown_status():
    result = {
        "status": "unknown",
        "reason": "Unknown",
        "eligible_after": None
    }

    response = explain_eligibility(result)

    assert "could not be recognized" in response["explanation"]


def test_invalid_input():
    response = explain_eligibility("invalid")

    assert response["status"] == "unknown"


def test_format_date():
    assert format_date("2027-01-15") == "15 January 2027"


def test_invalid_date():
    assert format_date("invalid-date") == "invalid-date"