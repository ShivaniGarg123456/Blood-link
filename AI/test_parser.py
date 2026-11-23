from AI.services.request_parser import parse_blood_request


def test_english_request():
    result = parse_blood_request(
        "Need 2 units B+ blood urgently at AIIMS Delhi"
    )

    assert result.blood_group == "B+"
    assert result.units == 2
    assert result.hospital is not None


def test_emergency_request():
    result = parse_blood_request(
        "Need 3 units O- blood immediately at Apollo Hospital"
    )

    assert result.blood_group == "O-"
    assert result.units == 3
    assert result.urgency == "critical"


def test_missing_information():
    result = parse_blood_request(
        "Need blood urgently"
    )

    assert result.blood_group is None
    assert result.units is None
    assert result.missing_fields


def test_hindi_request():
    result = parse_blood_request(
        "Mujhe 2 units A+ khoon chahiye AIIMS Delhi mein"
    )

    assert result.blood_group == "A+"
    assert result.units == 2
    assert result.language == "hi"