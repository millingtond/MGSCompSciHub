// frontend/src/pages/TeacherDashboardPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { 
  getTeacherClasses, 
  createClass, 
  listAllWorksheets, 
  assignWorksheetToClass, 
  getClassDetails 
} from '../services/api'; 
import { useAuth } from '../contexts/AuthContext'; 

// Modal component for displaying credentials
const CredentialsDisplayModal = ({ credentials, onClose }) => {
  console.log("[MODAL LOG] CredentialsDisplayModal received credentials:", credentials); 
  if (!credentials || credentials.length === 0) {
    console.log("[MODAL LOG] CredentialsDisplayModal: No credentials or empty, returning null."); 
    return null;
  }

  const credentialsString = credentials.map(
    cred => `Username: ${cred.app_username}\nLogin Email: ${cred.firebase_login_email}\nPassword: ${cred.initial_password}`
  ).join('\n\n');

  const handleCopyToClipboard = async () => { // Make async for modern API
    if (!navigator.clipboard) {
      // Fallback for older browsers or insecure contexts (http)
      const textArea = document.createElement("textarea");
      textArea.value = credentialsString;
      textArea.style.position = "fixed"; 
      textArea.style.left = "-9999px"; // Move out of view
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        const successful = document.execCommand('copy');
        const msg = successful ? 'Credentials copied to clipboard!' : 'Failed to copy credentials.';
        alert(msg); 
      } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        alert('Failed to copy credentials.');
      }
      document.body.removeChild(textArea);
      return;
    }

    try {
      await navigator.clipboard.writeText(credentialsString);
      alert('Credentials copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy credentials: ', err);
      alert('Failed to copy credentials.');
    }
  };

  const modalStyle = {
    position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
    backgroundColor: 'white', padding: '20px', zIndex: 1000, borderRadius: '8px',
    boxShadow: '0 4px 15px rgba(0,0,0,0.2)', width: '90%', maxWidth: '600px',
    maxHeight: '80vh', overflowY: 'auto'
  };
  const backdropStyle = {
    position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
    backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 999
  };
  const preStyle = {
    whiteSpace: 'pre-wrap', wordWrap: 'break-word', backgroundColor: '#f4f4f4',
    padding: '10px', borderRadius: '4px', border: '1px solid #ccc',
    maxHeight: '50vh', overflowY: 'auto'
  };
  const buttonContainerStyle = { marginTop: '15px', display: 'flex', justifyContent: 'space-between' };

  console.log("[MODAL LOG] CredentialsDisplayModal IS RENDERING."); 

  return (
    <>
      <div style={backdropStyle} onClick={onClose}></div> {/* Added onClose to backdrop for better UX */}
      <div style={modalStyle}>
        <h3>Student Accounts Created Successfully!</h3>
        <p><strong>Important:</strong> Please copy these credentials and distribute them securely to your students. They will not be shown again.</p>
        <pre style={preStyle}>{credentialsString}</pre>
        <div style={buttonContainerStyle}>
          <button onClick={handleCopyToClipboard} style={{padding: '8px 12px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px'}}>Copy to Clipboard</button>
          <button onClick={onClose} style={{padding: '8px 12px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px'}}>Close</button>
        </div>
      </div>
    </>
  );
};


