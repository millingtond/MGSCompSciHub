// frontend/src/contexts/AuthContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import { 
  auth, 
  microsoftProvider, 
  signInWithPopup, 
  signInWithEmailAndPassword,
  signOut as firebaseSignOut, 
  onAuthStateChanged 
} from '../services/firebase';
import { useNavigate } from 'react-router-dom';
import apiClient from '../services/api'; 

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null); 
  const [firebaseIdToken, setFirebaseIdToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    setIsLoading(true);
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken(true); 
          console.log("Firebase ID Token (Frontend):", token); // <<< ADD THIS LINE
          if (token) {
  try {
    const payloadBase64 = token.split('.')[1];
    const decodedPayload = JSON.parse(atob(payloadBase64));
    console.log("Decoded Token Payload (Frontend):", decodedPayload);
    console.log("Token Expiry (Frontend):", new Date(decodedPayload.exp * 1000));
    console.log("Token Issued At (Frontend):", new Date(decodedPayload.iat * 1000));
  } catch (e) {
    console.error("Error decoding token payload:", e);
  }
}
          setFirebaseIdToken(token);
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          const sessionResponse = await apiClient.post('/auth/firebase/verify_session', { firebase_token: token });
          
          if (sessionResponse.data && sessionResponse.data.success) {
            setCurrentUser(sessionResponse.data.user); 
            // Navigate after successful backend sync and role determination
            if (sessionResponse.data.user.role === 'teacher') navigate('/teacher/dashboard', { replace: true });
            else if (sessionResponse.data.user.role === 'student') navigate('/student/dashboard', { replace: true });
            else navigate('/', { replace: true });
          } else {
            console.error("Backend session verification/sync failed:", sessionResponse.data.message);
            setAuthError(sessionResponse.data.message || "Backend sync failed.");
            await firebaseSignOut(auth); 
          }
        } catch (error) {
          console.error("Error during Firebase auth state processing or backend sync:", error);
          setAuthError(error.message || "Error processing login.");
          // Ensure logout if backend sync fails critically
          try { await firebaseSignOut(auth); } catch (e) { console.error("Error signing out of Firebase after sync failure", e); }
          setCurrentUser(null); setFirebaseIdToken(null); delete apiClient.defaults.headers.common['Authorization'];
        }
      } else {
        setCurrentUser(null); setFirebaseIdToken(null); delete apiClient.defaults.headers.common['Authorization'];
      }
      setIsLoading(false);
    });
    return () => unsubscribe();
  }, [navigate]); // Added navigate to dependency array

  const teacherMicrosoftLogin = async () => {
    setIsLoading(true); setAuthError(null);
    try {
      await signInWithPopup(auth, microsoftProvider);
      // onAuthStateChanged will handle the rest
    } catch (error) {
      console.error("Firebase Microsoft login error:", error);
      setAuthError(error.message || "Microsoft login failed.");
      setIsLoading(false);
    }
  };

  const teacherEmailLogin = async (email, password) => { // For temporary teacher email/password login
    setIsLoading(true); setAuthError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      // onAuthStateChanged will handle the rest
      return { success: true };
    } catch (error) {
      console.error("Firebase Teacher email/password login error:", error);
      setAuthError(error.message || "Teacher login failed.");
      setIsLoading(false);
      return { success: false, message: error.message };
    }
  };

  const studentLoginWithEmail = async (email, password) => {
    setIsLoading(true); setAuthError(null);
    try {
      await signInWithEmailAndPassword(auth, email, password);
      return { success: true };
    } catch (error) {
      console.error("Firebase Student email/password login error:", error);
      setAuthError(error.message || "Student login failed.");
      setIsLoading(false);
      return { success: false, message: error.message };
    }
  };
  
  const createStudentAccountByTeacher = async (studentCreationData) => {
    if (!currentUser || currentUser.role !== 'teacher' || !firebaseIdToken) {
      setAuthError("Unauthorized: Only teachers can create student accounts.");
      return { success: false, message: "Unauthorized: Only teachers can create student accounts." };
    }
    setIsLoading(true); setAuthError(null);
    try {
      const response = await apiClient.post('/api/teacher/create_firebase_student', studentCreationData);
      setIsLoading(false);
      return response.data; 
    } catch (error) {
      console.error("Error calling backend to create student Firebase account:", error);
      setAuthError(error.response?.data?.message || "Failed to create student account.");
      setIsLoading(false);
      return { success: false, message: error.response?.data?.message || "Failed to create student account." };
    }
  };

  const logout = async () => {
    setIsLoading(true); setAuthError(null);
    try {
      await firebaseSignOut(auth); 
    } catch (error) {
      console.error("Firebase logout error:", error);
      setAuthError(error.message || "Logout failed.");
    } finally {
      setCurrentUser(null); setFirebaseIdToken(null); delete apiClient.defaults.headers.common['Authorization'];
      navigate('/login');
      setIsLoading(false);
    }
  };
  
  const value = {
    currentUser, 
    firebaseIdToken,
    isLoading,
    teacherMicrosoftLogin,
    teacherEmailLogin, // Added for temporary teacher login
    studentLoginWithEmail,
    createStudentAccountByTeacher, 
    logout,
    authError, 
    clearAuthError: () => setAuthError(null) 
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
