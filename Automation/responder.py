"""Accept / decline for a donor, shared by the Telegram buttons and the accept link."""
from . import messages as M


def respond(bridge, store, alert_id, action, lang, confirm_seconds=15):
    """action is "acc" or "dec". Returns (text for the donor, new response or None)."""
    res = bridge.accept(alert_id) if action == "acc" else bridge.decline(alert_id)
    if not res.get("ok"):
        return res.get("detail", "Something went wrong."), None
    response = res.get("response")
    if response in ("confirmed", "standby"):
        store.set_event(alert_id, response)   # donor is told right here, so the worker must not repeat it
    return M.describe_response(res, lang, confirm_seconds), response
