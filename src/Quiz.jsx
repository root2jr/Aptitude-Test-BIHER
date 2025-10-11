import React, { useState, useEffect, useRef } from 'react';
import './App.css'; // The quiz component will share the main stylesheet
import logo from '/images/logo.png'; // Correct path for Vite projects

// The URL of your FastAPI backend.
const API_URL = "http://127.0.0.1:8000";
const QUESTION_TIME_LIMIT = 60; // 60 seconds per question

function Quiz({ onLogout }) { // Renamed from App to Quiz and accepting onLogout prop
  // --- State Variables ---
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isBlocked, setIsBlocked] = useState(false);
  const [questionTimeLeft, setQuestionTimeLeft] = useState(QUESTION_TIME_LIMIT);

  const timerRef = useRef(null);

  // --- Check for block on initial app load ---
  useEffect(() => {
    const blockedStatus = localStorage.getItem('testBlocked');
    if (blockedStatus === 'true') {
      setIsBlocked(true);
      setIsLoading(false); // Stop loading if blocked
    } else {
      fetchQuestions(); // Fetch questions only if not blocked
    }
  }, []);

  // --- Data Fetching ---
  const fetchQuestions = () => {
    setIsLoading(true);
    fetch(`${API_URL}/api/questions`)
      .then(res => res.json())
      .then(data => {
        setQuestions(data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error("Failed to fetch questions:", error);
        setIsLoading(false);
      });
  };

  // --- Anti-Cheating: Tab Switch Detection ---
  useEffect(() => {
    if (isLoading || showResults || isBlocked) return;
    const handleVisibilityChange = () => {
      if (document.hidden) {
        localStorage.setItem('testBlocked', 'true');
        setIsBlocked(true);
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isLoading, showResults, isBlocked]);

  // --- Per-Question Timer Setup ---
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (isLoading || showResults || isBlocked) return;

    setQuestionTimeLeft(QUESTION_TIME_LIMIT); // Reset timer for the new question

    timerRef.current = setInterval(() => {
      setQuestionTimeLeft(prevTime => prevTime - 1);
    }, 1000);

    return () => clearInterval(timerRef.current);
  }, [currentQuestionIndex, isLoading, showResults, isBlocked]);

  // --- Effect to Handle Timer Expiration ---
  useEffect(() => {
    if (questionTimeLeft <= 0) {
      handleNextClick(); // Move to the next question automatically when time is up
    }
  }, [questionTimeLeft]);

  // --- Event Handlers ---
  const handleAnswerSelect = (questionId, selectedOption) => {
    setUserAnswers({
      ...userAnswers,
      [questionId]: selectedOption,
    });
  };

  const handleSubmit = () => {
    if (showResults) return;
    clearInterval(timerRef.current);
    fetch(`${API_URL}/api/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers: userAnswers }),
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

  if (isLoading) {
    return <div className="container"><h1>Loading Test...</h1></div>;
  }

  if (showResults) {
    return (
      <div className="container">
        <div className="results-container">
          <h2>Test Complete! ✅</h2>
          <p className="score-text">
            Your Final Score: {score?.score} / {score?.total}
          </p>
          <button onClick={onLogout} className="restart-btn">Logout & Finish</button>
        </div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="container">
        <h1>Could not load questions.</h1>
        <p>Please ensure the backend server is running and `questions.json` is not empty.</p>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="container">
       <div className="timer">
          <svg className="timer-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
          <span>{questionTimeLeft}s</span>
      </div>
      <div className="quiz-header">
        <img src={logo} alt="Bharat University Logo"/>
        <h1>Aptitude Test</h1>
        <div className="progress-bar">
          <div
            className="progress-bar-inner"
            style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
          ></div>
        </div>
      </div>
      <div className="question-block">
        <p className="question-text">
          <span style={{ color: '#718096', marginRight: '8px' }}>
            {currentQuestionIndex + 1}.
          </span>
          {currentQuestion.question}
        </p>
        <div className="options-container">
          {currentQuestion.options.map((option) => (
            <button
              key={option}
              className={`option-btn ${userAnswers[currentQuestion.id] === option ? 'selected' : ''}`}
              onClick={() => handleAnswerSelect(currentQuestion.id, option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      <button
        onClick={handleNextClick}
        className="next-btn"
        disabled={!userAnswers[currentQuestion.id]}
      >
        {currentQuestionIndex === questions.length - 1 ? 'Submit' : 'Next Question'}
      </button>
    </div>
  );
}

export default Quiz;
