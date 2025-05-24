// frontend/src/components/auth/TeacherMockLoginForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext.jsx';

function TeacherMockLoginForm() {
  const [username, setUsername] = useState('mockteacher@mgs.com'); // Pre-fill for dev
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const result = await login('teacher_mock', { username, password });
    if (!result.success) {
      setError(result.message || 'Failed to log in mock teacher.');
    }
    // Navigation is handled by AuthContext
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: '5px', backgroundColor: '#f9f9f9' }}>
      <h4 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Teacher Mock Login (Dev Only)</h4>
      {error && <p style={{ color: 'red', backgroundColor: '#ffebee', border: '1px solid #ffcdd2', padding: '0.5rem', borderRadius: '3px' }}>{error}</p>}
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="teacher-mock-username" style={{ display: 'block', marginBottom: '0.25rem' }}>Username (Email):</label>
        <input
          type="email"
          id="teacher-mock-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="teacher-mock-password" style={{ display: 'block', marginBottom: '0.25rem' }}>Password:</label>
        <input
          type="password"
          id="teacher-mock-password"
          placeholder="Enter mock teacher password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }}
        />
      </div>
      <button 
        type="submit" 
        disabled={loading} 
        style={{ 
          padding: '0.6rem 1.2rem', 
          cursor: 'pointer', 
          backgroundColor: '#28a745', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px' 
        }}
      >
        {loading ? 'Logging in...' : 'Login as Mock Teacher'}
      </button>
    </form>
  );
}

export default TeacherMockLoginForm;
