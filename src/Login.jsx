import React, { use, useState } from 'react';
// The logo is now referenced directly from the public folder in the img tag
import './App.css'; // Uses the same stylesheet

function Login() {
    const [userName, setUserName] = useState('');
    const [studentId, setStudentId] = useState('');
    const onLogin = () => {
        console.log("Username:", userName);
        console.log("Student ID:", studentId);
    }
  return (
    <div className="container">
      <div className="login-container">
        {/* Using the direct path to the public folder is the standard Vite approach */}
        <img src="/images/logo.png" alt="Bharat University Logo" />
        <h1>Student Details</h1>
        <input
          type="text"
          placeholder="Enter your full name"
          className="input-field"
          value={userName}
          onChange={(e) => setUserName(e.target.value)}
        />
        <input
          type="text"
          placeholder="Enter your Student ID"
          className="input-field"
          value={studentId}
          onChange={(e) => setStudentId(e.target.value)}
        />
        <button
          onClick={onLogin}
          className="next-btn"
          disabled={!userName.trim() || !studentId.trim()}
        >
          Start Test
        </button>
      </div>
    </div>
  );
}

export default Login;

