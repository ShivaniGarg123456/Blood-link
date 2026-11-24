
import { Link, useNavigate } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext";

function Navbar() {
  const { language, setLanguage } = useLanguage();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        BloodLink
      </Link>

      <div className="nav-links">
        <Link to="/">
          {language === "hi" ? "होम" : "Home"}
        </Link>

        <Link to="/donor">
          {language === "hi" ? "डोनर" : "Donor"}
        </Link>

        <Link to="/receiver">
          {language === "hi" ? "रिसीवर" : "Receiver"}
        </Link>

        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          aria-label="Select language"
        >
          <option value="en">English</option>
          <option value="hi">हिन्दी</option>
        </select>

        <button type="button" onClick={handleLogout}>
          {language === "hi" ? "लॉग आउट" : "Logout"}
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
