// frontend/src/pages/WorksheetDisplayPage.jsx
import React from 'react';
import { useParams } from 'react-router-dom';

function WorksheetDisplayPage() {
  const { worksheetId } = useParams(); // Access the :worksheetId from the URL

  return (
    <div>
      <h2>Worksheet: {worksheetId}</h2>
      <p>The content for worksheet ID: <strong>{worksheetId}</strong> will be loaded and displayed here.</p>
      {/* TODO: Fetch worksheet data based on worksheetId and render the specific worksheet component */}
    </div>
  );
}
export default WorksheetDisplayPage;
