from AI.services.disease_mapper import map_condition


def test_heart_disease():
    assert map_condition("Patient has heart disease") == ["heart_disease"]


def test_hepatitis_b():
    assert map_condition("I have hepatitis B") == ["hepatitis_b"]


def test_epilepsy():
    assert map_condition("Patient has epilepsy") == ["epilepsy"]


def test_fever():
    assert map_condition("I have a fever") == ["fever"]


def test_surgery():
    assert map_condition("I recently had surgery") == ["surgery"]


def test_pregnancy():
    assert map_condition("Patient is pregnant") == ["pregnancy"]


def test_tattoo():
    assert map_condition("I got a tattoo recently") == ["tattoo"]


def test_unknown_condition():
    assert map_condition("I have an unknown condition") == []


def test_empty_input():
    assert map_condition("") == []


def test_multiple_conditions():
    result = map_condition("I have fever and heart disease")

    assert "fever" in result
    assert "heart_disease" in result