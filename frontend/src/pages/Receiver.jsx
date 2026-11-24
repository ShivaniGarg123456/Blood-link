
import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import "../App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

const BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

const translations = {
  en: {
    title: "Blood Request",
    subtitle: "Speak or fill out the form to send a blood request.",
    details: "Details",
    confirm: "Confirm",
    submit: "Submit",
    requirement: "Tell us what you need",
    micOptional: "The microphone is optional. You can fill out the form directly.",
    listening: "Listening...",
    tapSpeak: "Tap to Speak",
    voiceVisible: "Your speech will appear here as text",
    speakHint: "You can speak in Hindi or English",
    voiceUnsupported: "Voice typing is not supported. You can fill out the form manually.",
    voiceError: "Voice capture failed. You can fill out the form manually.",
    type: "Want to type instead?",
    example: "Example: I need 2 units of O+ blood...",
    manual: "Or fill out the form manually",
    receiverName: "Receiver Name",
    patientName: "Patient name",
    bloodGroup: "Blood Group",
    units: "Units Required",
    selectUnits: "Select units",
    notSpecified: "Not specified",
    urgency: "Urgency",
    critical: "Critical",
    high: "High",
    normal: "Normal",
    component: "Blood Component",
    wholeBlood: "Whole blood",
    rbc: "RBC",
    doctorSlip: "Please check the doctor's prescription.",
    hospitalName: "Hospital Name",
    hospitalPlaceholder: "Enter hospital name",
    review: "Review Details",
    processing: "Processing details...",
    aiProcessing: "AI is processing the details...",
    reviewRequest: "Review your request",
    checkDetails: "Carefully check every detail before sending.",
    aiWarning: "AI could not identify some details. Please fill in the highlighted fields.",
    hospitalSearch: "Find Your Hospital",
    hospitalCity: "Enter hospital name and city",
    searching: "Searching...",
    search: "Search",
    chooseHospital: "Select your hospital from the suggestions below. Its location will be saved automatically.",
    selectedHospital: "Selected hospital:",
    coordinates: "Coordinates:",
    hospitalRequired: "Please enter the hospital name and city.",
    hospitalNotFound: "No hospital suggestions found. Check the name and city.",
    hospitalSearchError: "Hospital search failed. Please try again.",
    hospitalLocationRequired: "Please search and select a hospital from the suggestions.",
    requiredError: "Name, blood group, units and a selected hospital are required.",
    apiMissing: "Backend API URL is not configured. The request cannot be sent to the server yet.",
    requestFailed: "Request could not be submitted.",
    aiUnavailable: "AI parsing is currently unavailable. You can enter the details manually.",
    back: "Back",
    sending: "Sending...",
    sendRequest: "Send Request",
    success: "Request Submitted",
    successText: "Your blood request has been sent successfully.",
    another: "Create another request",
  },

  hi: {
    title: "ब्लड रिक्वेस्ट",
    subtitle: "बोलकर या फॉर्म भरकर ब्लड रिक्वेस्ट भेजें।",
    details: "जानकारी",
    confirm: "पुष्टि करें",
    submit: "जमा करें",
    requirement: "अपनी जरूरत बताएं",
    micOptional: "माइक इस्तेमाल करना जरूरी नहीं है। आप सीधे फॉर्म भी भर सकते हैं।",
    listening: "सुन रहा है...",
    tapSpeak: "बोलने के लिए दबाएं",
    voiceVisible: "आपकी आवाज यहां टेक्स्ट में दिखाई देगी",
    speakHint: "आप हिंदी या अंग्रेजी में बोल सकते हैं",
    voiceUnsupported: "वॉइस टाइपिंग उपलब्ध नहीं है। आप फॉर्म खुद भर सकते हैं।",
    voiceError: "आवाज रिकॉर्ड नहीं हो पाई। आप फॉर्म खुद भर सकते हैं।",
    type: "लिखना चाहते हैं?",
    example: "उदाहरण: O+ ब्लड के 2 यूनिट चाहिए...",
    manual: "या फॉर्म खुद भरें",
    receiverName: "रिसीवर का नाम",
    patientName: "मरीज का नाम",
    bloodGroup: "ब्लड ग्रुप",
    units: "कितने यूनिट चाहिए",
    selectUnits: "यूनिट चुनें",
    notSpecified: "बताया नहीं गया",
    urgency: "जरूरत की गंभीरता",
    critical: "बहुत जरूरी",
    high: "अधिक जरूरी",
    normal: "सामान्य",
    component: "ब्लड का प्रकार",
    wholeBlood: "होल ब्लड",
    rbc: "RBC",
    doctorSlip: "डॉक्टर की पर्ची देखें।",
    hospitalName: "अस्पताल का नाम",
    hospitalPlaceholder: "अस्पताल का नाम लिखें",
    review: "जानकारी जांचें",
    processing: "जानकारी तैयार हो रही है...",
    aiProcessing: "AI जानकारी समझ रहा है...",
    reviewRequest: "अपनी रिक्वेस्ट जांचें",
    checkDetails: "भेजने से पहले हर जानकारी ध्यान से जांच लें।",
    aiWarning: "AI कुछ जानकारी नहीं समझ पाया। हाइलाइट किए गए बॉक्स खुद भरें।",
    hospitalSearch: "अपना अस्पताल खोजें",
    hospitalCity: "अस्पताल का नाम और शहर लिखें",
    searching: "खोज रहे हैं...",
    search: "खोजें",
    chooseHospital: "नीचे दी गई लिस्ट में से अपना अस्पताल चुनें। उसकी लोकेशन अपने आप सेव हो जाएगी।",
    selectedHospital: "चुना गया अस्पताल:",
    coordinates: "निर्देशांक:",
    hospitalRequired: "कृपया अस्पताल का नाम और शहर लिखें।",
    hospitalNotFound: "अस्पताल नहीं मिला। नाम और शहर जांचें।",
    hospitalSearchError: "अस्पताल खोज नहीं पाए। कृपया दोबारा कोशिश करें।",
    hospitalLocationRequired: "कृपया अस्पताल खोजकर सुझावों की लिस्ट में से चुनें।",
    requiredError: "नाम, ब्लड ग्रुप, यूनिट और चुना हुआ अस्पताल जरूरी है।",
    apiMissing: "Backend API URL सेट नहीं है। अभी रिक्वेस्ट सर्वर पर नहीं भेजी जा सकती।",
    requestFailed: "रिक्वेस्ट भेजी नहीं जा सकी।",
    aiUnavailable: "AI अभी उपलब्ध नहीं है। आप जानकारी खुद भर सकते हैं।",
    back: "वापस",
    sending: "भेज रहे हैं...",
    sendRequest: "रिक्वेस्ट भेजें",
    success: "रिक्वेस्ट भेज दी गई",
    successText: "आपकी ब्लड रिक्वेस्ट सफलतापूर्वक भेज दी गई है।",
    another: "एक और रिक्वेस्ट बनाएं",
  },
};

