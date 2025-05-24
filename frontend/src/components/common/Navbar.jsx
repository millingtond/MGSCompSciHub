// frontend/src/components/common/Navbar.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.jsx';

function Navbar() {
  const { currentUser, logout, isLoading } = useAuth(); // currentUser is now the appUser object from AuthContext

  return (
    <nav style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '1rem 2rem',
      backgroundColor: '#f8f9fa', // Lighter grey
      borderBottom: '1px solid #dee2e6',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
    }}>
      <div className="nav-brand">
        <Link to="/" style={{ fontSize: '1.5rem', textDecoration: 'none', color: '#343a40', fontWeight: 'bold' }}>
          MGSCompSci Hub
        </Link>
      </div>

      <div className="nav-links-auth" style={{ display: 'flex', alignItems: 'center' }}>
        {isLoading ? (
          <span style={{ fontStyle: 'italic', color: '#6c757d' }}>Authenticating...</span>
        ) : currentUser ? (
          <>
            {currentUser.role === 'teacher' && (
              <Link to="/teacher/dashboard" style={{ marginRight: '20px', textDecoration: 'none', color: '#495057', fontWeight: 500 }}>
                Teacher Dashboard
              </Link>
            )}
            {currentUser.role === 'student' && (
              <Link to="/student/dashboard" style={{ marginRight: '20px', textDecoration: 'none', color: '#495057', fontWeight: 500 }}>
                Student Dashboard
              </Link>
            )}
            <span style={{ marginRight: '20px', color: '#495057' }}>
              Welcome, {currentUser.displayName || currentUser.email || currentUser.username}! 
              {currentUser.role && ` (${currentUser.role})`}
            </span>
            <button
              onClick={logout}
              style={{
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                backgroundColor: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '0.25rem',
                fontSize: '0.9rem',
                fontWeight: 500
              }}
            >
              Logout
            </button>
          </>
        ) : (
          <Link 
            to="/login" 
            style={{ 
              padding: '0.5rem 1rem',
              textDecoration: 'none', 
              color: '#fff', 
              backgroundColor: '#007bff', 
              borderRadius: '0.25rem',
              fontWeight: 500
            }}
          >
            Login
          </Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
