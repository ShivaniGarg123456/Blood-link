
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Donor from "./pages/Donor";
import Receiver from "./pages/Receiver";
import Signup from "./Signup";
import Login from "./Login";

import { useLanguage } from "./context/LanguageContext";
import LanguageSelection from "./LanguageSelection";

import "./App.css";

function App() {
  const { language } = useLanguage();

  if (!language) {
    return <LanguageSelection />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/donor" element={<Donor />} />
        <Route path="/receiver" element={<Receiver />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
