# Which donor blood groups can give to each receiver blood group.
# Fixed medical rule tables. Do not replace with AI.
#
# TWO tables, because the rules depend on the component:
#   - rbc          : red cells only (plasma removed). More flexible.
#   - whole_blood  : red cells AND plasma. Stricter, so the donor's ABO group
#                    must match the receiver's, and Rh-negative receivers
#                    only get Rh-negative blood.
#
# NOT valid for plasma or platelets, which follow different rules.
# Source: standard ABO/Rh chart (add the exact reference here).
# Must be reviewed by a doctor or blood bank officer before real use.
# The hospital cross-match is always the final check.

COMPONENTS = ("whole_blood", "rbc")

RBC_COMPATIBLE_DONORS = {
    "O-":  ["O-"],
    "O+":  ["O+", "O-"],
    "A-":  ["A-", "O-"],
    "A+":  ["A+", "A-", "O+", "O-"],
    "B-":  ["B-", "O-"],
    "B+":  ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
}

WHOLE_BLOOD_COMPATIBLE_DONORS = {
    "O-":  ["O-"],
    "O+":  ["O+", "O-"],
    "A-":  ["A-"],
    "A+":  ["A+", "A-"],
    "B-":  ["B-"],
    "B+":  ["B+", "B-"],
    "AB-": ["AB-"],
    "AB+": ["AB+", "AB-"],
}

TABLES = {
    "rbc": RBC_COMPATIBLE_DONORS,
    "whole_blood": WHOLE_BLOOD_COMPATIBLE_DONORS,
}

# Used to check that a blood group is valid (the same groups in every table)
COMPATIBLE_DONORS = RBC_COMPATIBLE_DONORS


def compatible_donors(receiver_group: str, component: str = "whole_blood") -> list[str]:
    """Return the donor blood groups that can give to this receiver."""
    group = receiver_group.strip().upper()
    kind = component.strip().lower()
    if kind not in TABLES:
        raise ValueError(f"Unknown component: {component}")
    if group not in TABLES[kind]:
        raise ValueError(f"Unknown blood group: {receiver_group}")
    return TABLES[kind][group]