export default function Receiver() {
  const [language, setLanguage] = useState(
    () => localStorage.getItem("bloodlink-receiver-language") || "en"
  );

  const t = (key) => translations[language][key] || key;

  const changeLanguage = (value) => {
    setLanguage(value);
    localStorage.setItem("bloodlink-receiver-language", value);
  };

  const [step, setStep] = useState(1);
  const [inputText, setInputText] = useState("");
  const [listening, setListening] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [aiMissing, setAiMissing] = useState([]);

  const [form, setForm] = useState({
    receiver_name: "",
    blood_group: "",
    units_needed: "",
    hospital: "",
    latitude: null,
    longitude: null,
    urgency: "high",
    component: "whole_blood",
  });

  const [hospitalQuery, setHospitalQuery] = useState("");
  const [hospitalResults, setHospitalResults] = useState([]);
  const [searchingHospital, setSearchingHospital] = useState(false);
  const [sending, setSending] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const update = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setAiMissing((prev) => prev.filter((item) => item !== key));
    setError("");
  };

  // Restore receiver name from the previous request.
  useEffect(() => {
    if (!API_BASE_URL) return;

    fetch(`${API_BASE_URL}/requests/mine`)
      .then((response) => {
        if (!response.ok) throw new Error("Previous request unavailable");
        return response.json();
      })
      .then((data) => {
        const previous = data?.request || data?.data || data;

        if (previous?.receiver_name) {
          setForm((prev) => ({
            ...prev,
            receiver_name: previous.receiver_name,
          }));
        }
      })
      .catch(() => {});
  }, []);

  const startVoice = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(t("voiceUnsupported"));
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language === "hi" ? "hi-IN" : "en-IN";
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => {
      setListening(true);
      setError("");
    };

    recognition.onresult = (event) => {
      let text = "";

      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }

      setInputText(text);
    };

    recognition.onerror = () => {
      setError(t("voiceError"));
      setListening(false);
    };

    recognition.onend = () => setListening(false);

    recognition.start();
  };

  const reviewDetails = async () => {
    setError("");
    setLoading(true);
    setAiMissing([]);

    if (API_BASE_URL && inputText.trim()) {
      try {
        const response = await fetch(`${API_BASE_URL}/requests/parse`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: inputText.trim() }),
        });

        if (!response.ok) throw new Error("AI parsing failed");

        const result = await response.json();
        const parsed = result?.data || result?.parsed || result;

        const bloodGroup = parsed?.blood_group ?? "";
        const units = parsed?.units ?? "";
        const hospital = parsed?.hospital ?? "";

        setForm((prev) => ({
          ...prev,
          blood_group: bloodGroup,
          units_needed:
            units === null || units === "" ? "" : Number(units),
          hospital: hospital || "",
          latitude: null,
          longitude: null,
          urgency: parsed?.urgency || prev.urgency,
          component: parsed?.component || prev.component,
        }));

        setHospitalQuery(hospital || "");
        setHospitalResults([]);

        setAiMissing([
          ...(!bloodGroup ? ["blood_group"] : []),
          ...(units === null || units === "" ? ["units_needed"] : []),
          ...(!hospital ? ["hospital"] : []),
        ]);
      } catch {
        setError(t("aiUnavailable"));
      }
    } else if (form.hospital) {
      setHospitalQuery(form.hospital);
    }

    setLoading(false);
    setStep(2);
  };

  // Search hospital suggestions in India.
  const searchHospital = async () => {
    if (!hospitalQuery.trim()) {
      setError(t("hospitalRequired"));
      return;
    }

    setSearchingHospital(true);
    setError("");
    setHospitalResults([]);

    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=in&limit=8&q=${encodeURIComponent(
        hospitalQuery.trim()
      )}`;

      const response = await fetch(url, {
        headers: { "Accept-Language": language === "hi" ? "hi" : "en" },
      });

      if (!response.ok) throw new Error("Search failed");

      const results = await response.json();

      // Keep only results with usable coordinates and a place name.
      const validResults = results.filter(
        (place) =>
          place.display_name &&
          Number.isFinite(Number(place.lat)) &&
          Number.isFinite(Number(place.lon))
      );

      setHospitalResults(validResults);

      if (validResults.length === 0) {
        setError(t("hospitalNotFound"));
      }
    } catch {
      setError(t("hospitalSearchError"));
    } finally {
      setSearchingHospital(false);
    }
  };

  // Selecting a suggestion confirms the hospital and its coordinates.
  const selectHospital = (place) => {
    const lat = Number(place.lat);
    const lng = Number(place.lon);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      setError(t("hospitalNotFound"));
      return;
    }

    setForm((prev) => ({
      ...prev,
      hospital: place.display_name,
      latitude: lat,
      longitude: lng,
    }));

    setHospitalQuery(place.display_name);
    setHospitalResults([]);
    setAiMissing((prev) => prev.filter((item) => item !== "hospital"));
    setError("");
  };

  const canSend =
    form.receiver_name.trim() &&
    form.blood_group &&
    Number(form.units_needed) >= 1 &&
    Number(form.units_needed) <= 10 &&
    form.hospital.trim() &&
    form.latitude !== null &&
    form.longitude !== null &&
    Number.isFinite(Number(form.latitude)) &&
    Number.isFinite(Number(form.longitude));

  const submitRequest = async () => {
    if (!canSend) {
      setError(t("requiredError"));
      return;
    }

    if (!API_BASE_URL) {
      setError(t("apiMissing"));
      return;
    }

    setSending(true);
    setError("");

    const payload = {
      receiver_name: form.receiver_name.trim(),
      blood_group: form.blood_group,
      units_needed: Number(form.units_needed),
      hospital: form.hospital.trim(),
      latitude: Number(form.latitude),
      longitude: Number(form.longitude),
      urgency: form.urgency,
      component: form.component,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          result?.detail || result?.message || t("requestFailed")
        );
      }

      setSubmitted(true);
      setStep(3);
    } catch (err) {
      setError(err.message || t("requestFailed"));
    } finally {
      setSending(false);
    }
  };

  const fieldClass = (key) =>
    aiMissing.includes(key) ? "receiver-ai-missing" : "";

  return (
    <>
      <Navbar />

      <main className="receiver-page">
        <div className="receiver-container">
          <header className="receiver-heading">
            <span className="receiver-tag">BLOODLINK</span>
            <h1>{t("title")}</h1>
            <p>{t("subtitle")}</p>

            <select
              value={language}
              onChange={(e) => changeLanguage(e.target.value)}
              aria-label="Select Receiver language"
              style={{
                padding: "9px 14px",
                borderRadius: "8px",
                border: "1px solid #ddd",
                marginTop: "12px",
                cursor: "pointer",
              }}
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
            </select>
          </header>

          <div className="receiver-progress">
            {[t("details"), t("confirm"), t("submit")].map((label, index) => (
              <div
                key={index}
                className={`receiver-progress-step ${
                  step >= index + 1 ? "active" : ""
                }`}
              >
                <span>{index + 1}</span>
                <small>{label}</small>
              </div>
            ))}
          </div>

          {step === 1 && (
            <section className="receiver-card">
              <h2>{t("requirement")}</h2>
              <p className="receiver-muted">{t("micOptional")}</p>

              <button
                type="button"
                className={`receiver-mic ${listening ? "listening" : ""}`}
                onClick={startVoice}
              >
                <span className="receiver-mic-icon">🎙</span>
                <strong>
                  {listening ? t("listening") : t("tapSpeak")}
                </strong>
                <small>
                  {listening ? t("voiceVisible") : t("speakHint")}
                </small>
              </button>

              <p className="receiver-type-label">{t("type")}</p>

              <textarea
                className="receiver-textarea"
                rows="3"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={t("example")}
              />

              <div className="receiver-divider-label">{t("manual")}</div>

              <div className="receiver-field">
                <label>{t("receiverName")} *</label>
                <input
                  value={form.receiver_name}
                  onChange={(e) => update("receiver_name", e.target.value)}
                  placeholder={t("patientName")}
                />
              </div>

              <div className="receiver-field">
                <label>{t("bloodGroup")} *</label>
                <div className="receiver-blood-grid">
                  {BLOOD_GROUPS.map((group) => (
                    <button
                      type="button"
                      key={group}
                      className={`receiver-blood-btn ${
                        form.blood_group === group ? "selected" : ""
                      }`}
                      onClick={() => update("blood_group", group)}
                    >
                      {group}
                    </button>
                  ))}
                </div>
              </div>

              <div className="receiver-field">
                <label>{t("units")} *</label>
                <div className="receiver-units">
                  <button
                    type="button"
                    disabled={
                      !form.units_needed || Number(form.units_needed) <= 1
                    }
                    onClick={() =>
                      update(
                        "units_needed",
                        Math.max(1, Number(form.units_needed) - 1)
                      )
                    }
                  >
                    −
                  </button>

                  <span>{form.units_needed || t("selectUnits")}</span>

                  <button
                    type="button"
                    disabled={Number(form.units_needed) >= 10}
                    onClick={() =>
                      update(
                        "units_needed",
                        form.units_needed
                          ? Math.min(10, Number(form.units_needed) + 1)
                          : 1
                      )
                    }
                  >
                    +
                  </button>
                </div>
              </div>

              <div className="receiver-field">
                <label>{t("urgency")}</label>
                <div className="receiver-choice-row">
                  {["critical", "high", "normal"].map((item) => (
                    <button
                      type="button"
                      key={item}
                      className={`receiver-choice-btn ${
                        form.urgency === item ? "selected" : ""
                      }`}
                      onClick={() => update("urgency", item)}
                    >
                      {t(item)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="receiver-field">
                <label>{t("component")}</label>
                <div className="receiver-choice-row">
                  <button
                    type="button"
                    className={`receiver-choice-btn ${
                      form.component === "whole_blood" ? "selected" : ""
                    }`}
                    onClick={() => update("component", "whole_blood")}
                  >
                    {t("wholeBlood")}
                  </button>

                  <button
                    type="button"
                    className={`receiver-choice-btn ${
                      form.component === "rbc" ? "selected" : ""
                    }`}
                    onClick={() => update("component", "rbc")}
                  >
                    {t("rbc")}
                  </button>
                </div>

                <small className="receiver-muted">{t("doctorSlip")}</small>
              </div>

              <div className="receiver-field">
                <label>{t("hospitalName")}</label>
                <input
                  value={form.hospital}
                  onChange={(e) => update("hospital", e.target.value)}
                  placeholder={t("hospitalPlaceholder")}
                />
              </div>

              {error && <p className="receiver-error">{error}</p>}

              <button
                type="button"
                className="receiver-primary-btn"
                onClick={reviewDetails}
                disabled={loading}
              >
                {loading ? t("processing") : t("review")}
              </button>
            </section>
          )}

          {step === 2 && (
            <section className="receiver-card">
              <h2>{t("reviewRequest")}</h2>
              <p className="receiver-muted">{t("checkDetails")}</p>

              {aiMissing.length > 0 && (
                <p className="receiver-warning">{t("aiWarning")}</p>
              )}

              <div className="receiver-field">
                <label>{t("receiverName")} *</label>
                <input
                  value={form.receiver_name}
                  onChange={(e) => update("receiver_name", e.target.value)}
                  placeholder={t("patientName")}
                />
              </div>

              <div className={`receiver-field ${fieldClass("blood_group")}`}>
                <label>{t("bloodGroup")} *</label>
                <div className="receiver-blood-grid">
                  {BLOOD_GROUPS.map((group) => (
                    <button
                      type="button"
                      key={group}
                      className={`receiver-blood-btn ${
                        form.blood_group === group ? "selected" : ""
                      }`}
                      onClick={() => update("blood_group", group)}
                    >
                      {group}
                    </button>
                  ))}
                </div>
              </div>

              <div className={`receiver-field ${fieldClass("units_needed")}`}>
                <label>{t("units")} *</label>
                <div className="receiver-units">
                  <button
                    type="button"
                    disabled={
                      !form.units_needed || Number(form.units_needed) <= 1
                    }
                    onClick={() =>
                      update(
                        "units_needed",
                        Math.max(1, Number(form.units_needed) - 1)
                      )
                    }
                  >
                    −
                  </button>

                  <span>{form.units_needed || t("notSpecified")}</span>

                  <button
                    type="button"
                    disabled={Number(form.units_needed) >= 10}
                    onClick={() =>
                      update(
                        "units_needed",
                        form.units_needed
                          ? Math.min(10, Number(form.units_needed) + 1)
                          : 1
                      )
                    }
                  >
                    +
                  </button>
                </div>
              </div>

              <div className="receiver-field">
                <label>{t("urgency")}</label>
                <div className="receiver-choice-row">
                  {["critical", "high", "normal"].map((item) => (
                    <button
                      type="button"
                      key={item}
                      className={`receiver-choice-btn ${
                        form.urgency === item ? "selected" : ""
                      }`}
                      onClick={() => update("urgency", item)}
                    >
                      {t(item)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="receiver-field">
                <label>{t("component")}</label>
                <div className="receiver-choice-row">
                  <button
                    type="button"
                    className={`receiver-choice-btn ${
                      form.component === "whole_blood" ? "selected" : ""
                    }`}
                    onClick={() => update("component", "whole_blood")}
                  >
                    {t("wholeBlood")}
                  </button>

                  <button
                    type="button"
                    className={`receiver-choice-btn ${
                      form.component === "rbc" ? "selected" : ""
                    }`}
                    onClick={() => update("component", "rbc")}
                  >
                    {t("rbc")}
                  </button>
                </div>

                <small className="receiver-muted">{t("doctorSlip")}</small>
              </div>

              <div className={`receiver-field ${fieldClass("hospital")}`}>
                <label>{t("hospitalSearch")} *</label>

                <div className="receiver-hospital-search">
                  <input
                    value={hospitalQuery}
                    onChange={(e) => {
                      const value = e.target.value;

                      setHospitalQuery(value);
                      setHospitalResults([]);

                      // Typing a new name clears the old selection and coordinates.
                      setForm((prev) => ({
                        ...prev,
                        hospital: "",
                        latitude: null,
                        longitude: null,
                      }));

                      setAiMissing((prev) =>
                        prev.includes("hospital") ? prev : [...prev, "hospital"]
                      );
                      setError("");
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        searchHospital();
                      }
                    }}
                    placeholder={t("hospitalCity")}
                  />

                  <button
                    type="button"
                    onClick={searchHospital}
                    disabled={searchingHospital}
                  >
                    {searchingHospital ? t("searching") : t("search")}
                  </button>
                </div>

                <p className="receiver-muted">{t("chooseHospital")}</p>

                {hospitalResults.length > 0 && (
                  <div className="receiver-search-results">
                    {hospitalResults.map((place) => (
                      <button
                        type="button"
                        key={place.place_id}
                        onClick={() => selectHospital(place)}
                      >
                        {place.display_name}
                      </button>
                    ))}
                  </div>
                )}

                {form.hospital &&
                  form.latitude !== null &&
                  form.longitude !== null && (
                    <div className="receiver-location-info">
                      <p>
                        <strong>{t("selectedHospital")}</strong>
                      </p>
                      <p>{form.hospital}</p>
                      <small>
                        {t("coordinates")} {form.latitude.toFixed(5)},{" "}
                        {form.longitude.toFixed(5)}
                      </small>
                    </div>
                  )}
              </div>

              {error && <p className="receiver-error">{error}</p>}

              <div className="receiver-actions">
                <button
                  type="button"
                  className="receiver-back-btn"
                  onClick={() => setStep(1)}
                >
                  {t("back")}
                </button>

                <button
                  type="button"
                  className="receiver-primary-btn"
                  onClick={submitRequest}
                  disabled={!canSend || sending}
                >
                  {sending ? t("sending") : t("sendRequest")}
                </button>
              </div>
            </section>
          )}

          {step === 3 && submitted && (
            <section className="receiver-card receiver-success">
              <div className="receiver-success-icon">✓</div>
              <h2>{t("success")}</h2>
              <p>{t("successText")}</p>

              <button
                type="button"
                className="receiver-primary-btn"
                onClick={() => window.location.reload()}
              >
                {t("another")}
              </button>
            </section>
          )}
        </div>
      </main>

      <Footer />
    </>
  );
}
