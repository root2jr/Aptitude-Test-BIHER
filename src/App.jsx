import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import logo from '/images/logo.png';

const API_URL = "http://127.0.0.1:8000";
const QUESTION_TIME_LIMIT = 60;

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [department, setDepartment] = useState('');
  const [Test, setTest] = useState('');
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBlocked, setIsBlocked] = useState(false);
  const [questionTimeLeft, setQuestionTimeLeft] = useState(QUESTION_TIME_LIMIT);

  const timerRef = useRef(null);

  useEffect(() => {
    const loggedInStatus = localStorage.getItem('isLoggedIn');
    const blockedStatus = localStorage.getItem('testBlocked');

    if (blockedStatus === 'true') {
      setIsBlocked(true);
    } else if (loggedInStatus === 'true') {
      setIsLoggedIn(true);
    }
  }, []);



  const handleLogin = async () => {
    if (!studentName.trim() || !studentId.trim()) {
      alert("Please enter both your name and student ID.");
      return;
    }
    if ((studentId.length < 9) || (studentId[0] != 'U')) {
      alert("Enter a valid Student ID");
      return;
    }

    setIsRegistering(true);

    try {

      const response = await fetch(`${API_URL}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: studentName,
          userid: studentId,
          didCheat: "NO",
          department: department,
          test: Test
        }),
      });
      const responseData = await response.json();
      const stringdfy = JSON.stringify(responseData);
      if (responseData && responseData.message === "User Already Attended the Test") {
        alert("User Already Attended the Test");
        setStudentId("");
        setStudentName("");
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to register user on the server.');
      }

      // Step 2: If registration is successful, log in on the client-side
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('studentName', studentName);
      localStorage.setItem('studentId', studentId);
      localStorage.setItem('test', Test);
      setIsLoggedIn(true);

    } catch (error) {
      console.error("Login failed:", error);
      alert("Could not start the test. Please check your connection and try again.");
    } finally {
      setIsRegistering(false);
    }
  };

  // --- Data Fetching ---
  useEffect(() => {
    if (!isLoggedIn || isBlocked) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    fetch(`${API_URL}/api/questions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ test: localStorage.getItem("test") }),
    })
      .then(res => res.json())
      .then(data => {
        setQuestions(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Failed to fetch questions:", error);
        setIsLoading(false);
      });
  }, [isLoggedIn, isBlocked]);


  useEffect(() => {
    if (!isLoggedIn || isLoading || showResults || isBlocked) return;
    const handleVisibilityChange = () => {
      if (document.hidden) {
        const id = localStorage.getItem('studentId');
        if (id) {
          fetch(`${API_URL}/cheat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ userid: id }),
          }).catch(err => console.error("Could not report cheat to server:", err));
        }

        localStorage.setItem('testBlocked', 'true');
        setIsBlocked(true);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isLoggedIn, isLoading, showResults, isBlocked]);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (!isLoggedIn || isLoading || showResults || isBlocked) return;

    setQuestionTimeLeft(QUESTION_TIME_LIMIT);
    timerRef.current = setInterval(() => {
      setQuestionTimeLeft(prevTime => prevTime - 1);
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [currentQuestionIndex, isLoggedIn, isLoading, showResults, isBlocked]);

  useEffect(() => {
    if (questionTimeLeft <= 0) {
      handleNextClick();
    }
  }, [questionTimeLeft]);

  // --- Event Handlers ---
  const handleAnswerSelect = (questionId, selectedOption) => {
    setUserAnswers({ ...userAnswers, [questionId]: selectedOption });
  };

  const handleSubmit = () => {
    if (showResults) return;
    clearInterval(timerRef.current);
    const userid = localStorage.getItem("studentId");
    // Corrected the body to match the backend's Pydantic model
    fetch(`${API_URL}/api/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userid: userid, answers: userAnswers }),
    })
      .then(res => res.json())
      .then(result => {
        setScore(result);
        setShowResults(true);
      })
      .catch(error => console.error("Failed to submit answers:", error));
  };

  const handleNextClick = () => {
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    if (isLastQuestion) {
      handleSubmit();
    } else {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  // --- Render Logic ---
  if (isBlocked) {
    return (
      <div className="container">
        <div className="results-container blocked-view">
          <h2>Test Blocked 🚫</h2>
          <p className="score-text">
            This test has been permanently blocked on this browser due to a navigation violation.
          </p>
        </div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return (
      <div className="container">
        <div className="login-container">
          <img src={logo} alt="Bharat University Logo" />
          <h1>Student Aptitude Test</h1>
          <input
            type="text"
            className="input-field"
            placeholder="Enter your full name"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            disabled={isRegistering}
          />
          <input
            type="text"
            className="input-field"
            placeholder="Enter your Student ID"
            value={studentId}
            onChange={(e) => setStudentId((e.target.value).toUpperCase())}
            disabled={isRegistering}
          />
          <select className="input-field" value={department} onChange={e => setDepartment(e.target.value)} disabled={isRegistering}>
            <option value="" disabled>Select your Department</option>
            <option value="Bachelors of Computer Science">Bachelors of Computer Science</option>
            <option value="Bachelors of Computer Application">Bachelors of Computer Application</option>
          </select>
          <select className="input-field" value={Test} onChange={e => setTest(e.target.value)} disabled={isRegistering}>
            <option value="" disabled>Select your Test</option>
            <option value="Prilims-1">Prilims-1</option>
            <option value="Prilims-2">Prilims-2</option>
            <option value="Prilims-3">Prilims-3</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
          <button onClick={handleLogin} className="next-btn" disabled={isRegistering}>
            {isRegistering ? 'Registering...' : 'Start Test'}
          </button>
        </div>
      </div>
    );
  }

  if (isLoading) return <div className="container"><h1>Loading Test...</h1></div>;

  if (showResults) {
    return (
      <div className="container">
        <div className="results-container">
          <h2>Test Complete! ✅</h2>
          <p className="score-text">Your Final Score: {score?.score} / {score?.total}</p>
          <button onClick={() => {
            localStorage.clear();
            window.location.reload();
          }} className="restart-btn">Logout</button>
        </div>
      </div>
    );
  }

  if (!questions.length) return <div className="container"><h1>Could not load questions.</h1></div>;

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="container">
      <div className="timer">
        <svg className="timer-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{questionTimeLeft}s</span>
      </div>
      <div className="quiz-header">
        <img src={logo} alt="Bharat University Logo" />
        <h1>Aptitude Test</h1>
        <div className="progress-bar">
          <div className="progress-bar-inner" style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}></div>
        </div>
      </div>
      <div className="question-block">
        <p className="question-text">
          <span style={{ color: '#718096', marginRight: '8px' }}>{currentQuestionIndex + 1}.</span>
          {currentQuestion.question}
        </p>
        <div className="options-container">
          {currentQuestion.options.map((option) => (
            <button key={option} style={{ color: "black" }} className={`option-btn ${userAnswers[currentQuestion.id] === option ? 'selected' : ''}`} onClick={() => handleAnswerSelect(currentQuestion.id, option)}>
              {option}
            </button>
          ))}
        </div>
      </div>
      <button onClick={handleNextClick} className="next-btn" disabled={!userAnswers[currentQuestion.id]}>
        {currentQuestionIndex === questions.length - 1 ? 'Submit' : 'Next Question'}
      </button>
    </div>
  );
}

export default App;