function TeacherDashboardPage() {
  const { currentUser, createStudentAccountByTeacher } = useAuth();
  const [classes, setClasses] = useState([]);
  const [newClassName, setNewClassName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const [selectedClassForManagement, setSelectedClassForManagement] = useState(null);
  const [classDetails, setClassDetails] = useState(null);
  const [numStudentsToCreate, setNumStudentsToCreate] = useState(1);
  const [studentCreationLoading, setStudentCreationLoading] = useState(false);
  const [studentCreationError, setStudentCreationError] = useState('');
  const [createdStudentCredentials, setCreatedStudentCredentials] = useState([]);
  const [shouldShowCredentialsModal, setShouldShowCredentialsModal] = useState(false); // Added state

  const [availableWorksheets, setAvailableWorksheets] = useState([]);
  const [selectedWorksheetIdToAssign, setSelectedWorksheetIdToAssign] = useState('');
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assignmentError, setAssignmentError] = useState('');
  const [assignmentSuccess, setAssignmentSuccess] = useState('');

  useEffect(() => {
    console.log("[EFFECT LOG] createdStudentCredentials changed:", createdStudentCredentials);
  }, [createdStudentCredentials]);

  useEffect(() => {
    console.log("[EFFECT LOG] shouldShowCredentialsModal changed:", shouldShowCredentialsModal);
  }, [shouldShowCredentialsModal]);


  const fetchClasses = useCallback(async () => {
    setIsLoading(true); setError('');
    try {
      const response = await getTeacherClasses();
      if (response.data.success) setClasses(response.data.classes);
      else setError(response.data.message || 'Failed to fetch classes.');
    } catch (err) { setError(err.response?.data?.message || err.message || 'An error occurred while fetching classes.'); } 
    finally { setIsLoading(false); }
  }, []);

  const fetchAvailableWorksheets = useCallback(async () => {
    try {
      const response = await listAllWorksheets();
      if (response.data.success) setAvailableWorksheets(response.data.worksheets);
      else setError(response.data.message || 'Failed to fetch available worksheets.');
    } catch (err) { setError(err.response?.data?.message || err.message || 'An error occurred while fetching worksheets.');}
  }, []);
  
  const fetchClassDetails = useCallback(async (classId) => {
    if (!classId) return;
    setAssignmentError(''); setAssignmentSuccess(''); // Clear assignment messages when fetching details
    setStudentCreationError(''); // Clear student creation errors too
    try {
      const response = await getClassDetails(classId);
      if (response.data.success) setClassDetails(response.data.class_details);
      else setStudentCreationError(response.data.message || 'Failed to fetch class details.');
    } catch (err) { setStudentCreationError(err.response?.data?.message || err.message || 'An error fetching class details.');}
  }, []);

  useEffect(() => {
    fetchClasses();
    fetchAvailableWorksheets();
  }, [fetchClasses, fetchAvailableWorksheets]);

  const handleCreateClassSubmit = async (e) => {
    e.preventDefault();
    if (!newClassName.trim()) { setError('Class name cannot be empty.'); return; }
    setIsLoading(true); setError(''); setSuccessMessage('');
    try {
      const response = await createClass({ name: newClassName.trim() });
      if (response.data.success) {
        setSuccessMessage(`Class '${newClassName.trim()}' created successfully!`);
        setNewClassName(''); fetchClasses(); 
      } else { setError(response.data.message || 'Failed to create class.'); }
    } catch (err) { setError(err.response?.data?.message || err.message || 'An error occurred while creating the class.');} 
    finally { setIsLoading(false); }
  };

  const handleSelectClassForManagement = (cls) => {
    setSelectedClassForManagement(cls); 
    setClassDetails(null); 
    setStudentCreationError(''); 
    setCreatedStudentCredentials([]); // Clear credentials when selecting a new class
    setShouldShowCredentialsModal(false); // Hide modal if it was open for a previous class
    setNumStudentsToCreate(1); 
    setSelectedWorksheetIdToAssign('');
    setAssignmentError(''); 
    setAssignmentSuccess('');
    if (cls) {
      fetchClassDetails(cls.id);
    }
  };

  const handleGenerateStudents = async (e) => {
    e.preventDefault();
    if (!selectedClassForManagement) { setStudentCreationError("Please select a class first."); return; }
    if (numStudentsToCreate < 1 || numStudentsToCreate > 50) { setStudentCreationError("Number of students must be between 1 and 50."); return; }
    
    setStudentCreationLoading(true); 
    setStudentCreationError(''); 
    // Do NOT clear createdStudentCredentials here, let modal close handler do it or new class selection.
    setShouldShowCredentialsModal(false); // Explicitly hide modal before attempting to show new credentials
    
    try {
      const response = await createStudentAccountByTeacher({
        classId: selectedClassForManagement.id,
        numStudents: parseInt(numStudentsToCreate, 10)
      });
      console.log("Response from createStudentAccountByTeacher:", response); 
      
      if (response.success && response.created_students && response.created_students.length > 0) {
        console.log("Data being passed to setCreatedStudentCredentials:", response.created_students); 
        setCreatedStudentCredentials([...response.created_students]);        
        setShouldShowCredentialsModal(true); // Explicitly set to show the modal
        console.log("Student credentials state set, shouldShowCredentialsModal set to true. Modal should appear.");
        // Optionally, refresh class details if student counts need to be updated immediately in the UI
        // fetchClassDetails(selectedClassForManagement.id); 
      } else {
        setStudentCreationError(response.message || 'Failed to create student accounts or no students returned.');
        setCreatedStudentCredentials([]); 
        setShouldShowCredentialsModal(false);
      }
    } catch (err) {
      setStudentCreationError(err.message || 'An error occurred while creating student accounts.');
      console.error("Student creation error:", err);
      setCreatedStudentCredentials([]); 
      setShouldShowCredentialsModal(false);
    } finally {
      setStudentCreationLoading(false);
    }
  };

  const handleModalClose = () => {
    console.log("[MODAL CLOSE HANDLER] Closing modal and clearing credentials.");
    setShouldShowCredentialsModal(false);
    setCreatedStudentCredentials([]);
    // Refresh class details to reflect new student count if necessary
    if (selectedClassForManagement) {
      fetchClassDetails(selectedClassForManagement.id); 
    }
  };

  const handleAssignWorksheet = async (e) => {
    e.preventDefault();
    if (!selectedClassForManagement) { setAssignmentError("Please select a class first."); return; }
    if (!selectedWorksheetIdToAssign) { setAssignmentError("Please select a worksheet to assign."); return; }
    setAssignmentLoading(true); setAssignmentError(''); setAssignmentSuccess('');
    try {
      const response = await assignWorksheetToClass(selectedClassForManagement.id, selectedWorksheetIdToAssign);
      if (response.data.success) {
        setAssignmentSuccess(response.data.message || "Worksheet assigned successfully!");
        setSelectedWorksheetIdToAssign(''); 
        fetchClassDetails(selectedClassForManagement.id); 
      } else { setAssignmentError(response.data.message || "Failed to assign worksheet."); }
    } catch (err) { setAssignmentError(err.response?.data?.message || err.message || "An error occurred during assignment."); } 
    finally { setAssignmentLoading(false); }
  };

  // Consider moving these styles to a separate CSS file or using CSS-in-JS for better organization
  const cardStyle = { border: '1px solid #ddd', padding: '15px', marginBottom: '15px', borderRadius: '8px', backgroundColor: '#f9f9f9' };
  const inputStyle = { padding: '10px', marginRight: '10px', border: '1px solid #ccc', borderRadius: '4px', minWidth: '200px', marginBottom: '10px' };
  const buttonStyle = { padding: '10px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginBottom: '10px' };
  const errorStyle = { color: 'red', margin: '10px 0', padding: '10px', border: '1px solid red', borderRadius: '4px', backgroundColor: '#ffebee' };
  const successStyle = { color: 'green', margin: '10px 0', padding: '10px', border: '1px solid green', borderRadius: '4px', backgroundColor: '#e8f5e9' };
  const classListItemStyle = { borderBottom: '1px solid #eee', padding: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', borderRadius: '4px', marginBottom: '5px' };
  const selectedClassStyle = { ...classListItemStyle, backgroundColor: '#e7f3ff', borderLeft: '4px solid #007bff' };
  const subSectionStyle = { marginTop: '20px', paddingTop: '15px', borderTop: '1px dashed #ccc' };

  // console.log("Created Student Credentials for Modal (on render):", createdStudentCredentials);
  // console.log("shouldShowCredentialsModal (on render):", shouldShowCredentialsModal);
  return (
    <div>
      <h2>Teacher Dashboard</h2>
      <p>Welcome, {currentUser?.displayName || currentUser?.email || 'Teacher'}!</p>
      {error && <div style={errorStyle}>{error}</div>}
      {successMessage && <div style={successStyle}>{successMessage}</div>}
      <div style={cardStyle}>
        <h3>Create New Class</h3>
        <form onSubmit={handleCreateClassSubmit}>
          <input type="text" value={newClassName} onChange={(e) => setNewClassName(e.target.value)} placeholder="Enter new class name" style={inputStyle} disabled={isLoading} />
          <button type="submit" style={{...buttonStyle, marginLeft: '0'}} disabled={isLoading}>
            {isLoading ? 'Creating...' : 'Create Class'}
          </button>
        </form>
      </div>
      <div style={{display: 'flex', gap: '20px', flexWrap: 'wrap'}}>
        <div style={{...cardStyle, flex: 1, minWidth: '300px'}}>
          <h3>Your Classes</h3>
          <p style={{fontSize: '0.85em', color: '#555'}}>Click on a class to manage it.</p>
          {isLoading && classes.length === 0 && <p>Loading classes...</p>}
          {!isLoading && classes.length === 0 && !error && (<p>You haven't created any classes yet.</p>)}
          {classes.length > 0 && (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {classes.map((cls) => (
                <li key={cls.id} style={selectedClassForManagement?.id === cls.id ? selectedClassStyle : classListItemStyle} onClick={() => handleSelectClassForManagement(cls)}>
                  <span>{cls.name}</span>
                  <span style={{fontSize: '0.9em', color: '#555'}}>Students: {cls.student_count !== undefined ? cls.student_count : 'N/A'}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        {selectedClassForManagement && (
          <div style={{...cardStyle, flex: 2, minWidth: '400px'}}>
            <h3>Manage Class: {selectedClassForManagement.name}</h3>
            <div style={subSectionStyle}>
              <h4>Add Students to Class</h4>
              {studentCreationError && <div style={errorStyle}>{studentCreationError}</div>}
              <form onSubmit={handleGenerateStudents}>
                <label htmlFor="numStudents" style={{display: 'block', marginBottom: '5px'}}>Number of new student accounts:</label>
                <input type="number" id="numStudents" value={numStudentsToCreate} onChange={(e) => setNumStudentsToCreate(e.target.value)} min="1" max="50" style={{...inputStyle, width: '80px', marginBottom:'10px'}} disabled={studentCreationLoading} />
                <button type="submit" style={buttonStyle} disabled={studentCreationLoading}>
                  {studentCreationLoading ? 'Generating...' : 'Generate Student Accounts'}
                </button>
              </form>
            </div>
            <div style={subSectionStyle}>
              <h4>Assign Worksheet to Class</h4>
              {assignmentError && <div style={errorStyle}>{assignmentError}</div>}
              {assignmentSuccess && <div style={successStyle}>{assignmentSuccess}</div>}
              <form onSubmit={handleAssignWorksheet}>
                <label htmlFor="worksheetToAssign" style={{display: 'block', marginBottom: '5px'}}>Select Worksheet:</label>
                <select id="worksheetToAssign" value={selectedWorksheetIdToAssign} onChange={(e) => setSelectedWorksheetIdToAssign(e.target.value)} style={{...inputStyle, minWidth: '250px'}} disabled={assignmentLoading || availableWorksheets.length === 0}>
                  <option value="">-- Select a Worksheet --</option>
                  {availableWorksheets.map(ws => (<option key={ws.id} value={ws.id}>{ws.title}</option>))}
                </select>
                <button type="submit" style={buttonStyle} disabled={assignmentLoading || !selectedWorksheetIdToAssign}>
                  {assignmentLoading ? 'Assigning...' : 'Assign Worksheet'}
                </button>
              </form>
            </div>
            {classDetails && classDetails.assigned_worksheets && classDetails.assigned_worksheets.length > 0 && (
              <div style={subSectionStyle}>
                <h4>Currently Assigned Worksheets:</h4>
                <ul style={{ listStyle: 'disc', paddingLeft: '20px' }}>
                  {classDetails.assigned_worksheets.map(aw => ( <li key={aw.assignment_id}> {aw.title} (Assigned: {new Date(aw.assigned_date).toLocaleDateString()}) </li> ))}
                </ul>
              </div>
            )}
            
             {classDetails && (!classDetails.assigned_worksheets || classDetails.assigned_worksheets.length === 0) && ( <div style={subSectionStyle}><p>No worksheets currently assigned to this class.</p></div> )}

            {/* Render modal based on the explicit flag and presence of data */}
            {shouldShowCredentialsModal && createdStudentCredentials.length > 0 && (
              <CredentialsDisplayModal 
                credentials={createdStudentCredentials} 
                onClose={handleModalClose} 
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default TeacherDashboardPage;
