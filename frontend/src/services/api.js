// frontend/src/services/api.js
import axios from 'axios';

// The base URL for your Flask backend
// Make sure this matches where your backend is running (usually http://localhost:5000)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Important for sending cookies (like session cookies)
});

// Interceptors can be added here for global error handling or adding auth tokens to headers

// --- Authentication Endpoints ---
export const studentLogin = (credentials) => apiClient.post('/auth/student/login', credentials);
export const teacherMockLogin = (credentials) => apiClient.post('/auth/teacher/mock_login', credentials);
// Real Microsoft login will be a redirect, but callback handling might involve an API call
export const checkSession = () => apiClient.get('/auth/check_session');
export const logoutUser = () => apiClient.post('/auth/logout');

// --- Teacher Endpoints ---
export const createClass = (classData) => apiClient.post('/api/teacher/classes', classData);
export const getTeacherClasses = () => apiClient.get('/api/teacher/classes');
export const getClassDetails = (classId) => apiClient.get(`/api/teacher/classes/${classId}`);
export const generateStudents = (classId, numStudents) => apiClient.post(`/api/teacher/classes/${classId}/generate_students`, { num_students: numStudents });
export const assignWorksheetToClass = (classId, worksheetId, dueDate = null) => {
  const payload = { worksheet_id: worksheetId };
  if (dueDate) payload.due_date = dueDate;
  return apiClient.post(`/api/teacher/classes/${classId}/assign_worksheet`, payload);
};
export const getAssignmentProgressForClass = (classId, assignmentId) => apiClient.get(`/api/teacher/classes/<span class="math-inline">\{classId\}/assignments/</span>{assignmentId}/progress`);


// --- Student Endpoints ---
export const getStudentAssignments = () => apiClient.get('/api/student/assignments');
export const getStudentProgressForAssignment = (assignmentId) => apiClient.get(`/api/student/assignments/${assignmentId}/progress`);
export const saveStudentProgress = (assignmentId, progressData) => apiClient.post(`/api/student/assignments/${assignmentId}/progress`, progressData);

// --- Worksheet Endpoints ---
export const listAllWorksheets = () => apiClient.get('/api/worksheets'); // For teachers to choose from

export default apiClient; // Export the configured instance if you want to use it directly elsewhere too