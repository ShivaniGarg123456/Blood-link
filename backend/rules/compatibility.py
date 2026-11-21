# Which donor blood groups can give to each receiver blood group.
# Fixed medical rule table. Do not replace with AI.

COMPATIBLE_DONORS = {
    "O-":  ["O-"],
    "O+":  ["O+", "O-"],
    "A-":  ["A-", "O-"],
    "A+":  ["A+", "A-", "O+", "O-"],
    "B-":  ["B-", "O-"],
    "B+":  ["B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
}


def compatible_donors(receiver_group: str) -> list[str]:
    """Return the donor blood groups that can give to this receiver."""
    group = receiver_group.strip().upper()
    if group not in COMPATIBLE_DONORS:
        raise ValueError(f"Unknown blood group: {receiver_group}")
    return COMPATIBLE_DONORS[group]