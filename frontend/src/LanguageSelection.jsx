
import { useLanguage } from "./context/LanguageContext";
import "./App.css";

export default function LanguageSelection() {
  const { setLanguage } = useLanguage();

  return (
    <div className="language-screen">
      <div className="language-card">
        <h1>Welcome to BloodLink</h1>
        <p>Please select your preferred language</p>

        <button onClick={() => setLanguage("en")}>
          English
        </button>

        <button onClick={() => setLanguage("hi")}>
          हिन्दी
        </button>
      </div>
    </div>
  );
}
