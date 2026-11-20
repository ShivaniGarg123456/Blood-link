from datetime import date, timedelta

# Fixed rules. Values are typical figures for India and are kept here
# so the team can change them easily. Check against official guidelines.

MIN_AGE = 18
MAX_AGE = 65
MIN_WEIGHT_KG = 45

# Days to wait between donations
DONATION_GAP_DAYS = {"male": 90, "female": 120}

# Conditions that stop a person from donating
PERMANENT_CONDITIONS = {
    "hiv": "HIV infection",
    "hepatitis_b": "hepatitis B",
    "hepatitis_c": "hepatitis C",
    "heart_disease": "heart disease",
    "cancer": "cancer",
    "epilepsy": "epilepsy",
}

# Conditions that only delay donation: name -> (days to wait, label)
TEMPORARY_CONDITIONS = {
    "fever": (14, "a recent fever"),
    "surgery": (180, "recent surgery"),
    "pregnancy": (180, "pregnancy"),
    "breastfeeding": (180, "breastfeeding"),
    "tattoo": (180, "a recent tattoo"),
}


def check_eligibility(age, weight_kg, sex, last_donation_date=None,
                      conditions=None, today=None):
    """Return {"status", "reason", "eligible_after"}.

    status is one of: "eligible", "not_eligible", "eligible_after".
    The hospital still does the final medical check.
    """
    today = today or date.today()
    conditions = [c.strip().lower() for c in (conditions or [])]
    sex = sex.strip().lower()

    if age < MIN_AGE:
        return _result("not_eligible",
                       f"You are under {MIN_AGE}, so you can't donate yet.")
    if age > MAX_AGE:
        return _result("not_eligible",
                       f"Donors must be {MAX_AGE} or younger.")
    if weight_kg < MIN_WEIGHT_KG:
        return _result("not_eligible",
                       f"Donors must weigh at least {MIN_WEIGHT_KG} kg.")

    for c in conditions:
        if c in PERMANENT_CONDITIONS:
                        return _result("not_eligible",
                           "You can't donate because of a medical condition. "
                           "Please talk to a doctor.")
    # Find the latest date the donor becomes eligible again
    wait_until = None
    reason = ""

    if last_donation_date:
        gap = DONATION_GAP_DAYS.get(sex, 120)
        d = last_donation_date + timedelta(days=gap)
        if d > today:
            wait_until, reason = d, "You donated recently."

    for c in conditions:
        if c in TEMPORARY_CONDITIONS:
            days, label = TEMPORARY_CONDITIONS[c]
            d = today + timedelta(days=days)
            if wait_until is None or d > wait_until:
                wait_until, reason = d, f"You need to wait because of {label}."

    if wait_until:
        return _result("eligible_after", reason, wait_until)

    return _result("eligible", "You can donate. The hospital will do the final check.")


def _result(status, reason, eligible_after=None):
    return {
        "status": status,
        "reason": reason,
        "eligible_after": eligible_after.isoformat() if eligible_after else None,
    }