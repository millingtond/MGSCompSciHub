// frontend/src/pages/LoginPage.jsx
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext.jsx';
import { Navigate, useLocation } from 'react-router-dom';

function LoginPage() {
  const [studentEmail, setStudentEmail] = useState(''); 
  const [studentPassword, setStudentPassword] = useState(''); 
  const [teacherEmail, setTeacherEmail] = useState(''); // For temporary teacher email login
  const [teacherPassword, setTeacherPassword] = useState(''); // For temporary teacher email login
  
  const [uiError, setUiError] = useState(''); // For displaying errors directly on this page
  const [studentLoading, setStudentLoading] = useState(false);
  const [teacherLoading, setTeacherLoading] = useState(false);
  const [teacherTempLoading, setTeacherTempLoading] = useState(false);

  const { 
    teacherMicrosoftLogin, 
    studentLoginWithEmail, 
    teacherEmailLogin, // New method for temporary teacher login
    currentUser, 
    isLoading: isAuthLoading, 
    authError, 
    clearAuthError 
  } = useAuth();
  
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const oauthCallbackError = queryParams.get('error_message');

  useEffect(() => {
    // Clear any global auth errors when the component mounts or error changes
    if (authError || oauthCallbackError) {
        setUiError(authError || oauthCallbackError); // Show global error locally
        clearAuthError(); // Clear it from context after displaying
    }
  }, [authError, oauthCallbackError, clearAuthError]);


  const handleStudentSubmit = async (e) => {
    e.preventDefault();
    setUiError(''); setStudentLoading(true);
    const result = await studentLoginWithEmail(studentEmail, studentPassword);
    if (!result.success) {
      setUiError(result.message || 'Student login failed. Please check credentials.');
    }
    setStudentLoading(false);
  };

  const handleTeacherTempSubmit = async (e) => { // For temporary teacher email/password
    e.preventDefault();
    setUiError(''); setTeacherTempLoading(true);
    const result = await teacherEmailLogin(teacherEmail, teacherPassword);
    if (!result.success) {
      setUiError(result.message || 'Temporary Teacher login failed.');
    }
    setTeacherTempLoading(false);
  };

  const handleTeacherMicrosoftLoginAttempt = async () => {
    setUiError(''); setTeacherLoading(true);
    await teacherMicrosoftLogin(); 
    // setLoadingTeacher(false); // onAuthStateChanged will manage loading state
  };

  if (isAuthLoading && !currentUser) { 
    return <div style={{ textAlign: 'center', padding: '2rem', fontSize: '1.2em' }}>Loading authentication state...</div>;
  }

  if (currentUser) { 
    const redirectTo = currentUser.role === 'teacher' ? '/teacher/dashboard' :
                       currentUser.role === 'student' ? '/student/dashboard' : '/';
    return <Navigate to={redirectTo} replace />;
  }

  return (
    <div style={{ maxWidth: '500px', margin: '3rem auto', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', borderRadius: '8px', backgroundColor: '#fff' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: '#333' }}>MGSCompSci Hub Login</h2>
      
      {uiError && (
        <p style={{ color: 'red', border: '1px solid #f5c6cb', padding: '0.75rem', marginBottom: '1rem', borderRadius: '4px', backgroundColor: '#f8d7da' }}>
          {uiError.replace(/_/g, ' ')}
        </p>
      )}

      {/* Student Login Form */}
      <form onSubmit={handleStudentSubmit} style={{ marginBottom: '2rem' }}>
        <h4 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Student Login</h4>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="student-email" style={{ display: 'block', marginBottom: '0.25rem' }}>Generated Email:</label>
          <input type="email" id="student-email" value={studentEmail} onChange={(e) => setStudentEmail(e.target.value)} required 
                 placeholder="e.g., student123@your-app-domain.com"
                 style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="student-password" style={{ display: 'block', marginBottom: '0.25rem' }}>Password:</label>
          <input type="password" id="student-password" value={studentPassword} onChange={(e) => setStudentPassword(e.target.value)} required
                 style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }} />
        </div>
        <button type="submit" disabled={studentLoading} 
                style={{ padding: '0.6rem 1.2rem', cursor: 'pointer', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', width: '100%' }}>
          {studentLoading ? 'Logging in...' : 'Login as Student'}
        </button>
      </form>

      <hr style={{margin: '2rem 0'}} />

      {/* Temporary Teacher Email/Password Login Form */}
      <form onSubmit={handleTeacherTempSubmit} style={{ marginBottom: '2rem' }}>
        <h4 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Teacher Login (Temporary Email/Password)</h4>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="teacher-email" style={{ display: 'block', marginBottom: '0.25rem' }}>Teacher Email:</label>
          <input type="email" id="teacher-email" value={teacherEmail} onChange={(e) => setTeacherEmail(e.target.value)} required 
                 placeholder="e.g., teacher.admin@yourschoolapp.com"
                 style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="teacher-password" style={{ display: 'block', marginBottom: '0.25rem' }}>Password:</label>
          <input type="password" id="teacher-password" value={teacherPassword} onChange={(e) => setTeacherPassword(e.target.value)} required
                 style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }} />
        </div>
        <button type="submit" disabled={teacherTempLoading} 
                style={{ padding: '0.6rem 1.2rem', cursor: 'pointer', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', width: '100%' }}>
          {teacherTempLoading ? 'Logging in...' : 'Login as Teacher (Temp)'}
        </button>
      </form>
      
      <div style={{ textAlign: 'center', borderTop: '1px solid #eee', paddingTop: '1.5rem' }}>
        <p style={{marginBottom: '0.5rem', color: '#555'}}>For School Staff (Official):</p>
        <button onClick={handleTeacherMicrosoftLoginAttempt} disabled={teacherLoading}
                style={{ padding: '0.7rem 1.5rem', cursor: 'pointer', backgroundColor: '#0078D4', color: 'white', border: 'none', borderRadius: '4px', fontSize: '1rem' }}>
          {teacherLoading ? 'Redirecting to Microsoft...' : 'Login with Microsoft'}
        </button>
      </div>
    </div>
  );
}
export default LoginPage;
