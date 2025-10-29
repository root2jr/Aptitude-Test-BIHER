import random
from typing import List, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException
from jose import JWTError, jwt
from datetime import timedelta, datetime

app = FastAPI()
load_dotenv()


origins = [
    "http://localhost:5173",
    "https://aptitude-test-biher.netlify.app",
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
staffs = db["Staffs"]
questions = db["Questions"]
ALGORITHM = "HS256"
SECRET = os.getenv("secret-key")

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
   jwt: str



def create_access_token(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + (timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM) 
def check_access_token(token:str):
    check = jwt.decode(token, SECRET,algorithms=ALGORITHM )
    if check:
        return check
    else:
        return HTTPException(status_code=502, detail="Invalid Token.")
# --- 5. DEFINE API ENDPOINTS ---

@app.post("/api/questions", response_model=List[QuestionForClient])
async def get_shuffled_questions(data:test):
    """
    This endpoint provides the questions for the test.
    It shuffles the order of questions and the order of options for each question
    to make cheating more difficult. It NEVER sends the answers.
    """
    # Create a deep copy to avoid modifying the original list in memory
    access = check_access_token(data.jwt)
    if not access:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED.")
    questions_db = (await questions.find_one({"test": data.test}))["questions"]
    questions_copy = [q.copy() for q in questions_db]
    
    # Shuffle the list of questions
    random.shuffle(questions_copy)
    
    # Shuffle the options within each question
    for question in questions_copy:
        random.shuffle(question["options"])
        
    return questions_copy



class UserAnswers(BaseModel):
    userid: str
    answers: Dict[str, str] # Frontend sends question ID as string keys
    test: str
    jwt: str

@app.post("/api/submit")
async def submit_answers(user_answers: UserAnswers):
    """
    Receives answers, calculates score, saves marks,
    and returns score, total, and detailed results for review.
    """
    access = check_access_token(user_answers.jwt)
    if not access:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")

    score = 0
    detailed_results = []
    submitted_answers = user_answers.answers

    # Fetch the specific test questions from the database
    test_data = await questions.find_one({"test": user_answers.test})
    if not test_data or "questions" not in test_data:
        raise HTTPException(
            status_code=404,
            detail=f"Test '{user_answers.test}' not found or has no questions."
        )

    questions_for_test = test_data["questions"]
    correct_answers_db = {str(q["id"]): q for q in questions_for_test}  # Use string ID keys

    # Iterate through all questions to build detailed results
    for question_id_str, q_data in correct_answers_db.items():
        user_answer = submitted_answers.get(question_id_str)
        is_correct = (user_answer == q_data["answer"])

        if is_correct:
            score += 1

        detailed_results.append({
            "id": q_data["id"],
            "question": q_data["question"],
            "userAnswer": user_answer,  # Will be None if not answered
            "correctAnswer": q_data["answer"],
            "isCorrect": is_correct,
        })

    # Sort results by question ID
    detailed_results.sort(key=lambda x: x['id'])

    total_questions = len(questions_for_test)
    marks_string = f"{score}/{total_questions}"

    # Update user's record
    await users.update_one(
        {"userid": user_answers.userid, "test": user_answers.test},
        {"$set": {"marks": marks_string}},
        upsert=False
    )

    # Return result
    return {
        "score": score,
        "total": total_questions,
        "results": detailed_results
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
    requirements = {
    "Prilims-1": 0,
    "Prilims-2": 1,
    "Prilims-3": 2,
    "Medium": 3,
    "Hard": 4
}

    required_count = requirements[data.test]
    prev_tests = [r["test"] for r in await users.find({"userid": data.userid}).to_list(None)]

    if len(prev_tests) >= required_count:
       response = await users.insert_one({"name": data.name, "userid": data.userid, "didCheat": "NO", "department": data.department, "test": data.test})       
       jwt_token = create_access_token({"userid": data.userid, "name": data.name})
       return {"message": "Data Saved", "token": jwt_token }
    else:
       return {"message": "You haven’t attended the previous tests"}

      
          
class StudentID(BaseModel):
    userid: str
    jwt: str
@app.post("/cheat")
async def handle_cheat(data:StudentID):
    access = check_access_token(data.jwt)
    if access:
        response = await users.find_one_and_update({"userid": data.userid}, {"$set":{"didCheat": "YES"}})
        return {"message": "Cheat Added"}
    else:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")

class checkJWT(BaseModel):
    jwt: str

@app.post("/fetch-student-details")
async def handle_student_details(data:checkJWT):
  access = check_access_token(data.jwt)
  if not access:
    raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")

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
  jwt: str

@app.post("/api/add-questions")
async def handle_add_questions(data: newAdd):
    access = check_access_token(data.jwt)
    if not access:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")

    new_questions = [q.dict() for q in data.Question]

    # Fetch the test document once
    test_doc = await questions.find_one({"test": data.test})
    if not test_doc:
        insert_new = await questions.insert_one({"test": data.test, "questions":new_questions })
        return {"message": "New Test Created"}

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
   access = check_access_token(data.jwt)
   if not access:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")
   response = await questions.delete_one({"test": data.test})
   return {"Message": "Questions Deleted Successfully"}

class Fetch_Questions(BaseModel):
  test: str
  jwt: str
  
@app.post("/fetch-questions")
async def handle_fetch_questions(data:Fetch_Questions):
  access = check_access_token(data.jwt)
  if not access:
        raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")
  response = await questions.find_one({"test": data.test})
  response["_id"] = str(response["_id"])
  return {"message": response}

class userdelete(BaseModel):
  reg: str
  jwt: str
  
@app.post("/delete-user")
async def handle_user_deletion(data:userdelete):
  access = check_access_token(data.jwt)
  if not access:
    raise HTTPException(status_code=404, detail="AUTHORIZATION REJECTED")
  response = await users.delete_one({"userid": data.reg})
  return {"message": "User Deleted Successfully"} 

class staffLogin(BaseModel):
    name:str
    staffId: str
    role: str
    
@app.post("/staffs-login")
async def handle_staffs_login(data:staffLogin):
    if data.role == "HOD":
        find = await staffs.find_one({"role": "HOD"})
        if find:
            if data.staffId == find["staffId"]:
                 jwt = create_access_token({"name": data.name, "staffId": data.staffId})
                 return {"message": "Login Accepted", "token": jwt}
            else:
                return {"message": "Invalid Staff ID"}
        else:
            respond = await staffs.insert_one({"name": data.name, "staffId": data.staffId, "role": data.role})
            jwt = create_access_token({"name": data.name, "staffId": data.staffId})
            return {"message": "Account created", "token": jwt}
    else:        
        response = await staffs.find_one({"staffId": data.staffId})
        if response:
           jwt = create_access_token({"name": data.name, "staffId": data.staffId})
           return {"message": "Login Accepted"}
        else:
           respond = await staffs.insert_one({"name": data.name, "staffId": data.staffId, "role": data.role})
           jwt = create_access_token({"name": data.name, "staffId": data.staffId})
           return {"message": "Account created", "token": jwt}
       
@app.get("/fetch-options")
async def fetch_options():
    response = await questions.find().to_list(length=None)
    options = []
    for res in response:
        options.append(res["test"])
    return {"options":options }