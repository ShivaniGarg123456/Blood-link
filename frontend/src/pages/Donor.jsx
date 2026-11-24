
import { useState } from "react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";
import "../App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
  "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
  "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
  "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
  "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
  "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh",
];

const CITIES_BY_STATE = {
  "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Nellore"],
  "Arunachal Pradesh": ["Itanagar", "Naharlagun", "Tawang"],
  Assam: ["Guwahati", "Silchar", "Dibrugarh", "Jorhat"],
  Bihar: ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur"],
  Chhattisgarh: ["Raipur", "Bhilai", "Bilaspur", "Durg"],
  Goa: ["Panaji", "Margao", "Vasco da Gama"],
  Gujarat: ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
  Haryana: ["Palwal", "Faridabad", "Gurugram", "Panipat", "Rohtak", "Hisar", "Karnal", "Ambala", "Sonipat"],
  "Himachal Pradesh": ["Shimla", "Dharamshala", "Mandi", "Solan"],
  Jharkhand: ["Ranchi", "Jamshedpur", "Dhanbad", "Bokaro"],
  Karnataka: ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi"],
  Kerala: ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur"],
  "Madhya Pradesh": ["Bhopal", "Indore", "Gwalior", "Jabalpur", "Ujjain"],
  Maharashtra: ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"],
  Manipur: ["Imphal", "Thoubal"],
  Meghalaya: ["Shillong", "Tura"],
  Mizoram: ["Aizawl", "Lunglei"],
  Nagaland: ["Kohima", "Dimapur"],
  Odisha: ["Bhubaneswar", "Cuttack", "Rourkela", "Puri"],
  Punjab: ["Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Mohali"],
  Rajasthan: ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
  Sikkim: ["Gangtok", "Namchi"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
  Telangana: ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar"],
  Tripura: ["Agartala", "Udaipur"],
  "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Prayagraj", "Noida", "Ghaziabad", "Meerut"],
  Uttarakhand: ["Dehradun", "Haridwar", "Roorkee", "Haldwani"],
  "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri"],
  Delhi: ["New Delhi", "Delhi"],
  "Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag"],
  Ladakh: ["Leh", "Kargil"],
};

const permanentConditions = [
  { label: "HIV", value: "hiv" },
  { label: "Hepatitis B", value: "hepatitis_b" },
  { label: "Hepatitis C", value: "hepatitis_c" },
  { label: "Heart Disease", value: "heart_disease" },
  { label: "Cancer", value: "cancer" },
  { label: "Epilepsy", value: "epilepsy" },
];

const temporaryConditions = [
  { label: "Fever", value: "fever" },
  { label: "Recent Surgery", value: "surgery" },
  { label: "Pregnancy", value: "pregnancy" },
  { label: "Breastfeeding", value: "breastfeeding" },
  { label: "Recent Tattoo", value: "tattoo" },
];

function calculateAge(dob) {
  if (!dob) return "";

  const birthDate = new Date(dob);
  const today = new Date();

  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDifference = today.getMonth() - birthDate.getMonth();

  if (
    monthDifference < 0 ||
    (monthDifference === 0 && today.getDate() < birthDate.getDate())
  ) {
    age--;
  }

  return age;
}

// Only use actual city-level address fields.
// Do not use county because it may contain a district or region.
function getCityFromAddress(address) {
  return (
    address.city ||
    address.town ||
    address.village ||
    address.municipality ||
    address.city_district ||
    ""
  );
}

