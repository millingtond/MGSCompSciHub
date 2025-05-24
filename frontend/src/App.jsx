// frontend/src/App.jsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import './assets/css/main.css';
import { useAuth } from './contexts/AuthContext.jsx';

// Import Page Components
import HomePage from './pages/HomePage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import TeacherDashboardPage from './pages/TeacherDashboardPage.jsx';
import StudentDashboardPage from './pages/StudentDashboardPage.jsx';
import WorksheetDisplayPage from './pages/WorksheetDisplayPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';
import AuthCallbackPage from './pages/AuthCallbackPage.jsx';

// Import Common Components
import Navbar from './components/common/Navbar.jsx'; // Import the Navbar

const LoadingSpinner = () => <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontSize: '1.2rem' }}>Loading application state...</div>;

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { currentUser, isLoading } = useAuth();

  if (isLoading) { // Wait for auth state to resolve
    return <LoadingSpinner />;
  }

  if (!currentUser) { // If no user, redirect to login
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(currentUser.role)) { // If role not allowed
    return <Navigate to="/" replace />; // Or a specific "Access Denied" page
  }

  return children; // User is authenticated and has the correct role
};

function App() {
  const { currentUser, isLoading: isAuthLoading } = useAuth();

  // This initial loading check is important
  if (isAuthLoading) {
     const isAuthCallbackRoute = window.location.pathname.startsWith('/auth/success') || window.location.pathname.startsWith('/auth/failure');
     if (!isAuthCallbackRoute) { // Don't show main loader on auth callback routes as they have their own logic
        return <LoadingSpinner />;
     }
  }

  return (
    <div className="App">
      <Navbar /> {/* Use the Navbar component here */}
      <main style={{ padding: '1rem' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={
            currentUser ? ( // If already logged in, redirect from /login
              currentUser.role === 'teacher' ? <Navigate to="/teacher/dashboard" replace /> :
              currentUser.role === 'student' ? <Navigate to="/student/dashboard" replace /> :
              <Navigate to="/" replace />
            ) : (
              <LoginPage />
            )
          } />
          <Route path="/auth/success" element={<AuthCallbackPage />} />
          <Route path="/auth/failure" element={<AuthCallbackPage error={true} />} />

          <Route
            path="/teacher/dashboard"
            element={
              <ProtectedRoute allowedRoles={['teacher']}>
                <TeacherDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute allowedRoles={['student']}>
                <StudentDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/worksheet/:worksheetId"
            element={
              <ProtectedRoute allowedRoles={['student', 'teacher']}>
                <WorksheetDisplayPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
