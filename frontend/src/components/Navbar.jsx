
import { Link } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        BloodLink
      </Link>

      <div className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/donor">Donor</Link>
        <Link to="/receiver">Receiver</Link>
      </div>
    </nav>
  );
}

export default Navbar;
