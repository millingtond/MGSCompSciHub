// frontend/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { AuthProvider } from './contexts/AuthContext.jsx'; // AuthProvider uses Firebase
// import './index.css'; // Main global styles can be imported in App.jsx or here

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider> {/* AuthProvider now uses Firebase logic */}
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
