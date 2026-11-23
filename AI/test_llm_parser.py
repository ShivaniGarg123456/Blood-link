import pytest

from AI.services.request_parser import (
    parse_blood_request,
    extract_blood_group,
    extract_units,
    extract_urgency,
)

from AI.services.llm_parser import (
    merge_parser_results,
    fallback_parser,
)


# ============================================================
# 1. BLOOD GROUP EXTRACTION TESTS
# ============================================================

@pytest.mark.parametrize("user_text, expected", [
    ("Need O+ blood", "O+"),
    ("Need O negative blood", "O-"),
    ("Need A positive blood", "A+"),
    ("Need A negative blood", "A-"),
    ("Need B+ blood", "B+"),
    ("Need B negative blood", "B-"),
    ("Need AB positive blood", "AB+"),
    ("Need AB negative blood", "AB-"),
])
def test_blood_group_extraction(user_text, expected):
    result = extract_blood_group(user_text)
    assert result == expected


# ============================================================
# 2. UNITS EXTRACTION TESTS
# ============================================================

@pytest.mark.parametrize("user_text, expected", [
    ("Need 2 units of O+ blood", 2),
    ("Need 5 bags of B- blood", 5),
    ("Need 3 units of AB+ blood", 3),
    ("Need 1 unit of A positive blood", 1),
])
def test_units_extraction(user_text, expected):
    result = extract_units(user_text)
    assert result == expected


# ============================================================
# 3. URGENCY EXTRACTION TESTS
# ============================================================

@pytest.mark.parametrize("user_text, expected", [
    ("Need blood urgently", "critical"),
    ("Need blood immediately", "critical"),
    ("Emergency, blood needed now", "critical"),
    ("Need blood as soon as possible", "high"),
    ("Need blood tomorrow", "normal"),
])
def test_urgency_extraction(user_text, expected):
    result = extract_urgency(user_text)
    assert result == expected


# ============================================================
# 4. COMPLETE REQUEST PARSING
# ============================================================

def test_complete_request_parsing():
    user_text = "Need 3 units O negative blood at Apollo Hospital"

    result = parse_blood_request(user_text)

    assert result.blood_group == "O-"
    assert result.units == 3
    assert result.hospital is not None
    assert result.urgency == "normal"
    assert result.language == "en"
    assert result.missing_fields == []


# ============================================================
# 5. HINDI REQUEST PARSING
# ============================================================

def test_hindi_request_parsing():
    user_text = "Mujhe 2 units B+ blood urgently chahiye"

    result = parse_blood_request(user_text)

    assert result.blood_group == "B+"
    assert result.units == 2
    assert result.urgency == "critical"
    assert result.language == "hi"


# ============================================================
# 6. MISSING FIELDS TEST
# ============================================================

def test_missing_fields():
    user_text = "Please arrange blood immediately"

    result = parse_blood_request(user_text)

    assert result.blood_group is None
    assert result.units is None
    assert result.hospital is None

    assert "blood_group" in result.missing_fields
    assert "units" in result.missing_fields
    assert "hospital" in result.missing_fields


# ============================================================
# 7. FALLBACK PARSER TEST
# ============================================================

def test_fallback_parser():
    user_text = "Need 2 units O+ blood at AIIMS Delhi"

    result = fallback_parser(user_text)

    assert result.blood_group == "O+"
    assert result.units == 2
    assert result.hospital is not None


# ============================================================
# 8. MERGE PARSER RESULTS TEST
# ============================================================

def test_merge_parser_results():
    rule_result = parse_blood_request(
        "Mujhe 2 units B+ blood urgently chahiye"
    )

    llm_result = parse_blood_request(
        "Need blood at AIIMS Delhi"
    )

    result = merge_parser_results(
        rule_result,
        llm_result
    )

    assert result.blood_group == "B+"
    assert result.units == 2
    assert result.hospital is not None
    assert result.urgency == "critical"
    assert result.language == "hi"


# ============================================================
# 9. RULE-BASED PARSER PRIORITY TEST
# ============================================================

def test_rule_based_priority():
    rule_result = parse_blood_request(
        "Need 2 units B+ blood urgently"
    )

    llm_result = parse_blood_request(
        "Need 5 units O- blood at AIIMS Delhi"
    )

    result = merge_parser_results(
        rule_result,
        llm_result
    )

    assert result.blood_group == "B+"
    assert result.units == 2
    assert result.urgency == "critical"


