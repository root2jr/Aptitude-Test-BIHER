import json
import random
from typing import List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import uuid

# --- 1. INITIALIZE FASTAPI APP ---
app = FastAPI()
load_dotenv()

# --- 2. CONFIGURE CORS ---
# This is crucial for allowing your React frontend (running on a different port)
# to communicate with this backend.
origins = [
    "http://localhost:5173",
    "https://aptitude-test-biher.netlify.app",
    "https://lp732l7b-5173.inc1.devtunnels.ms/"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 3. LOAD QUESTIONS FROM JSON FILE ---
# This loads all questions into memory when the server starts.


url = os.getenv("url")
cluster = AsyncIOMotorClient(url)
db = cluster["Aptitude_Test_BIHER"]
users = db["Users"]
questions = db["Questions"]

class QuestionForClient(BaseModel):
    id: int
    question: str
    options: List[str]


class UserAnswers(BaseModel):
    """The format for receiving answers from the client."""
    userid: str
    answers: Dict[int, str]
    test: str

class test(BaseModel):
   test: str

# --- 5. DEFINE API ENDPOINTS ---

@app.post("/api/questions", response_model=List[QuestionForClient])
async def get_shuffled_questions(data:test):
    """
    This endpoint provides the questions for the test.
    It shuffles the order of questions and the order of options for each question
    to make cheating more difficult. It NEVER sends the answers.
    """
    # Create a deep copy to avoid modifying the original list in memory
    questions_db = (await questions.find_one({"test": data.test}))["questions"]
    questions_copy = [q.copy() for q in questions_db]
    
    # Shuffle the list of questions
    random.shuffle(questions_copy)
    
    # Shuffle the options within each question
    for question in questions_copy:
        random.shuffle(question["options"])
        
    return questions_copy

import json
import random
from typing import List, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient # Assuming these are defined elsewhere
# from dotenv import load_dotenv # Assuming these are defined elsewhere
# Assuming 'app', 'users', 'questions' are initialized Motor collections

# Assuming UserAnswers model is defined like this:
class UserAnswers(BaseModel):
    userid: str
    answers: Dict[str, str] # Frontend sends question ID as string keys
    test: str

@app.post("/api/submit")
async def submit_answers(user_answers: UserAnswers):
    """
    Receives answers, calculates score, saves marks, 
    and returns score, total, and detailed results for review.
    """
    score = 0
    detailed_results = []
    submitted_answers = user_answers.answers

    # Fetch the specific test questions from the database
    test_data = await questions.find_one({"test": user_answers.test})
    if not test_data or "questions" not in test_data:
        raise HTTPException(status_code=404, detail=f"Test '{user_answers.test}' not found or has no questions.")
    
    questions_for_test = test_data["questions"]
    correct_answers_db = {str(q["id"]): q for q in questions_for_test} # Use string ID keys

    # Iterate through all questions of the test to build detailed results
    for question_id_str, q_data in correct_answers_db.items():
        user_answer = submitted_answers.get(question_id_str) # Get user's answer, defaults to None if not found
        is_correct = (user_answer == q_data["answer"])

        if is_correct:
            score += 1

        detailed_results.append({
            "id": q_data["id"],
            "question": q_data["question"],
            "userAnswer": user_answer, # Will be None if not answered
            "correctAnswer": q_data["answer"],
            "isCorrect": is_correct,
        })

    # Sort results by question ID for consistent order
    detailed_results.sort(key=lambda x: x['id'])
    
    total_questions = len(questions_for_test)
    marks_string = f"{score}/{total_questions}"

    # Update the user's record with the marks string
    await users.update_one(
        {"userid": user_answers.userid, "test": user_answers.test}, # Match on userid and test
        {"$set": {"marks": marks_string}},
        upsert=False # Don't create if user not found, should exist from login
    )

    # Return score, total, and the detailed results
    return {
        "score": score,
        "total": total_questions,
        "results": detailed_results # Add the detailed results array
    }

@app.get("/")
def read_root():
    return {"message": f"Welcome to the Aptitude Test API. questions loaded."}


class User(BaseModel):
    name: str
    userid: str
    didCheat: str
    department: str
    test: str

@app.post("/users")
async def handle_user(data:User):
    response1 = await users.find_one({"userid": data.userid})
    if response1:
      return {"message": "User Already Attended the Test"}
    else:
      response = await users.insert_one({"name": data.name, "userid": data.userid, "didCheat": "NO", "department": data.department, "test": data.test})
      return {"message": "Data Saved"}
class StudentID(BaseModel):
    userid: str
@app.post("/cheat")
async def handle_cheat(data:StudentID):
    response = await users.find_one_and_update({"userid": data.userid}, {"$set":{"didCheat": "YES"}})
    return {"message": "Cheat Added"}

@app.get("/fetch-student-details")
async def handle_student_details():
  response = await users.find({}).to_list(length=None)
  for res in response:
    res["_id"] = str(res["_id"])
  return {"message": response}

class AddNewQuestions(BaseModel):
    question: str
    options: List[str]
    answer: str
    test: str

class newAdd(BaseModel):
  Question: List[AddNewQuestions]
  test: str

@app.post("/api/add-questions")
async def handle_add_questions(data: newAdd):
    new_questions = [q.dict() for q in data.Question]

    # Fetch the test document once
    test_doc = await questions.find_one({"test": data.test})

    # Get current count of existing questions
    base_count = len(test_doc["questions"]) if test_doc and "questions" in test_doc else 0

    # Enumerate over new questions, continuing from base_count + 1
    for i, que in enumerate(new_questions, start=base_count + 1):
        que["id"] = i

        await questions.update_one(
            {"test": que["test"]},
            {"$addToSet": {"questions": que}},
            upsert=True
        )

    return {"Message": "Questions Added Successfully", "Added": len(new_questions)}


@app.post("/handle-delete")
async def handle_delete_questions(data:test):
  response = await questions.delete_one({"test": data.test})
  return {"Message": "Questions Deleted Successfully"}

class Fetch_Questions(BaseModel):
  test: str
  
@app.get("/fetch-questions")
async def handle_fetch_questions():
  response = await questions.find({}).to_list(length=None)
  for res in response:
    res["_id"] = str(res["_id"])
  return response

class userdelete(BaseModel):
  reg: str
  
@app.post("/delete-user")
async def handle_user_deletion(data:userdelete):
  response = await users.delete_one({"userid": data.reg})
  return {"message": "User Deleted Successfully"}