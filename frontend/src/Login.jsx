
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Droplet,
  ShieldCheck,
  HeartPulse,
  ArrowRight,
  Phone,
  LockKeyhole,
  Users,
  Heart,
} from "lucide-react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function readResponse(response) {
  const text = await response.text();

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function Login() {
  const navigate = useNavigate();

  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const sendOTP = async () => {
    setError("");
    setMessage("");

    if (!/^[6-9]\d{9}$/.test(phone)) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/otp/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ phone }),
      });

      const data = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          data?.detail || data?.message || "Could not send OTP."
        );
      }

      setOtpSent(true);
      setMessage(
        data?.demo_hint || data?.message || "OTP sent successfully."
      );
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!/^\d{4}$/.test(otp)) {
      setError("Please enter a valid 4-digit OTP.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/auth/otp/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ phone, otp }),
      });

      const data = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          data?.detail || data?.message || "OTP verification failed."
        );
      }

      const token =
        typeof data === "string"
          ? data
          : data?.access_token || data?.token || data?.jwt;

      if (!token) {
        throw new Error(
          "JWT token was not received. Please check the backend response."
        );
      }

      localStorage.setItem("token", token);
      localStorage.setItem("userPhone", phone);

      navigate("/");
    } catch (err) {
      setError(err.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bl-login-page">
      <div className="bl-login-wrapper">

        <section className="bl-login-visual">
          <div className="bl-brand">
            <div className="bl-brand-icon">
              <Droplet size={27} fill="white" />
            </div>
            <span>Blood<span>Link</span></span>
          </div>

          <div className="bl-visual-content">
            <span className="bl-eyebrow">ONE DONATION. MANY LIVES.</span>

            <h1>
              Be someone's
              <br />
              <span>reason to live.</span>
            </h1>

            <p>
              Connect with people who need you. Your small step
              can make a life-changing difference.
            </p>

            <div className="bl-heart-illustration">
              <div className="bl-circle bl-circle-one"></div>
              <div className="bl-circle bl-circle-two"></div>

              <div className="bl-main-heart">
                <HeartPulse size={105} strokeWidth={1.3} />
              </div>

              <div className="bl-floating-icon bl-float-one">
                <Droplet size={24} fill="#e63946" />
              </div>

              <div className="bl-floating-icon bl-float-two">
                <Heart size={23} fill="#e63946" />
              </div>
            </div>

            <div className="bl-impact">
              <div className="bl-impact-item">
                <Users size={21} />
                <div>
                  <strong>One Community</strong>
                  <small>United to save lives</small>
                </div>
              </div>

              <div className="bl-impact-item">
                <HeartPulse size={21} />
                <div>
                  <strong>One Mission</strong>
                  <small>Making help accessible</small>
                </div>
              </div>
            </div>
          </div>

          <div className="bl-visual-footer">
            Every drop counts. Every life matters.
          </div>
        </section>

        <section className="bl-login-form-side">
          <div className="bl-mobile-brand">
            <Droplet size={25} fill="#e63946" color="#e63946" />
            <strong>Blood<span>Link</span></strong>
          </div>

          <div className="bl-login-card">
            <div className="bl-form-icon">
              <LockKeyhole size={25} />
            </div>

            <span className="bl-welcome-label">WELCOME BACK</span>

            <h2>Login to your account</h2>

            <p className="bl-form-description">
              Enter your mobile number to securely access your BloodLink account.
            </p>

            <form onSubmit={handleLogin}>
              <label className="bl-input-label">
                Mobile Number
              </label>

              <div className="bl-input-box">
                <span className="bl-country-code">+91</span>

                <input
                  type="tel"
                  inputMode="numeric"
                  placeholder="Enter 10-digit number"
                  value={phone}
                  maxLength={10}
                  disabled={otpSent}
                  onChange={(e) => {
                    setPhone(
                      e.target.value.replace(/\D/g, "").slice(0, 10)
                    );
                    setError("");
                    setMessage("");
                  }}
                />

                <Phone size={18} className="bl-input-icon" />
              </div>

              {!otpSent ? (
                <button
                  type="button"
                  className="bl-primary-button"
                  onClick={sendOTP}
                  disabled={loading}
                >
                  {loading ? "Sending OTP..." : "Send OTP"}
                  {!loading && <ArrowRight size={19} />}
                </button>
              ) : (
                <>
                  <div className="bl-otp-heading">
                    <label className="bl-input-label">Enter OTP</label>
                    <button
                      type="button"
                      className="bl-text-button"
                      onClick={() => {
                        setOtpSent(false);
                        setOtp("");
                        setError("");
                        setMessage("");
                      }}
                      disabled={loading}
                    >
                      Change number
                    </button>
                  </div>

                  <div className="bl-input-box">
                    <LockKeyhole size={18} className="bl-input-icon" />

                    <input
                      type="text"
                      inputMode="numeric"
                      placeholder="Enter 4-digit OTP"
                      value={otp}
                      maxLength={4}
                      onChange={(e) => {
                        setOtp(
                          e.target.value.replace(/\D/g, "").slice(0, 4)
                        );
                        setError("");
                      }}
                    />
                  </div>

                  <button
                    type="submit"
                    className="bl-primary-button"
                    disabled={loading}
                  >
                    {loading ? "Verifying..." : "Login Securely"}
                    {!loading && <ArrowRight size={19} />}
                  </button>
                </>
              )}
            </form>

            {error && (
              <div className="bl-alert bl-error">
                {error}
              </div>
            )}

            {message && (
              <div className="bl-alert bl-success">
                {message}
              </div>
            )}

            <div className="bl-security-note">
              <ShieldCheck size={19} />
              <span>Your information is protected and secure.</span>
            </div>

            <div className="bl-signup-link">
              Don't have an account?
              <Link to="/signup"> Create an account</Link>
            </div>
          </div>

          <div className="bl-bottom-note">
            © BloodLink · Connecting donors with those in need
          </div>
        </section>

      </div>

      <style>{`
        .bl-login-page {
          min-height: 100vh;
          padding: 35px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f6fa;
          font-family: inherit;
        }

        .bl-login-wrapper {
          width: 100%;
          max-width: 1120px;
          min-height: 680px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          background: white;
          border-radius: 24px;
          overflow: hidden;
          box-shadow: 0 18px 65px rgba(30, 30, 50, 0.10);
        }

        .bl-login-visual {
          background: linear-gradient(145deg, #b91f32, #e63946 60%, #f15b65);
          color: white;
          padding: 43px 48px 28px;
          display: flex;
          flex-direction: column;
          position: relative;
          overflow: hidden;
        }

        .bl-brand {
          display: flex;
          align-items: center;
          gap: 11px;
          font-size: 25px;
          font-weight: 800;
        }

        .bl-brand > span > span,
        .bl-mobile-brand span {
          color: #ffd9dc;
        }

        .bl-brand-icon {
          width: 43px;
          height: 43px;
          border-radius: 13px;
          display: grid;
          place-items: center;
          background: rgba(255,255,255,0.2);
        }

        .bl-visual-content {
          margin-top: 66px;
        }

        .bl-eyebrow {
          font-size: 11px;
          letter-spacing: 2px;
          font-weight: 800;
          color: #ffe1e3;
        }

        .bl-visual-content h1 {
          font-size: clamp(34px, 4vw, 47px);
          line-height: 1.15;
          margin: 17px 0;
          color: white;
          font-weight: 800;
        }

        .bl-visual-content h1 span {
          color: #ffd6d9;
        }

        .bl-visual-content > p {
          max-width: 370px;
          line-height: 1.8;
          font-size: 14px;
          color: #ffebed;
        }

        .bl-heart-illustration {
          height: 205px;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .bl-circle {
          position: absolute;
          border: 1px solid rgba(255,255,255,0.2);
          border-radius: 50%;
        }

        .bl-circle-one {
          width: 180px;
          height: 180px;
        }

        .bl-circle-two {
          width: 135px;
          height: 135px;
        }

        .bl-main-heart {
          width: 115px;
          height: 115px;
          border-radius: 32px;
          display: grid;
          place-items: center;
          background: rgba(255,255,255,0.16);
          backdrop-filter: blur(8px);
        }

        .bl-floating-icon {
          position: absolute;
          width: 47px;
          height: 47px;
          border-radius: 15px;
          background: white;
          color: #e63946;
          display: grid;
          place-items: center;
          box-shadow: 0 8px 20px rgba(80,0,0,0.12);
        }

        .bl-float-one {
          top: 20px;
          right: 20%;
        }

        .bl-float-two {
          bottom: 18px;
          left: 20%;
        }

        .bl-impact {
          display: flex;
          gap: 28px;
          margin-top: 10px;
        }

        .bl-impact-item {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .bl-impact-item div {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .bl-impact-item strong {
          font-size: 12px;
        }

        .bl-impact-item small {
          font-size: 10px;
          color: #ffe1e3;
        }

        .bl-visual-footer {
          margin-top: auto;
          padding-top: 28px;
          font-size: 12px;
          color: #ffe1e3;
        }

        .bl-login-form-side {
          padding: 45px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          position: relative;
        }

        .bl-login-card {
          width: 100%;
          max-width: 390px;
          margin: auto;
        }

        .bl-form-icon {
          width: 53px;
          height: 53px;
          border-radius: 17px;
          display: grid;
          place-items: center;
          color: #e63946;
          background: #fff0f1;
          margin-bottom: 25px;
        }

        .bl-welcome-label {
          color: #e63946;
          font-size: 11px;
          font-weight: 800;
          letter-spacing: 2px;
        }

        .bl-login-card h2 {
          font-size: 29px;
          line-height: 1.3;
          color: #202638;
          margin: 10px 0;
        }

        .bl-form-description {
          color: #7c8290;
          font-size: 13px;
          line-height: 1.7;
          margin-bottom: 32px;
        }

        .bl-input-label {
          display: block;
          font-size: 13px;
          font-weight: 700;
          color: #343a49;
          margin-bottom: 10px;
        }

        .bl-input-box {
          height: 55px;
          display: flex;
          align-items: center;
          border: 1px solid #e5e7ed;
          border-radius: 11px;
          padding: 0 14px;
          gap: 12px;
          margin-bottom: 22px;
          transition: border-color .2s, box-shadow .2s;
        }

        .bl-input-box:focus-within {
          border-color: #e63946;
          box-shadow: 0 0 0 3px rgba(230,57,70,0.09);
        }

        .bl-input-box input {
          width: 100%;
          border: none !important;
          outline: none !important;
          background: transparent !important;
          box-shadow: none !important;
          font-size: 14px;
          color: #252a38;
          min-width: 0;
        }

        .bl-input-box input:disabled {
          opacity: .65;
        }

        .bl-country-code {
          color: #343a49;
          font-size: 13px;
          font-weight: 700;
          padding-right: 12px;
          border-right: 1px solid #e5e7ed;
        }

        .bl-input-icon {
          color: #a0a5b1;
          flex-shrink: 0;
        }

        .bl-primary-button {
          width: 100%;
          height: 55px;
          border: none;
          border-radius: 11px;
          background: linear-gradient(100deg, #d9273c, #ef4b59);
          color: white;
          font-size: 14px;
          font-weight: 750;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 12px;
          cursor: pointer;
          box-shadow: 0 8px 18px rgba(217,39,60,0.2);
          transition: transform .2s, box-shadow .2s;
        }

        .bl-primary-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 11px 23px rgba(217,39,60,0.28);
        }

        .bl-primary-button:disabled {
          opacity: .65;
          cursor: not-allowed;
        }

        .bl-otp-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .bl-text-button {
          border: none;
          background: none;
          color: #e63946;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
          margin-bottom: 10px;
        }

        .bl-alert {
          padding: 12px 14px;
          border-radius: 9px;
          margin-top: 17px;
          font-size: 12px;
          line-height: 1.6;
          overflow-wrap: anywhere;
        }

        .bl-error {
          color: #b42332;
          background: #fff0f1;
          border: 1px solid #ffd7db;
        }

        .bl-success {
          color: #18794e;
          background: #eaf8f0;
          border: 1px solid #c9eed9;
        }

        .bl-security-note {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          color: #777f8e;
          font-size: 11px;
          margin-top: 30px;
        }

        .bl-security-note svg {
          color: #26996c;
        }

        .bl-signup-link {
          text-align: center;
          margin-top: 25px;
          color: #777f8e;
          font-size: 12px;
        }

        .bl-signup-link a {
          color: #e63946;
          font-weight: 800;
          text-decoration: none;
        }

        .bl-signup-link a:hover {
          text-decoration: underline;
        }

        .bl-bottom-note {
          text-align: center;
          font-size: 10px;
          color: #a0a5b1;
          margin-top: 30px;
        }

        .bl-mobile-brand {
          display: none;
        }

        @media (max-width: 800px) {
          .bl-login-page {
            padding: 18px;
          }

          .bl-login-wrapper {
            grid-template-columns: 1fr;
            max-width: 520px;
            min-height: auto;
          }

          .bl-login-visual {
            display: none;
          }

          .bl-login-form-side {
            padding: 35px 25px;
            min-height: 620px;
          }

          .bl-mobile-brand {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 9px;
            font-size: 23px;
            color: #202638;
            margin-bottom: 40px;
          }

          .bl-mobile-brand span {
            color: #e63946;
          }

          .bl-login-card h2 {
            font-size: 26px;
          }
        }

        @media (max-width: 420px) {
          .bl-login-page {
            padding: 10px;
          }

          .bl-login-form-side {
            padding: 28px 19px;
          }
        }
      `}</style>
    </div>
  );
}

export default Login;
