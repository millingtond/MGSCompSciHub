// frontend/src/components/auth/StudentLoginForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext.jsx';

function StudentLoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const result = await login('student', { username, password });
    if (!result.success) {
      setError(result.message || 'Failed to log in student.');
    }
    // Navigation is handled by AuthContext on successful login
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '5px', backgroundColor: '#f9f9f9' }}>
      <h4 style={{ marginTop: 0, borderBottom: '1px solid #eee', paddingBottom: '0.5rem' }}>Student Login</h4>
      {error && <p style={{ color: 'red', backgroundColor: '#ffebee', border: '1px solid #ffcdd2', padding: '0.5rem', borderRadius: '3px' }}>{error}</p>}
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="student-username" style={{ display: 'block', marginBottom: '0.25rem' }}>Username:</label>
        <input
          type="text"
          id="student-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          style={{ width: '100%', padding: '0.5rem', boxSizing: 'border-box', border: '1px solid #ccc', borderRadius: '3px' }}
        />
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="student-password" style={{ display: 'block', marginBottom: '0.25rem' }}>Password:</label>
        <input
          type="password"
          id="student-password"
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
          backgroundColor: '#007bff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px' 
        }}
      >
        {loading ? 'Logging in...' : 'Login as Student'}
      </button>
    </form>
  );
}

export default StudentLoginForm;
