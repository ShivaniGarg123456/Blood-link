"""Wave timer, called about once a second for every open request.

It has no backend imports: the backend's own functions are passed in (see bridge.py),
so the logic here is easy to test and stays in step with the backend's rules.

For one request it:
  1. calls resolve (confirms nearest donors, standby, the 15 s nearest-donor wait)
  2. when the current wave is over (all answered or the timer ran out) moves to the next radius
     and alerts the new donors; empty radii are skipped at once
  3. at the last radius, keeps looking for donors who became active later
"""


def advance(db, req, now, *, resolve, wave_is_finished, next_radius, send_wave):
    resolve(db, req, now)
    if req.status != "open":
        return []
    created = []
    radius = req.current_radius_km
    while wave_is_finished(db, req, radius, now):
        nxt = next_radius(radius)
        if nxt is None:
            created = send_wave(db, req, radius)
            break
        radius = nxt
        req.current_radius_km = radius
        db.commit()
        created = send_wave(db, req, radius)
        if created:
            break
    return created