async function readResponse(response) {
  const text = await response.text();

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function Donor() {
  const [formData, setFormData] = useState({
    name: "",
    phone: localStorage.getItem("userPhone") || "",
    dob: "",
    sex: "",
    blood_group: "",
    weight_kg: "",
    state: "",
    city: "",
    firstTimeDonor: "",
    last_donation_date: "",
  });

  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [permanent, setPermanent] = useState([]);
  const [temporary, setTemporary] = useState([]);
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [locationLoading, setLocationLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const age = calculateAge(formData.dob);

  const updateField = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({ ...prev, [name]: value }));
    setError("");
    setMessage("");
  };

  const handleConditionChange = (value, type) => {
    const setter = type === "permanent" ? setPermanent : setTemporary;
    const current = type === "permanent" ? permanent : temporary;

    if (value === "none") {
      setter(current.includes("none") ? [] : ["none"]);
    } else {
      setter(
        current.includes(value)
          ? current.filter((item) => item !== value && item !== "none")
          : [...current.filter((item) => item !== "none"), value]
      );
    }

    setError("");
  };

  const useMyLocation = () => {
    setError("");
    setMessage("");

    if (!navigator.geolocation) {
      setError(
        "Location is not supported by this browser. Please select your state and city manually."
      );
      return;
    }

    setLocationLoading(true);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;

        try {
          const response = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=14&addressdetails=1`,
            { headers: { "Accept-Language": "en" } }
          );

          if (!response.ok) {
            throw new Error("Could not find your location details.");
          }

          const data = await response.json();
          const address = data.address || {};

          const detectedState = address.state || "";
          const detectedCity = getCityFromAddress(address);

          if (!detectedState || !detectedCity) {
            throw new Error(
              "GPS could not identify your exact city. Please select your state and city manually."
            );
          }

          // Keep GPS coordinates only when a city is successfully identified.
          setFormData((prev) => ({
            ...prev,
            state: detectedState,
            city: detectedCity,
          }));

          setLatitude(lat);
          setLongitude(lon);

          setMessage(`GPS location detected: ${detectedCity}, ${detectedState}`);
        } catch (err) {
          setError(
            err.message ||
              "Could not identify your city. Please select it manually."
          );

          // Do not erase a previously valid manual selection.
        } finally {
          setLocationLoading(false);
        }
      },
      () => {
        setLocationLoading(false);
        setError(
          "Location permission denied or unavailable. Please select your state and city manually."
        );
      },
      {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 0,
      }
    );
  };

  const handleCityChange = async (e) => {
    const city = e.target.value;

    setFormData((prev) => ({ ...prev, city }));
    setLatitude(null);
    setLongitude(null);
    setError("");
    setMessage("");

    if (!city || !formData.state) return;

    try {
      const query = encodeURIComponent(`${city}, ${formData.state}, India`);

      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=in&q=${query}`,
        { headers: { "Accept-Language": "en" } }
      );

      if (!response.ok) {
        throw new Error("Could not find coordinates for this city.");
      }

      const results = await response.json();

      if (!results.length) {
        setError("Coordinates not found. Please try GPS or another city.");
        return;
      }

      setLatitude(Number(results[0].lat));
      setLongitude(Number(results[0].lon));
      setMessage("City selected successfully.");
    } catch {
      setError("Could not get city coordinates. Please try again or use GPS.");
    }
  };

  const handleStateChange = (e) => {
    const state = e.target.value;

    setFormData((prev) => ({
      ...prev,
      state,
      city: "",
    }));

    setLatitude(null);
    setLongitude(null);
    setError("");
    setMessage("");
  };

  const validateForm = () => {
    if (!formData.name.trim()) return "Please enter your full name.";

    if (!/^[6-9]\d{9}$/.test(formData.phone)) {
      return "Please enter a valid 10-digit Indian mobile number.";
    }

    if (!formData.dob) return "Please enter your date of birth.";

    if (age < 18 || age > 65) {
      return "Donors must be between 18 and 65 years old.";
    }

    if (!formData.sex) return "Please select your gender.";
    if (!formData.blood_group) return "Please select your blood group.";

    if (!formData.weight_kg || Number(formData.weight_kg) < 45) {
      return "Minimum required weight is 45 kg.";
    }

    if (!formData.state) return "Please select your state.";
    if (!formData.city) return "Please select your city.";

    if (
      latitude === null ||
      longitude === null ||
      !Number.isFinite(latitude) ||
      !Number.isFinite(longitude)
    ) {
      return "Please use GPS or select a city to get your location coordinates.";
    }

    if (!formData.firstTimeDonor) {
      return "Please tell us whether you have donated blood before.";
    }

    if (
      formData.firstTimeDonor === "yes" &&
      !formData.last_donation_date
    ) {
      return "Please enter your last donation date.";
    }

    if (
      formData.last_donation_date &&
      new Date(formData.last_donation_date) > new Date()
    ) {
      return "Last donation date cannot be in the future.";
    }

    if (!permanent.length) {
      return "Please select an option in Permanent Medical Conditions.";
    }

    if (!temporary.length) {
      return "Please select an option in Temporary Medical Conditions.";
    }

    if (!consent) return "Please accept the Terms and Conditions.";

    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    const token = localStorage.getItem("token");

    if (!token) {
      setError("Please login before registering as a donor.");
      return;
    }

    const registrationData = {
      name: formData.name.trim(),
      state: formData.state,
      city: formData.city,
      latitude,
      longitude,
      age: Number(age),
      sex: formData.sex,
      weight_kg: Number(formData.weight_kg),
      blood_group: formData.blood_group,
      conditions: [
        ...permanent.filter((item) => item !== "none"),
        ...temporary.filter((item) => item !== "none"),
      ],
      last_donation_date:
        formData.firstTimeDonor === "yes"
          ? formData.last_donation_date
          : null,
      consent: true,
    };

    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/donors/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(registrationData),
      });

      const data = await readResponse(response);

      if (response.status === 401) {
        localStorage.removeItem("token");
        setError("Your login session has expired. Please login again.");
        return;
      }

      if (!response.ok) {
        const detail = data?.detail;

        const errorMessage = Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : detail || data?.message || "Donor registration failed.";

        throw new Error(errorMessage);
      }

      const successMessage =
        typeof data === "string"
          ? data
          : data?.message || data?.status || "Donor registration successful!";

      setMessage(`Registration successful: ${successMessage}`);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setSubmitting(false);
    }
  };

  const cityOptions = CITIES_BY_STATE[formData.state] || [];

  return (
    <>
      <Navbar />

      <main className="donor-registration">
        <div className="registration-heading">
          <h1>Donor Registration</h1>
          <p>Complete your details to become a BloodLink donor.</p>
        </div>

        <form className="registration-card" onSubmit={handleSubmit}>
          <h2>Personal Details</h2>

          <div className="registration-grid">
            <div className="form-field">
              <label>Full Name *</label>
              <input
                name="name"
                value={formData.name}
                onChange={updateField}
                placeholder="Enter your full name"
              />
            </div>

            <div className="form-field">
              <label>Mobile Number *</label>
              <input
                name="phone"
                type="tel"
                inputMode="numeric"
                maxLength={10}
                value={formData.phone}
                onChange={(e) => {
                  setFormData((prev) => ({
                    ...prev,
                    phone: e.target.value.replace(/\D/g, "").slice(0, 10),
                  }));
                  setError("");
                }}
                placeholder="10-digit mobile number"
              />
            </div>

            <div className="form-field">
              <label>Date of Birth *</label>
              <input
                type="date"
                name="dob"
                max={new Date().toISOString().split("T")[0]}
                value={formData.dob}
                onChange={updateField}
              />
              {formData.dob && (
                <small>Calculated age: {age} years</small>
              )}
            </div>

            <div className="form-field">
              <label>Gender *</label>
              <select name="sex" value={formData.sex} onChange={updateField}>
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            <div className="form-field">
              <label>Blood Group *</label>
              <select
                name="blood_group"
                value={formData.blood_group}
                onChange={updateField}
              >
                <option value="">Select blood group</option>
                {["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"].map(
                  (group) => (
                    <option key={group} value={group}>
                      {group}
                    </option>
                  )
                )}
              </select>
            </div>

            <div className="form-field">
              <label>Weight (kg) *</label>
              <input
                type="number"
                name="weight_kg"
                min="45"
                value={formData.weight_kg}
                onChange={updateField}
                placeholder="Enter weight"
              />
            </div>
          </div>

          <div className="registration-divider" />

          <h2>Location Details</h2>
          <p className="section-description">
            Use GPS to detect your state and city automatically, or select them manually.
          </p>

          <button
            type="button"
            className="registration-submit"
            onClick={useMyLocation}
            disabled={locationLoading}
          >
            {locationLoading ? "Detecting location..." : "Use My Location"}
          </button>

          <div className="registration-grid" style={{ marginTop: "18px" }}>
            <div className="form-field">
              <label>State *</label>
              <select value={formData.state} onChange={handleStateChange}>
                <option value="">Select state</option>
                {INDIAN_STATES.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
                {formData.state && !INDIAN_STATES.includes(formData.state) && (
                  <option value={formData.state}>{formData.state}</option>
                )}
              </select>
            </div>

            <div className="form-field">
              <label>City *</label>
              <select
                value={formData.city}
                onChange={handleCityChange}
                disabled={!formData.state}
              >
                <option value="">Select city</option>
                {cityOptions.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
                {formData.city && !cityOptions.includes(formData.city) && (
                  <option value={formData.city}>{formData.city}</option>
                )}
              </select>
            </div>
          </div>

          {latitude !== null && longitude !== null && (
            <p className="section-description">
              Location coordinates received successfully.
            </p>
          )}

          <div className="registration-divider" />

          <h2>Donation Details</h2>
          <p className="section-description">
            Have you donated blood before?
          </p>

          <div className="registration-grid">
            <label className="registration-checkbox">
              <input
                type="radio"
                name="firstTimeDonor"
                value="yes"
                checked={formData.firstTimeDonor === "yes"}
                onChange={updateField}
              />
              Yes
            </label>

            <label className="registration-checkbox">
              <input
                type="radio"
                name="firstTimeDonor"
                value="no"
                checked={formData.firstTimeDonor === "no"}
                onChange={(e) => {
                  setFormData((prev) => ({
                    ...prev,
                    firstTimeDonor: "no",
                    last_donation_date: "",
                  }));
                  setError("");
                }}
              />
              No, this is my first time
            </label>
          </div>

          {formData.firstTimeDonor === "yes" && (
            <div className="form-field donation-date-field">
              <label>Last Donation Date *</label>
              <input
                type="date"
                name="last_donation_date"
                max={new Date().toISOString().split("T")[0]}
                value={formData.last_donation_date}
                onChange={updateField}
              />
            </div>
          )}

          <div className="registration-divider" />

          <h2>Permanent Medical Conditions *</h2>
          <p className="section-description">
            Please select any condition that applies to you, or select None.
          </p>

          <div className="condition-grid">
            {permanentConditions.map((condition) => (
              <label className="registration-checkbox" key={condition.value}>
                <input
                  type="checkbox"
                  checked={permanent.includes(condition.value)}
                  onChange={() =>
                    handleConditionChange(condition.value, "permanent")
                  }
                />
                {condition.label}
              </label>
            ))}

            <label className="registration-checkbox">
              <input
                type="checkbox"
                checked={permanent.includes("none")}
                onChange={() => handleConditionChange("none", "permanent")}
              />
              None of the above
            </label>
          </div>

          <div className="registration-divider" />

          <h2>Temporary Medical Conditions *</h2>
          <p className="section-description">
            Please select any condition that applies to you, or select None.
          </p>

          <div className="condition-grid">
            {temporaryConditions.map((condition) => (
              <label className="registration-checkbox" key={condition.value}>
                <input
                  type="checkbox"
                  checked={temporary.includes(condition.value)}
                  onChange={() =>
                    handleConditionChange(condition.value, "temporary")
                  }
                />
                {condition.label}
              </label>
            ))}

            <label className="registration-checkbox">
              <input
                type="checkbox"
                checked={temporary.includes("none")}
                onChange={() => handleConditionChange("none", "temporary")}
              />
              None of the above
            </label>
          </div>

          <div className="registration-divider" />

          <label className="signup-consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span>
              I confirm that the information provided is accurate and agree
              to the Terms and Conditions.
            </span>
          </label>

          {error && <p className="signup-error">{error}</p>}
          {message && <p className="signup-message">{message}</p>}

          <button
            type="submit"
            className="registration-submit"
            disabled={submitting}
          >
            {submitting ? "Submitting..." : "Submit Registration"}
          </button>
        </form>
      </main>

      <Footer />
    </>
  );
}

export default Donor;
