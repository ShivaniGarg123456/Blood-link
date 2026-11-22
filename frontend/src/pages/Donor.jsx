
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

function Donor() {
  return (
    <>
      <Navbar />

      <div className="page-container">
        <h1>Become a Blood Donor</h1>
        <p>
          Your willingness to donate can bring hope to someone in need.
        </p>

        <div className="donor-card">
          <h2>Donor Registration</h2>

          <form>
            <label>Full Name</label>
            <input type="text" placeholder="Enter your full name" />

            <label>Age</label>
            <input type="number" placeholder="Enter your age" />

            <label>Blood Group</label>
            <select defaultValue="">
              <option value="" disabled>Select blood group</option>
              <option>A+</option>
              <option>A-</option>
              <option>B+</option>
              <option>B-</option>
              <option>AB+</option>
              <option>AB-</option>
              <option>O+</option>
              <option>O-</option>
            </select>

            <label>City</label>
            <input type="text" placeholder="Enter your city" />

            <button type="button">Continue</button>
          </form>
        </div>
      </div>

      <Footer />
    </>
  );
}

export default Donor;
