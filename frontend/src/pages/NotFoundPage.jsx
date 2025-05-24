// frontend/src/pages/NotFoundPage.jsx
import React from 'react';
import { Link } from 'react-router-dom';

function NotFoundPage() {
  return (
    <div>
      <h2>404 - Page Not Found</h2>
      <p>Sorry, the page you are looking for does not exist.</p>
      <p><Link to="/">Go back to the Home Page</Link></p>
    </div>
  );
}
export default NotFoundPage;
