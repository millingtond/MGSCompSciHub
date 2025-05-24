// frontend/src/pages/HomePage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

function HomePage() {
  return (
    <div>
      <h2>Home Page</h2>
      <p>This is the public landing page for MGSCompSci Hub.</p>
      <p><Link to="/login">Login</Link> to access your dashboard and worksheets.</p>
    </div>
  );
}
export default HomePage;
