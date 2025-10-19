import json
import random
from typing import List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
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
class AddNewQuestions(BaseModel):
    question: str
    options: List[str]
    answer: str
    test: str

class UserAnswers(BaseModel):
    """The format for receiving answers from the client."""
    userid: str
    answers: Dict[int, str]

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
    correct_answers_db = {q["id"]: q["answer"] for q in questions_db}
    questions_copy = [q.copy() for q in questions_db]
    
    # Shuffle the list of questions
    random.shuffle(questions_copy)
    
    # Shuffle the options within each question
    for question in questions_copy:
        random.shuffle(question["options"])
        
    return questions_copy

@app.post("/api/submit")
async def submit_answers(user_answers: UserAnswers):
    """
    This endpoint receives the user's answers, calculates the score securely
    on the server, and returns the finl result.
    """
    score = 0
    submitted = user_answers.answers
    questions_db = (await questions.find_one({"test": "prelims-1"}))["questions"]
    correct_answers_db = {q["id"]: q["answer"] for q in questions_db}

    # Iterate through the submitted answers and compare with the correct ones
    for question_id, user_answer in submitted.items():
        # Check if the submitted answer for the given question ID is correct
        if correct_answers_db.get(question_id) == user_answer:
            score += 1
    response = await users.find_one_and_update({"userid":user_answers.userid},{"$set":{"marks": f"{score}/{len(questions_db)}"}})
    return {
        "score": score,
        "total": len(questions_db)
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

class newAdd(BaseModel):
  Question: List[AddNewQuestions]
  test: str

@app.post("/api/add-questions")
async def handle_add_questions(data:newAdd):
   new_questions = [q.dict() for q in data.Question]
   for que in new_questions:
      response =  await questions.update_one(
    {"test": que["test"]},
    {"$addToSet": {"questions": que}},upsert=True
)
  
   return {"Message": "Questions Added Successfully"}


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