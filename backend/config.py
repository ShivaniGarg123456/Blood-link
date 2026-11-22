import os

# Radius steps, in km. Each wave only alerts donors not alerted before.
# The search keeps growing until the receiver closes the request or
# enough donors are confirmed. 5000 km covers the whole of India.
WAVE_RADII_KM = [15, 30, 45, 60, 100, 200, 500, 1000, 5000]

# How long donors have to accept in each wave (3 minutes).
# For the live demo, set WAVE_SECONDS=20 in your environment to speed it up.
WAVE_SECONDS = int(os.getenv("WAVE_SECONDS", "180"))

# When a donor accepts but a NEARER donor is still deciding, we wait up to
# this many seconds for the nearer donor. If nobody nearer is pending,
# the donor is confirmed immediately.
CONFIRM_WINDOW_SECONDS = int(os.getenv("CONFIRM_WINDOW_SECONDS", "15"))


# A request that is still open after this many hours is closed automatically,
# so donors who register much later are not alerted for an old request.
REQUEST_MAX_HOURS = int(os.getenv("REQUEST_MAX_HOURS", "24"))

# A donor who fails the hospital checkup is paused for this many days
CHECKUP_FAIL_PAUSE_DAYS = int(os.getenv("CHECKUP_FAIL_PAUSE_DAYS", "7"))


def next_radius(current_km: int):
    """Return the next radius in the list.

    Returns None after the last radius. That does NOT mean the request
    ends. It stays open and keeps checking for newly active donors until
    the receiver closes it or enough donors are confirmed.
    """
    for radius in WAVE_RADII_KM:
        if radius > current_km:
            return radius
    return None