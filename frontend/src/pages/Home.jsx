
import { Link } from "react-router-dom";
import "../App.css";

function Home() {
  return (
    <div className="app">

      {/* Navigation */}
      <header className="navbar">
        <Link to="/" className="brand">
          <span className="brand-icon">♥</span>
          <span>Blood<span className="brand-highlight">Link</span></span>
        </Link>

        <nav className="nav-links">
          <Link to="/">Home</Link>
          <a href="#how-it-works">How it works</a>
          <Link to="/donor">For Donors</Link>
          <a href="#about">About us</a>
        </nav>

        <div className="nav-actions">
          <Link to="/login" className="login-link">Log in</Link>
          <Link to="/signup" className="nav-button">Get Started</Link>
        </div>
      </header>

      {/* Hero Section */}
      <main>
        <section className="hero-section" id="home">
          <div className="hero-content">

            <div className="hero-badge">
              <span className="live-dot"></span>
              CONNECTING LIVES, SAVING LIVES
            </div>

            <h1>
              Every Drop Can
              <span> Save a Life.</span>
            </h1>

            <p className="hero-description">
              Find blood donors when every second matters.
              BloodLink connects people who need blood with
              potential donors nearby.
            </p>

            <div className="hero-buttons">
              <Link to="/receiver" className="primary-button">
                Request Blood <span>→</span>
              </Link>

              <Link to="/donor" className="secondary-button">
                Become a Donor
              </Link>
            </div>

            <div className="hero-note">
              <span>✦</span>
              Every connection brings hope.
            </div>
          </div>

          {/* Hero Visual */}
          <div className="hero-visual">
            <div className="visual-circle circle-one"></div>
            <div className="visual-circle circle-two"></div>

            <div className="blood-card">
              <div className="blood-symbol">♥</div>
              <p className="card-small-text">THE POWER OF GIVING</p>
              <h2>Be someone's<br />reason to smile.</h2>
              <p className="card-description">
                Your willingness to donate can make a difference.
              </p>
              <div className="card-footer">
                <span>❤️</span>
                <span>One donation. A new hope.</span>
              </div>
            </div>

            <div className="floating-card">
              <span className="floating-icon">+</span>
              <div>
                <strong>Help is closer</strong>
                <p>Connect with nearby donors</p>
              </div>
            </div>
          </div>
        </section>

        {/* Feature Section */}
        <section className="features-section" id="how-it-works">
          <div className="section-heading">
            <span className="section-label">HOW BLOODLINK WORKS</span>
            <h2>Making blood donation connections easier.</h2>
            <p>
              A simple platform designed to bring donors and receivers together.
            </p>
          </div>

          <div className="feature-grid">
            <article className="feature-card">
              <div className="feature-icon red-icon">♥</div>
              <h3>Register as a Donor</h3>
              <p>
                Create your donor profile and complete the pre-screening form.
              </p>
              <Link to="/donor">Join as donor →</Link>
            </article>

            <article className="feature-card">
              <div className="feature-icon pink-icon">⌕</div>
              <h3>Find Nearby Donors</h3>
              <p>
                Send a blood request and connect with compatible donors nearby.
              </p>
              <Link to="/receiver">Request blood →</Link>
            </article>

            <article className="feature-card">
              <div className="feature-icon green-icon">✓</div>
              <h3>Stay Connected</h3>
              <p>
                Follow request updates and stay informed throughout the process.
              </p>
              <Link to="/receiver">Explore platform →</Link>
            </article>
          </div>
        </section>

        {/* Call to Action */}
        <section className="cta-section" id="donors">
          <div>
            <span className="section-label">BE THE DIFFERENCE</span>
            <h2>Someone out there may need you.</h2>
            <p>
              Become part of a community that connects people through the
              power of blood donation.
            </p>
          </div>

          <Link to="/signup" className="cta-button">
            Get Started →
          </Link>
        </section>

        {/* Receiver Section */}
        <section className="receiver-section" id="receiver">
          <div>
            <span className="section-label">NEED BLOOD?</span>
            <h2>Get connected when it matters most.</h2>
            <p>
              Start a blood request and let BloodLink help connect you
              with potential donors.
            </p>
          </div>

          <Link to="/receiver" className="primary-button">
            Start a Request →
          </Link>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer" id="about">
        <Link to="/" className="brand footer-brand">
          <span className="brand-icon">♥</span>
          <span>Blood<span className="brand-highlight">Link</span></span>
        </Link>

        <p>Connecting lives, one donation at a time.</p>
        <span className="copyright">
          © 2026 BloodLink. All rights reserved.
        </span>
      </footer>

    </div>
  );
}

export default Home;
