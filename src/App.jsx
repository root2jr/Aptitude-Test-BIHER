import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import logo from '/images/logo.png'; // Make sure this path is correct relative to public folder

const API_URL = "https://aptitude-test-biher.onrender.com";
const QUESTION_TIME_LIMIT = 60; // 60 seconds per question

function App() {
  // --- State Variables ---
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [department, setDepartment] = useState('');
  const [test, setTest] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(null);
  const [detailedResults, setDetailedResults] = useState([]); // <-- NEW state for review
  const [isLoading, setIsLoading] = useState(true);
  const [isBlocked, setIsBlocked] = useState(false);
  const [questionTimeLeft, setQuestionTimeLeft] = useState(QUESTION_TIME_LIMIT);
  const [showWarning, setShowWarning] = useState(false);
  const [returnLogin, setReturnLogin] = useState(false);

  const timerRef = useRef(null);
  const warningTimeoutRef = useRef(null);
  const timeoutTriggeredNextRef = useRef(false);

  // --- Initial Load Check ---
  useEffect(() => {
    const blockedStatus = localStorage.getItem('testBlocked');
    const loggedInStatus = localStorage.getItem('isLoggedIn');

    if (blockedStatus === 'true') {
      setIsBlocked(true);
      setIsLoading(false);
    } else if (loggedInStatus === 'true') {
      setIsLoggedIn(true);
      // Retrieve stored details if needed
      setStudentName(localStorage.getItem('studentName') || '');
      setStudentId(localStorage.getItem('studentId') || '');
      setTest(localStorage.getItem('test') || '');
      setDepartment(localStorage.getItem('department') || ''); // Retrieve department too
    } else {
      setIsLoading(false);
    }

    return () => {
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
    };
  }, []);

  // --- Login Handler ---
  const handleLogin = async () => {
    if (!studentName.trim() || !studentId.trim() || !department || !test) {
      alert("Please fill in all fields: Name, Student ID, Department, and Test.");
      return;
    }
    if (studentId.length < 9 || (studentId[0] !== 'U' && studentId[0] !== 'P')) {
      alert("Enter a valid Student ID (must start with 'U' or 'P' and be at least 9 characters)");
      return;
    }

    
    setIsRegistering(true);
    try {
      const response = await fetch(`${API_URL}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: studentName, userid: studentId, department: department, test: test, didCheat: "NO" }),
      });
      const responseData = await response.json();
      localStorage.setItem("jwt", responseData?.token);
      if (responseData?.message === "User Already Attended the Test") {
        alert("A test has already been submitted with this Student ID.");
        setIsRegistering(false);
        return;
      }
      if (!response.ok) throw new Error(responseData.detail || 'Failed to register user.');

      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('studentName', studentName);
      localStorage.setItem('studentId', studentId);
      localStorage.setItem('test', test);
      localStorage.setItem('department', department); // Save department
      localStorage.setItem('violationCount', '0');
      setIsLoggedIn(true);
    } catch (error) {
      console.error("Login failed:", error);
      alert(`Could not start the test: ${error.message}.`);
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
    const selectedTest = localStorage.getItem("test");
    if (!selectedTest) {
      console.error("No test selected."); setIsLoading(false); return;
    }
    fetch(`${API_URL}/api/questions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ test: selectedTest, jwt:localStorage.getItem("jwt") }),
    })
      .then(res => res.ok ? res.json() : res.json().then(err => { throw new Error(err.detail || 'Failed to fetch.') }))
      .then(data => { setQuestions(data); setIsLoading(false); })
      .catch(error => { console.error("Fetch questions error:", error); alert(`Error: ${error.message}`); setIsLoading(false); });
  }, [isLoggedIn, isBlocked]);

  // --- Anti-Cheating: Tab Switch Detection (2-Strike Policy) ---
  useEffect(() => {
    if (isLoading || showResults || isBlocked || !isLoggedIn) {
      if (warningTimeoutRef.current) { clearTimeout(warningTimeoutRef.current); warningTimeoutRef.current = null; setShowWarning(false); }
      return;
    }
    const handleVisibilityChange = () => {
      if (document.hidden && !showResults && !isBlocked && isLoggedIn) {
        if (warningTimeoutRef.current) { clearTimeout(warningTimeoutRef.current); warningTimeoutRef.current = null; }
        let currentViolations = parseInt(localStorage.getItem('violationCount') || '0', 10);
        const newViolationCount = currentViolations + 1;
        localStorage.setItem('violationCount', newViolationCount.toString());
        if (newViolationCount === 1) {
          setShowWarning(true);
          warningTimeoutRef.current = setTimeout(() => { setShowWarning(false); warningTimeoutRef.current = null; }, 60000);
        } else if (newViolationCount >= 2) {
          const id = localStorage.getItem('studentId');
          if (id) { fetch(`${API_URL}/cheat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ userid: id, jwt: localStorage.getItem("jwt") }) }).catch(err => console.error("Cheat report failed:", err)); }
          localStorage.setItem('testBlocked', 'true');
          setIsBlocked(true);
          if (timerRef.current) clearInterval(timerRef.current);
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (warningTimeoutRef.current) { clearTimeout(warningTimeoutRef.current); warningTimeoutRef.current = null; }
    };
  }, [isLoading, showResults, isBlocked, isLoggedIn]);

  // --- Per-Question Timer Setup ---
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (isLoading || showResults || isBlocked || !isLoggedIn) return;
    setQuestionTimeLeft(QUESTION_TIME_LIMIT);
    timeoutTriggeredNextRef.current = false;
    timerRef.current = setInterval(() => {
      setQuestionTimeLeft(prevTime => {
        if (prevTime <= 1) { clearInterval(timerRef.current); return 0; }
        return prevTime - 1;
      });
    }, 1000);
    return () => clearInterval(timerRef.current);
  }, [currentQuestionIndex, isLoading, showResults, isBlocked, isLoggedIn]);

  const handleSubmit = useCallback(() => {
    if (showResults || isBlocked) return;
    console.log("Submitting final answers.");
    if (timerRef.current) clearInterval(timerRef.current);
    const studentId = localStorage.getItem("studentId");
    const test = localStorage.getItem("test");
    fetch(`${API_URL}/api/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userid: studentId, answers: userAnswers, test: test, jwt: localStorage.getItem("jwt") }),
    })
      .then(res => res.ok ? res.json() : res.json().then(err => { throw new Error(err.detail || 'Submit failed.') }))
      .then(result => {
        setScore({ score: result.score, total: result.total });
        setDetailedResults(result.results || []); // <-- Store detailed results
        setShowResults(true);
        setTimeout(() => {
          setReturnLogin(true);
        }, 60000);
      })
      .catch(error => {
        console.error("Failed to submit answers:", error);
        alert(`Submission Error: ${error.message}`);
        // Optionally, don't show results on error, or handle differently
      });
  }, [showResults, isBlocked, userAnswers]);

  // --- Next Click Handler (useCallback) ---
  const handleNextClick = useCallback(() => {
    if (showResults || isBlocked) return;
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    if (isLastQuestion) {
      handleSubmit();
    } else {
      setCurrentQuestionIndex(prevIndex => prevIndex + 1);
    }
    timeoutTriggeredNextRef.current = false;
  }, [currentQuestionIndex, questions.length, showResults, isBlocked, handleSubmit]);

  // --- Effect to Handle Timer Expiration ---
  useEffect(() => {
    if (questionTimeLeft <= 0 && !isLoading && !showResults && !isBlocked && isLoggedIn) {
      if (!timeoutTriggeredNextRef.current) {
        console.log("Timer expired, triggering handleNextClick.");
        timeoutTriggeredNextRef.current = true;
        handleNextClick();
      }
    }
  }, [questionTimeLeft, isLoading, showResults, isBlocked, isLoggedIn, handleNextClick]);


  // --- Event Handlers ---
  const handleAnswerSelect = (questionId, selectedOption) => {
    setUserAnswers({ ...userAnswers, [questionId]: selectedOption });
  };


  // --- Render Logic ---
  if (isBlocked) {
    return (
      <div className="container">
        <div className="results-container blocked-view">
          <h2>Test Blocked 🚫</h2>
          <p className="score-text">This test has been permanently blocked due to multiple navigation violations.</p>
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
          <input type="text" className="input-field" placeholder="Enter your full name" value={studentName} onChange={(e) => setStudentName(e.target.value)} disabled={isRegistering} />
          <input type="text" className="input-field" placeholder="Enter your Student ID" value={studentId} onChange={(e) => setStudentId(e.target.value.toUpperCase())} disabled={isRegistering} />
          <select className="input-field" value={department} onChange={e => setDepartment(e.target.value)} disabled={isRegistering}>
            <option value="" disabled>Select your Department</option>
            <option value="Bachelors of Computer Science">Bachelors of Computer Science</option>
            <option value="Bachelors of Computer Application">Bachelors of Computer Application</option>
            <option value="Masters of Computer Science">Masters of Computer Science</option>
            <option value="Masters of Computer Application">Masters of Computer Application</option>
          </select>
          <select className="input-field" value={test} onChange={e => setTest(e.target.value)} disabled={isRegistering}>
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

          {/* --- NEW ANSWER REVIEW SECTION --- */}
          <div className="answer-review-container">
            <h3>Answer Review</h3>
            {detailedResults.length > 0 ? (
              detailedResults.map((result, index) => (
                <div key={result.id || index} className="review-item">
                  <p className="review-question">
                    <strong>{index + 1}. {result.question}</strong>
                  </p>
                  <p className={`review-answer your-answer ${result.isCorrect ? 'correct' : 'incorrect'}`}>
                    Your Answer: {result.userAnswer || <i>Not Answered</i>}
                    {result.isCorrect ? <span className="feedback-icon"> ✔️</span> : <span className="feedback-icon"> ❌</span>}
                  </p>
                  {!result.isCorrect && (
                    <p className="review-answer correct-answer">
                      Correct Answer: {result.correctAnswer}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <p>Detailed results could not be loaded.</p>
            )}
          </div>
          {/* --- END ANSWER REVIEW SECTION --- */}

        { returnLogin && <button onClick={() => { localStorage.clear(); window.location.reload(); }} className="restart-btn">
            Logout
          </button> }
        </div>
      </div>
    );
  }

  if (!questions || questions.length === 0) {
    return (
      <div className="container">
        <h1>Could not load questions.</h1>
        <button onClick={() => { localStorage.clear(); window.location.reload(); }} className="restart-btn">Logout</button>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  if (!currentQuestion) return <div className="container"><h1>Loading question...</h1></div>;

  return (
    <div className="container">
      {showWarning && (<div className="warning-popup">⚠️ First violation detected. Navigating away again will block the test permanently.</div>)}
      <div className="timer">
        <svg className="timer-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <span>{questionTimeLeft}s</span>
      </div>
      <div className="quiz-header">
        <img src={logo} alt="Bharat University Logo" />
        <h1>Aptitude Test</h1>
        <div className="progress-bar"><div className="progress-bar-inner" style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}></div></div>
      </div>
      <div className="question-block">
        <p className="question-text"><span>{currentQuestionIndex + 1}.</span> {currentQuestion.question}</p>
        <div className="options-container">
          {currentQuestion.options.map((option) => (
            <button key={option} className={`option-btn ${userAnswers[currentQuestion.id] === option ? 'selected' : ''}`} onClick={() => handleAnswerSelect(currentQuestion.id, option)}>
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

