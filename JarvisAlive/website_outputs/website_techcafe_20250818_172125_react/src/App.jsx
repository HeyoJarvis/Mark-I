import React from 'react'

function App() {
  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-container">
          <h1 className="logo">TechCafe</h1>
          <ul className="nav-links">
            <li><a href="#home">Home</a></li>
            <li><a href="#about">About</a></li>
            <li><a href="#services">Services</a></li>
            <li><a href="#contact">Contact</a></li>
          </ul>
        </div>
      </nav>

      <main>
        <section className="hero" id="home">
          <h1>Delicious Food at TechCafe</h1>
          <p>Made fresh daily with the finest ingredients</p>
          <div className="hero-buttons">
            <a href="#contact" className="btn primary">Order Now</a>
            <a href="#about" className="btn secondary">View Menu</a>
          </div>
        </section>

        <section className="features" id="services">
          <h2>Why Choose TechCafe</h2>
          <div className="features-grid">
          </div>
        </section>

        <section className="contact" id="contact">
          <h2>Get Started Today</h2>
          <p>Ready to experience what TechCafe can do for you?</p>
          <a href="#" className="btn primary">Contact Us</a>
        </section>
      </main>

      <footer>
        <p>&copy; 2024 TechCafe. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
