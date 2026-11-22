
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

function Receiver() {
  return (
    <>
      <Navbar />

      <div className="page-container">
        <h1>Request Blood</h1>
        <p>
          Find the blood support you need. Every connection can save a life.
        </p>

        <div className="donor-card">
          <h2>Blood Request Form</h2>

          <form>
            <label>Patient Name</label>
            <input type="text" placeholder="Enter patient name" />

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

            <label>Blood Component</label>
            <select defaultValue="">
              <option value="" disabled>Select component</option>
              <option>Whole Blood</option>
              <option>Red Blood Cells</option>
            </select>

            <label>Units Required</label>
            <input type="number" placeholder="Enter units required" />

            <label>Hospital Name</label>
            <input type="text" placeholder="Enter hospital name" />

            <label>Urgency</label>
            <select defaultValue="">
              <option value="" disabled>Select urgency</option>
              <option>Normal</option>
              <option>Urgent</option>
              <option>Emergency</option>
            </select>

            <button type="button">Submit Request</button>
          </form>
        </div>
      </div>

      <Footer />
    </>
  );
}

export default Receiver;
