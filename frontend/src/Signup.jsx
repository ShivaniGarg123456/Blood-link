
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Droplet, ShieldCheck } from "lucide-react";
import "./App.css";

function Signup() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [verified, setVerified] = useState(false);
  const [consent, setConsent] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const validateName = () => {
    const cleanName = name.trim();

    if (!cleanName) {
      return "Full name is required.";
    }

    if (cleanName.length < 2 || !/^[a-zA-Z\s.'-]+$/.test(cleanName)) {
      return "Please enter a valid full name.";
    }

    return "";
  };

  const validatePhone = () => {
    if (!phone.trim()) {
      return "Mobile number is required.";
    }

    if (!/^[6-9]\d{9}$/.test(phone)) {
      return "Please enter a valid 10-digit Indian mobile number.";
    }

    return "";
  };

  const handleSendOTP = () => {
    setError("");
    setMessage("");

    const nameError = validateName();
    const phoneError = validatePhone();

    if (nameError || phoneError) {
      setError(nameError || phoneError);
      return;
    }

    setOtpSent(true);
    setVerified(false);
    setOtp("");
    setMessage("Demo OTP sent successfully. Use 1234.");
  };

  const handleVerifyOTP = () => {
    setError("");
    setMessage("");

    if (!otp.trim()) {
      setError("Please enter the OTP.");
      return;
    }

    if (!/^\d{4}$/.test(otp)) {
      setError("OTP must contain exactly 4 digits.");
      return;
    }

    if (otp !== "1234") {
      setError("Invalid OTP. Please try again.");
      return;
    }

    setVerified(true);
    setMessage("Mobile number verified successfully!");
  };

  const handleSignup = (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    const nameError = validateName();
    const phoneError = validatePhone();

    if (nameError || phoneError) {
      setError(nameError || phoneError);
      return;
    }

    if (!verified) {
      setError("Please verify your mobile number first.");
      return;
    }

    if (!consent) {
      setError("Please accept Terms and Conditions.");
      return;
    }

    // Next step: connect signup with backend.
    navigate("/", {
  state: { name: name.trim(), phone },
});
  };

  return (
    <div className="signup-page">
      <div className="signup-card">
        <div className="signup-logo">
          <Droplet size={34} fill="#c62828" color="#c62828" />
          <span>BloodLink</span>
        </div>

        <h1>Create your account</h1>
        <p className="signup-subtitle">
          Join our community and help save lives.
        </p>

        <form onSubmit={handleSignup}>
          <div className="signup-field">
            <label>Full Name</label>
            <input
              type="text"
              placeholder="Enter your full name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setVerified(false);
                setOtpSent(false);
                setError("");
              }}
            />
          </div>

          <div className="signup-field">
            <label>Mobile Number</label>
            <div className="phone-input">
              <span>+91</span>
              <input
                type="tel"
                inputMode="numeric"
                placeholder="Enter 10-digit mobile number"
                maxLength={10}
                value={phone}
                onChange={(e) => {
                  setPhone(e.target.value.replace(/\D/g, "").slice(0, 10));
                  setVerified(false);
                  setOtpSent(false);
                  setOtp("");
                  setError("");
                }}
              />
            </div>
          </div>

          {!otpSent ? (
            <button
              type="button"
              className="signup-button"
              onClick={handleSendOTP}
            >
              Send OTP
            </button>
          ) : (
            <>
              <div className="signup-field">
                <label>Enter OTP</label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="Enter 4-digit OTP"
                  maxLength={4}
                  value={otp}
                  onChange={(e) => {
                    setOtp(e.target.value.replace(/\D/g, "").slice(0, 4));
                    setVerified(false);
                    setError("");
                  }}
                />
                <small>Demo OTP: 1234</small>
              </div>

              {!verified && (
                <button
                  type="button"
                  className="signup-button"
                  onClick={handleVerifyOTP}
                >
                  Verify OTP
                </button>
              )}

              {verified && (
                <div className="verified-message">
                  <ShieldCheck size={18} />
                  Mobile number verified
                </div>
              )}
            </>
          )}

          <label className="signup-consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            <span>
              I agree to the <a href="/terms">Terms and Conditions</a> and
              <a href="/privacy"> Privacy Policy</a>.
            </span>
          </label>

          {error && <p className="signup-error">{error}</p>}
          {message && <p className="signup-message">{message}</p>}

          <button
            type="submit"
            className="signup-button create-account-button"
            disabled={!verified}
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  );
}

export default Signup;