# ============================================================
# 10. MISSING FIELDS RECALCULATION TEST
# ============================================================

def test_missing_fields_recalculation():
    rule_result = parse_blood_request(
        "Need 2 units O+ blood"
    )

    llm_result = parse_blood_request(
        "Need blood at Fortis Hospital"
    )

    result = merge_parser_results(
        rule_result,
        llm_result
    )

    assert result.blood_group == "O+"
    assert result.units == 2
    assert result.hospital is not None
    assert result.missing_fields == []


# ============================================================
# 11. LANGUAGE PRESERVATION TEST
# ============================================================

def test_language_preservation():
    rule_result = parse_blood_request(
        "Mujhe 2 units O+ blood chahiye"
    )

    llm_result = parse_blood_request(
        "Need blood at Apollo Hospital"
    )

    result = merge_parser_results(
        rule_result,
        llm_result
    )

    assert result.language == "hi"


# ============================================================
# 12. EMPTY REQUEST TEST
# ============================================================

def test_empty_request():
    result = parse_blood_request("")

    assert result.blood_group is None
    assert result.units is None
    assert result.hospital is None

    assert "blood_group" in result.missing_fields
    assert "units" in result.missing_fields
    assert "hospital" in result.missing_fields


# ============================================================
# 13. HOSPITAL EXTRACTION EDGE CASES
# ============================================================

@pytest.mark.parametrize("user_text, expected", [
    ("Need blood at AIIMS Delhi", "AIIMS Delhi"),
    ("Need 2 units B+ blood at Apollo Hospital", "Apollo Hospital"),
    ("Need blood at Fortis Hospital", "Fortis Hospital"),
])
def test_hospital_extraction_edge_cases(user_text, expected):
    result = parse_blood_request(user_text)

    assert result.hospital is not None
    assert expected.lower() in result.hospital.lower()


# ============================================================
# 14. MISSING BLOOD GROUP
# ============================================================

def test_missing_blood_group():
    result = parse_blood_request(
        "Need 2 units blood at AIIMS Delhi"
    )

    assert result.blood_group is None
    assert result.units == 2
    assert result.hospital is not None
    assert "blood_group" in result.missing_fields


# ============================================================
# 15. MISSING UNITS
# ============================================================

def test_missing_units():
    result = parse_blood_request(
        "Need O+ blood at Apollo Hospital"
    )

    assert result.blood_group == "O+"
    assert result.units is None
    assert "units" in result.missing_fields


# ============================================================
# 16. INVALID UNITS
# ============================================================

@pytest.mark.parametrize("user_text", [
    "Need 0 units O+ blood",
    "Need 15 units B+ blood",
    "Need 100 bags O- blood",
])
def test_invalid_units(user_text):
    result = parse_blood_request(user_text)

    assert result.units is None
    assert "units" in result.missing_fields


# ============================================================
# 17. COMPONENT EXTRACTION
# ============================================================

@pytest.mark.parametrize("user_text, expected", [
    ("Need RBC at AIIMS Delhi", "rbc"),
    ("Need red blood cells at Apollo Hospital", "rbc"),
    ("Need packed red cells at Fortis Hospital", "rbc"),
    ("Need whole blood at AIIMS Delhi", "whole_blood"),
    ("Need 2 units O+ blood", "whole_blood"),
])
def test_component_extraction(user_text, expected):
    result = parse_blood_request(user_text)

    assert result.component == expected


# ============================================================
# 18. HINDI LOCATION EXTRACTION
# ============================================================

def test_hindi_location_extraction():
    result = parse_blood_request(
        "AIIMS Delhi mein B+ blood ki zarurat hai"
    )

    assert result.blood_group == "B+"
    assert result.hospital is not None

    # Case-insensitive comparison
    assert "aiims delhi" in result.hospital.lower()


# ============================================================
# 19. NO HOSPITAL PROVIDED
# ============================================================

def test_no_hospital_provided():
    result = parse_blood_request(
        "Need 2 units O+ blood urgently"
    )

    assert result.blood_group == "O+"
    assert result.units == 2
    assert result.hospital is None
    assert "hospital" in result.missing_fields