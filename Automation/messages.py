"""All user-facing text (Hindi + English). Edit wording here only."""

GROUP_SPOKEN_HI = {"A+": "ए पॉज़िटिव", "A-": "ए नेगेटिव", "B+": "बी पॉज़िटिव", "B-": "बी नेगेटिव",
                   "O+": "ओ पॉज़िटिव", "O-": "ओ नेगेटिव", "AB+": "एबी पॉज़िटिव", "AB-": "एबी नेगेटिव"}
COMPONENT = {"whole_blood": {"en": "blood", "hi": "खून"},
             "rbc": {"en": "red cells", "hi": "रेड सेल्स"},
             "platelets": {"en": "platelets", "hi": "प्लेटलेट्स"}}


def spoken_group(group, lang):
    if lang == "hi":
        return GROUP_SPOKEN_HI.get(group, group)
    return group.replace("+", " positive").replace("-", " negative")


def component_label(component, lang):
    key = getattr(component, "value", component)
    return COMPONENT.get(key, COMPONENT["whole_blood"]).get(lang, "blood")


def human_window(seconds, lang="en"):
    seconds = max(0, int(seconds))
    if seconds >= 60:
        m = round(seconds / 60)
        return f"{m} मिनट" if lang == "hi" else f"{m} minute{'s' if m != 1 else ''}"
    return f"{seconds} सेकंड" if lang == "hi" else f"{seconds} seconds"


TEXT = {
    "alert": {
        "en": "🩸 Blood needed near you\n{group} ({comp}) · {km} km away\nHospital: {hospital}\nAccept within {window}\n{link}",
        "hi": "🩸 आपके पास खून की ज़रूरत है\n{group} ({comp}) · {km} किमी दूर\nअस्पताल: {hospital}\n{window} में स्वीकार करें\n{link}"},
    "reminder": {
        "en": "⏰ Still needed: {group} at {hospital}, {km} km away. {left} left.\n{link}",
        "hi": "⏰ अभी भी ज़रूरत है: {hospital} में {group}, {km} किमी दूर। {left} बचे हैं।\n{link}"},
    "audio_caption": {
        "en": "🔊 Voice alert: {group} needed at {hospital}. {left} left.",
        "hi": "🔊 वॉइस अलर्ट: {hospital} में {group} चाहिए। {left} बचे हैं।"},
    "voice": {
        "en": "Blood request near you. {spoken} {comp} is needed at {hospital}, {km} kilometres away. Please accept within {window}.",
        "hi": "आपके पास खून की ज़रूरत है। {hospital} में {spoken} {comp} चाहिए, {km} किलोमीटर दूर। कृपया {window} में स्वीकार करें।"},
    "confirmed_donor": {
        "en": "✅ You are confirmed. Receiver: {receiver_name}, {receiver_phone}. Hospital: {hospital}. The hospital will check your eligibility before donation.",
        "hi": "✅ आप चुने गए हैं। रिसीवर: {receiver_name}, {receiver_phone}। अस्पताल: {hospital}। दान से पहले अस्पताल आपकी पात्रता जाँचेगा।"},
    "confirmed_receiver": {
        "en": "✅ A donor accepted: {donor_name}, {donor_phone}. The hospital will check eligibility before donation.",
        "hi": "✅ एक डोनर ने स्वीकार किया: {donor_name}, {donor_phone}। दान से पहले अस्पताल पात्रता जाँचेगा।"},
    "standby": {
        "en": "Thank you for accepting! The need is fulfilled for now. We will contact you if it is needed again.",
        "hi": "स्वीकार करने के लिए धन्यवाद! अभी ज़रूरत पूरी हो गई है। ज़रूरत पड़ने पर हम आपसे संपर्क करेंगे।"},
    "tentative": {
        "en": "Accepted! Confirming the nearest donor, please wait about {n} seconds.",
        "hi": "स्वीकार हो गया! सबसे नज़दीकी डोनर चुना जा रहा है, लगभग {n} सेकंड रुकें।"},
    "tentative_wait": {
        "en": "Accepted! We are waiting for the other donors for this request.",
        "hi": "स्वीकार हो गया! इस अनुरोध के लिए बाकी डोनर्स का इंतज़ार है।"},
    "declined": {
        "en": "Okay, we will not count on you for this request.",
        "hi": "ठीक है, इस अनुरोध के लिए हम आप पर निर्भर नहीं रहेंगे।"},
    "linked": {
        "en": "✅ Telegram linked. You will get BloodLink alerts here.",
        "hi": "✅ टेलीग्राम जुड़ गया। BloodLink के अलर्ट यहीं मिलेंगे।"},
}


def render(kind, lang, **kw):
    lang = lang if lang in ("en", "hi") else "en"
    return TEXT[kind][lang].format(**kw)


def describe_accept_result(result, lang="en"):
    """One plain-language line for the outcome of engine.accept()."""
    outcome = result.get("outcome")
    if outcome == "confirmed":
        dv = result["donor_view"]
        return render("confirmed_donor", lang, receiver_name=dv["receiver_name"],
                      receiver_phone=dv["receiver_phone"], hospital=dv["hospital"])
    if outcome == "standby":
        return render("standby", lang)
    if outcome == "tentative":
        n = result.get("seconds_to_confirm")
        return render("tentative_wait", lang) if n is None else render("tentative", lang, n=n)
    return result.get("message", "Something went wrong.")
