// frontend/src/pages/AuthCallbackPage.jsx
import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext.jsx';
import { checkSession } from '../services/api.js'; // Import checkSession

function AuthCallbackPage({ error }) {
  const navigate = useNavigate();
  const location = useLocation();
  // const { refreshUser } = useAuth(); // Assuming you add refreshUser to AuthContext

  useEffect(() => {
    const handleAuthCallback = async () => {
      if (error) {
        const queryParams = new URLSearchParams(location.search);
        const errorMessage = queryParams.get('error_message') || "Authentication failed.";
        console.error("OAuth Error:", errorMessage);
        // Optionally display the error message to the user
        // For now, just redirect to login with a delay or a message
        setTimeout(() => navigate('/login?error=' + encodeURIComponent(errorMessage)), 1000);
        return;
      }

      // If successful, the backend session should be set.
      // We need to re-check the session on the frontend to update AuthContext.
      try {
        const response = await checkSession(); // Re-verify session
        if (response.data && response.data.isLoggedIn) {
          // AuthContext's useEffect will pick up the change if currentUser is updated
          // Or, if you have a refreshUser function in AuthContext:
          // await refreshUser(); 
          
          // For now, we rely on AuthContext's own useEffect to update after this.
          // A more direct update might be needed if AuthContext's useEffect doesn't re-run as expected here.
          // The simplest way is to navigate, and AuthProvider's checkSession will run on mount.
          
          if (response.data.user.role === 'teacher') {
            navigate('/teacher/dashboard', { replace: true });
          } else {
            // Should not happen for MS OAuth, but as a fallback
            navigate('/', { replace: true });
          }
        } else {
          navigate('/login?error=session_not_found', { replace: true });
        }
      } catch (e) {
        console.error("Error processing auth callback:", e);
        navigate('/login?error=callback_processing_failed', { replace: true });
      }
    };

    handleAuthCallback();
  }, [navigate, error, location.search]);

  if (error) {
    const queryParams = new URLSearchParams(location.search);
    const errorMessage = queryParams.get('error_message') || "Authentication failed.";
    return <div>Error during authentication: {errorMessage}. Redirecting...</div>;
  }

  return <div>Processing authentication...</div>;
}

export default AuthCallbackPage;
