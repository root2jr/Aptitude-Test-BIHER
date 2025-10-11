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
    "http://localhost:3000", # Default for Create React App
    "http://localhost:5173", # Default for Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- 3. LOAD QUESTIONS FROM JSON FILE ---
# This loads all questions into memory when the server starts.
questions_db = [
  {
    "id": 1,
    "question": "A train running at the speed of 60 km/hr crosses a pole in 9 seconds. What is the length of the train?",
    "options": ["120 metres", "150 metres", "180 metres", "210 metres"],
    "answer": "150 metres"
  },
  {
    "id": 2,
    "question": "What is the next number in the series: 3, 7, 15, 31, 63, ?",
    "options": ["127", "125", "131", "97"],
    "answer": "127"
  },
  {
    "id": 3,
    "question": "If 'APPLE' is coded as 25563 and 'RUNG' is coded as 7148, then 'PURPLE' is coded as:",
    "options": ["517563", "517536", "517653", "617563"],
    "answer": "517563"
  },
  {
    "id": 4,
    "question": "The cost price of 20 articles is the same as the selling price of x articles. If the profit is 25%, then the value of x is:",
    "options": ["15", "16", "18", "25"],
    "answer": "16"
  },
  {
    "id": 5,
    "question": "Find the missing number in the sequence: 4, 18, ?, 100, 180, 294.",
    "options": ["32", "36", "48", "40"],
    "answer": "48"
  },
  {
    "id": 6,
    "question": "A can do a piece of work in 10 days, and B can do it in 15 days. In how many days will they do it together?",
    "options": ["5 days", "6 days", "8 days", "9 days"],
    "answer": "6 days"
  },
  {
    "id": 7,
    "question": "What is the average of the first five prime numbers?",
    "options": ["5", "5.6", "6", "4.8"],
    "answer": "5.6"
  },
  {
    "id": 8,
    "question": "A student scored 80% in a test with a maximum of 500 marks. How many marks did the student get?",
    "options": ["350", "380", "400", "420"],
    "answer": "400"
  },
  {
    "id": 9,
    "question": "What is the area of a circle with a radius of 7 cm? (Use π = 22/7)",
    "options": ["144 sq.cm", "154 sq.cm", "164 sq.cm", "174 sq.cm"],
    "answer": "154 sq.cm"
  },
  {
    "id": 10,
    "question": "Two numbers are in the ratio 3:5. If their sum is 80, what is the smaller number?",
    "options": ["20", "30", "40", "50"],
    "answer": "30"
  },
  {
    "id": 11,
    "question": "Pointing to a photograph, a man said, 'I have no brother, but that man's father is my father's son.' Whose photograph was it?",
    "options": ["His son's", "His father's", "His nephew's", "His own"],
    "answer": "His son's"
  },
  {
    "id": 12,
    "question": "Find the next term in the series: A, C, E, G, ?",
    "options": ["H", "I", "J", "K"],
    "answer": "I"
  },
  {
    "id": 13,
    "question": "A shopkeeper buys an article for $200 and sells it for $250. What is his profit percentage?",
    "options": ["20%", "25%", "30%", "15%"],
    "answer": "25%"
  },
  {
    "id": 14,
    "question": "Which word does NOT belong with the others?",
    "options": ["Inch", "Ounce", "Centimeter", "Yard"],
    "answer": "Ounce"
  },
  {
    "id": 15,
    "question": "Find the simple interest on $800 for 3 years at 5% per annum.",
    "options": ["$100", "$110", "$120", "$130"],
    "answer": "$120"
  },
  {
    "id": 16,
    "question": "If a car travels 450 km in 9 hours, what is its speed in km/hr?",
    "options": ["40 km/hr", "45 km/hr", "50 km/hr", "55 km/hr"],
    "answer": "50 km/hr"
  },
  {
    "id": 17,
    "question": "What is 35% of 600?",
    "options": ["180", "210", "240", "200"],
    "answer": "210"
  },
  {
    "id": 18,
    "question": "The sum of the ages of a father and son is 60 years. Six years ago, the father's age was five times the age of the son. What will be the son's age after 6 years?",
    "options": ["14 years", "20 years", "22 years", "18 years"],
    "answer": "20 years"
  },
  {
    "id": 19,
    "question": "Look at this series: 8, 6, 9, 23, 87, ... What number should come next?",
    "options": ["128", "226", "324", "429"],
    "answer": "429"
  },
  {
    "id": 20,
    "question": "Choose the word which is the best synonym for 'AMBIGUOUS'.",
    "options": ["Clear", "Unclear", "Certain", "Bright"],
    "answer": "Unclear"
  },
  {
    "id": 21,
    "question": "Choose the word which is the best antonym for 'EXPAND'.",
    "options": ["Widen", "Enlarge", "Contract", "Stretch"],
    "answer": "Contract"
  },
  {
    "id": 22,
    "question": "A boat can travel with a speed of 13 km/hr in still water. If the speed of the stream is 4 km/hr, find the time taken by the boat to go 68 km downstream.",
    "options": ["2 hours", "3 hours", "4 hours", "5 hours"],
    "answer": "4 hours"
  },
  {
    "id": 23,
    "question": "If 3 men or 6 boys can do a piece of work in 10 days, in how many days can 6 men and 2 boys do the work?",
    "options": ["4 days", "5 days", "6 days", "3 days"],
    "answer": "3 days"
  },
  {
    "id": 24,
    "question": "What is the smallest number which when divided by 6, 9, and 12 leaves a remainder of 1 in each case?",
    "options": ["37", "73", "109", "181"],
    "answer": "37"
  },
  {
    "id": 25,
    "question": "A man walks 5 km toward the south and then turns to the right. After walking 3 km he turns to the left and walks 5 km. In which direction is he now from the starting point?",
    "options": ["West", "South", "North-East", "South-West"],
    "answer": "South-West"
  },
  {
    "id": 26,
    "question": "The average of 5 numbers is 20. If one number is removed, the average becomes 23. What is the removed number?",
    "options": ["10", "12", "8", "9"],
    "answer": "8"
  },
  {
    "id": 27,
    "question": "Paw is to Cat as Hoof is to ______?",
    "options": ["Horse", "Dog", "Bird", "Lion"],
    "answer": "Horse"
  },
  {
    "id": 28,
    "question": "What is the perimeter of a rectangle with a length of 15 cm and a width of 10 cm?",
    "options": ["25 cm", "50 cm", "150 cm", "40 cm"],
    "answer": "50 cm"
  },
  {
    "id": 29,
    "question": "Find the missing term in the series: 2, 5, 10, 17, 26, ?",
    "options": ["35", "36", "37", "38"],
    "answer": "37"
  },
  {
    "id": 30,
    "question": "If 5 pipes can fill a tank in 120 minutes, then 6 pipes will fill it in ______.",
    "options": ["100 minutes", "144 minutes", "90 minutes", "110 minutes"],
    "answer": "100 minutes"
  },
  {
    "id": 31,
    "question": "If 'WATER' is written as 'YCVGT', how is 'EARTH' written in that code?",
    "options": ["GCTVJ", "GCTVI", "FCSUI", "GDSVK"],
    "answer": "GCTVJ"
  },
  {
    "id": 32,
    "question": "A number when increased by 20% gives 240. What is the number?",
    "options": ["180", "200", "220", "192"],
    "answer": "200"
  },
  {
    "id": 33,
    "question": "Choose the word that is a synonym for 'EFFICIENT'.",
    "options": ["Lazy", "Slow", "Effective", "Weak"],
    "answer": "Effective"
  },
  {
    "id": 34,
    "question": "What is the probability of getting a 'head' when a single coin is tossed?",
    "options": ["1", "0", "1/2", "1/4"],
    "answer": "1/2"
  },
  {
    "id": 35,
    "question": "If x/4 + 5 = 10, what is the value of x?",
    "options": ["15", "20", "25", "30"],
    "answer": "20"
  },
  {
    "id": 36,
    "question": "Find the odd one out: Triangle, Square, Circle, Rectangle.",
    "options": ["Triangle", "Square", "Circle", "Rectangle"],
    "answer": "Circle"
  },
  {
    "id": 37,
    "question": "What is the Least Common Multiple (LCM) of 12 and 15?",
    "options": ["3", "30", "60", "180"],
    "answer": "60"
  },
  {
    "id": 38,
    "question": "A man is facing North. He turns 90 degrees clockwise, then 135 degrees anti-clockwise. Which direction is he facing now?",
    "options": ["North", "West", "North-West", "South-East"],
    "answer": "North-West"
  },
  {
    "id": 39,
    "question": "Choose the word that is an antonym for 'BRAVE'.",
    "options": ["Bold", "Courageous", "Timid", "Strong"],
    "answer": "Timid"
  },
  {
    "id": 40,
    "question": "The sum of the ages of Ram and Shyam is 40. Ram is 10 years older than Shyam. What is Shyam's age?",
    "options": ["10 years", "15 years", "20 years", "25 years"],
    "answer": "15 years"
  },
  {
    "id": 41,
    "question": "If the price of a book is first decreased by 25% and then increased by 20%, what is the net change in the price?",
    "options": ["10% decrease", "5% decrease", "No change", "10% increase"],
    "answer": "10% decrease"
  },
  {
    "id": 42,
    "question": "What is the value of (81)^0.25?",
    "options": ["3", "9", "27", "81"],
    "answer": "3"
  },
  {
    "id": 43,
    "question": "A, B, C, D, and E are sitting in a row. A is between E and B. C is at the right end. Who is at the left end if D is not next to C?",
    "options": ["A", "B", "D", "E"],
    "answer": "D"
  },
  {
    "id": 44,
    "question": "In a class of 60 students, 45% are girls. The number of boys in the class is:",
    "options": ["27", "33", "30", "25"],
    "answer": "33"
  },
  {
    "id": 45,
    "question": "Which of the following is a prime number?",
    "options": ["51", "87", "91", "97"],
    "answer": "97"
  },
  {
    "id": 46,
    "question": "An insect crawls 10m North, then turns left and crawls 24m. How far is it from its starting point?",
    "options": ["14m", "26m", "34m", "20m"],
    "answer": "26m"
  },
  {
    "id": 47,
    "question": "What is the next term in the alphabet series: Z, X, V, T, R, ...?",
    "options": ["P", "Q", "S", "O"],
    "answer": "P"
  },
  {
    "id": 48,
    "question": "Complete the analogy: Book is to Read as Fork is to ____.",
    "options": ["Cut", "Spoon", "Eat", "Plate"],
    "answer": "Eat"
  },
  {
    "id": 49,
    "question": "If 1st January 2024 was a Monday, what day of the week will 15th January 2024 be?",
    "options": ["Sunday", "Monday", "Tuesday", "Wednesday"],
    "answer": "Monday"
  },
  {
    "id": 50,
    "question": "A man buys a cycle for $1400 and sells it at a loss of 15%. What is the selling price of the cycle?",
    "options": ["$1190", "$1200", "$1210", "$1160"],
    "answer": "$1190"
  },
  {
    "id": 51,
    "question": "Statements: 1. All cats are animals. 2. All tigers are cats. Conclusion: All tigers are animals.",
    "options": ["True", "False", "Cannot be determined", "Irrelevant"],
    "answer": "True"
  },
  {
    "id": 52,
    "question": "Imagine a 3x3 grid. A dot moves one step clockwise around the outer edge with each turn. If it starts in the top-left square, where will it be after 3 moves?",
    "options": ["Top-right", "Bottom-right", "Bottom-left", "Middle-right"],
    "answer": "Bottom-right"
  },
  {
    "id": 53,
    "question": "A survey of 100 students found 70 own a laptop and 50 own a tablet. If everyone owns at least one device, how many own both?",
    "options": ["10", "20", "30", "40"],
    "answer": "20"
  },
  {
    "id": 54,
    "question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?",
    "options": ["A dream", "A map", "A book", "A photograph"],
    "answer": "A map"
  },
  {
    "id": 55,
    "question": "If yesterday was Friday's tomorrow, what day is it today?",
    "options": ["Saturday", "Sunday", "Monday", "Friday"],
    "answer": "Sunday"
  },
  {
    "id": 56,
    "question": "Statement: 'Please use the stairs; the elevator is out of service.' What is the most logical assumption?",
    "options": ["People need to go to another floor", "Using stairs is safer", "The elevator will be fixed soon", "The building is old"],
    "answer": "People need to go to another floor"
  },
  {
    "id": 57,
    "question": "An item costs $80 and is on sale for 25% off. You also have a coupon for an additional 10% off the sale price. What is the final price?",
    "options": ["$54", "$60", "$52", "$50"],
    "answer": "$54"
  },
  {
    "id": 58,
    "question": "Rearrange the letters of 'OCEAN' to form a common watercraft.",
    "options": ["Boat", "Ship", "Canoe", "Yacht"],
    "answer": "Canoe"
  },
  {
    "id": 59,
    "question": "A sequence of shapes follows a pattern of increasing sides: Triangle, Square, Pentagon. What comes next?",
    "options": ["Circle", "Hexagon", "Octagon", "Heptagon"],
    "answer": "Hexagon"
  },
  {
    "id": 60,
    "question": "Which of the following capital letters appears the same when viewed in a mirror?",
    "options": ["F", "S", "A", "R"],
    "answer": "A"
  },
  {
    "id": 61,
    "question": "If 5 cats can catch 5 mice in 5 minutes, how many cats are needed to catch 100 mice in 100 minutes?",
    "options": ["100", "50", "20", "5"],
    "answer": "5"
  },
  {
    "id": 62,
    "question": "You are in a race and you overtake the second person. What position are you in now?",
    "options": ["First", "Second", "Third", "Last"],
    "answer": "Second"
  },
  {
    "id": 63,
    "question": "There are 8 apples in a basket. You take 3. How many apples do you have?",
    "options": ["3", "5", "8", "11"],
    "answer": "3"
  },
  {
    "id": 64,
    "question": "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    "options": ["$0.10", "$0.05", "$1.00", "$0.50"],
    "answer": "$0.05"
  },
  {
    "id": 65,
    "question": "Find the number that best completes the analogy: 8:4 as 10:?",
    "options": ["3", "7", "5", "6"],
    "answer": "5"
  },
  {
    "id": 66,
    "question": "A farmer had 17 sheep. All but 9 died. How many are left?",
    "options": ["8", "17", "9", "26"],
    "answer": "9"
  },
  {
    "id": 67,
    "question": "Which of the following is least like the others?",
    "options": ["Apple", "Banana", "Carrot", "Grape"],
    "answer": "Carrot"
  },
  {
    "id": 68,
    "question": "A family has five sons, and each son has one sister. How many children are in the family?",
    "options": ["10", "11", "5", "6"],
    "answer": "6"
  },
  {
    "id": 69,
    "question": "The day before yesterday was Saturday. What day will it be the day after tomorrow?",
    "options": ["Tuesday", "Wednesday", "Thursday", "Friday"],
    "answer": "Wednesday"
  },
  {
    "id": 70,
    "question": "What is the result of dividing 30 by half and adding 10?",
    "options": ["25", "5", "70", "45"],
    "answer": "70"
  },
  {
    "id": 71,
    "question": "Which number should come next in the pattern: 3, 3, 5, 4, 4, 3, 5, 5, 4, ...?",
    "options": ["2", "3", "4", "5"],
    "answer": "4"
  },
  {
    "id": 72,
    "question": "How many months have 28 days?",
    "options": ["1", "2", "6", "All 12"],
    "answer": "All 12"
  },
  {
    "id": 73,
    "question": "If you were to write down all the numbers from 1 to 100, how many times would you write the number 9?",
    "options": ["10", "11", "19", "20"],
    "answer": "20"
  },
  {
    "id": 74,
    "question": "A doctor gives you 3 pills and tells you to take one every half an hour. How long would the pills last?",
    "options": ["90 minutes", "60 minutes", "30 minutes", "120 minutes"],
    "answer": "60 minutes"
  },
  {
    "id": 75,
    "question": "A clerk at a butcher shop is 5'10\" tall. What does he weigh?",
    "options": ["Meat", "180 lbs", "Depends on his diet", "Not enough information"],
    "answer": "Meat"
  },
  {
    "id": 76,
    "question": "Question: What is the value of x? Statement I: x + y = 12. Statement II: x - y = 4.",
    "options": ["Statement I alone is sufficient", "Statement II alone is sufficient", "Both statements together are needed", "Data is insufficient"],
    "answer": "Both statements together are needed"
  },
  {
    "id": 77,
    "question": "A square rotating 45 degrees becomes a diamond. What does a circle become when it is rotated 45 degrees?",
    "options": ["An oval", "A sphere", "A circle", "An ellipse"],
    "answer": "A circle"
  },
  {
    "id": 78,
    "question": "Statement I: Ice cream sales increased this month. Statement II: The average temperature was higher this month. What is the relationship?",
    "options": ["I is the cause of II", "II is the cause of I", "Both are independent", "Both are effects of a third cause"],
    "answer": "II is the cause of I"
  },
  {
    "id": 79,
    "question": "A man who lives on the 20th floor takes the elevator to the 10th floor and walks the rest of the way up. On his way down, he takes the elevator all the way. Why?",
    "options": ["He enjoys walking", "The elevator is slow", "He is too short to reach the '20' button", "He is training for a race"],
    "answer": "He is too short to reach the '20' button"
  },
  {
    "id": 80,
    "question": "Tom, Sam, and Ken are a doctor, lawyer, and pilot. Tom is not the lawyer. Sam is not the pilot. The pilot's name is not Tom. Who is the doctor?",
    "options": ["Tom", "Sam", "Ken", "Cannot be determined"],
    "answer": "Tom"
  },
  {
    "id": 81,
    "question": "Argument: 'My friend is a good driver, so all people from his city must be good drivers.' This is an example of what?",
    "options": ["Sound Logic", "Hasty Generalization", "Slippery Slope", "Circular Reasoning"],
    "answer": "Hasty Generalization"
  },
  {
    "id": 82,
    "question": "You have a 5-liter jug and a 3-liter jug. You fill the 5L jug and pour it into the 3L jug until it's full. How much water is left in the 5L jug?",
    "options": ["1L", "2L", "3L", "4L"],
    "answer": "2L"
  },
  {
    "id": 83,
    "question": "Find the next number in the series: 2, 6, 18, 54, ...?",
    "options": ["108", "162", "216", "152"],
    "answer": "162"
  },
  {
    "id": 84,
    "question": "If A=1, B=2, C=3, and so on, what is the sum of the letters in the word 'CAB'?",
    "options": ["312", "5", "6", "24"],
    "answer": "6"
  },
  {
    "id": 85,
    "question": "A paper is folded in half, and then folded in half again. A hole is punched through the center. How many holes will there be when the paper is unfolded?",
    "options": ["1", "2", "3", "4"],
    "answer": "4"
  },
  {
    "id": 86,
    "question": "A watch reads 3:15. If the minute hand points East, in which direction does the hour hand point?",
    "options": ["North", "South", "North-East", "South-West"],
    "answer": "North-East"
  },
  {
    "id": 87,
    "question": "If 'some cats are pets' is a true statement, what can be definitively concluded?",
    "options": ["All pets are cats", "Some pets are cats", "No cats are pets", "All cats are pets"],
    "answer": "Some pets are cats"
  },
  {
    "id": 88,
    "question": "What is the maximum number of times you can subtract 5 from 25?",
    "options": ["5", "20", "1", "As many times as you want"],
    "answer": "1"
  },
  {
    "id": 89,
    "question": "There are six glasses in a row. The first three are full of water, the next three are empty. By moving only one glass, can you arrange them so empty and full glasses alternate?",
    "options": ["Yes, pour glass 2 into glass 5", "Yes, pour glass 1 into glass 6", "Yes, swap glass 2 and 5", "No, it's impossible"],
    "answer": "Yes, pour glass 2 into glass 5"
  },
  {
    "id": 90,
    "question": "Which of these words is the 'odd one out' based on its vowel pattern: TEAM, BOAT, SUIT, ROAD?",
    "options": ["TEAM", "BOAT", "SUIT", "ROAD"],
    "answer": "SUIT"
  },
  {
    "id": 91,
    "question": "A tree doubles in height every year. If it takes 10 years for the tree to reach its full height, how many years did it take to reach half its full height?",
    "options": ["5 years", "2 years", "9 years", "7 years"],
    "answer": "9 years"
  },
  {
    "id": 92,
    "question": "What number logically follows this sequence: 4, 6, 9, 6, 14, 6, ...?",
    "options": ["6", "17", "19", "21"],
    "answer": "19"
  },
  {
    "id": 93,
    "question": "A man has to be at work at 9:00 a.m. It takes him 15 minutes to get dressed, 20 minutes to eat, and 35 minutes to walk to work. What time should he get up?",
    "options": ["7:50 a.m.", "8:00 a.m.", "7:45 a.m.", "7:30 a.m."],
    "answer": "7:50 a.m."
  },
  {
    "id": 94,
    "question": "In a certain code, 'pen' is 'pencil', 'pencil' is 'book', and 'book' is 'paper'. In this code, what would you write with?",
    "options": ["pen", "pencil", "book", "paper"],
    "answer": "pencil"
  },
  {
    "id": 95,
    "question": "Which three of the following numbers have a sum of 30? (1, 3, 5, 7, 9, 11, 13, 15)",
    "options": ["1+13+15", "5+9+15", "7+11+13", "It's impossible"],
    "answer": "It's impossible"
  },
  {
    "id": 96,
    "question": "What is the center of gravity?",
    "options": ["The letter 'V'", "The Sun", "A specific point in an object", "The Earth's core"],
    "answer": "The letter 'V'"
  },
  {
    "id": 97,
    "question": "How many squares are on a standard chessboard?",
    "options": ["64", "65", "128", "204"],
    "answer": "204"
  },
  {
    "id": 98,
    "question": "A lily pad in a pond doubles in size every day. If it covers the entire pond in 48 days, on which day did it cover half the pond?",
    "options": ["Day 24", "Day 47", "Day 12", "Day 36"],
    "answer": "Day 47"
  },
  {
    "id": 99,
    "question": "What comes once in a minute, twice in a moment, but never in a thousand years?",
    "options": ["The number 1000", "The letter 'M'", "A second", "An idea"],
    "answer": "The letter 'M'"
  },
  {
    "id": 100,
    "question": "A boy is two years old. His brother is half his age. When the boy is 100 years old, what will be his brother's age?",
    "options": ["50", "99", "101", "98"],
    "answer": "99"
  }
]

correct_answers_db = {q["id"]: q["answer"] for q in questions_db}
url = os.getenv("url")
cluster = AsyncIOMotorClient(url)
db = cluster["Aptitude_Test_BIHER"]
users = db["Users"]


class QuestionForClient(BaseModel):
    """The question format sent to the client. Notice 'answer' is NOT included."""
    id: int
    question: str
    options: List[str]

class UserAnswers(BaseModel):
    """The format for receiving answers from the client."""
    answers: Dict[int, str]


# --- 5. DEFINE API ENDPOINTS ---

@app.get("/api/questions", response_model=List[QuestionForClient])
def get_shuffled_questions():
    """
    This endpoint provides the questions for the test.
    It shuffles the order of questions and the order of options for each question
    to make cheating more difficult. It NEVER sends the answers.
    """
    # Create a deep copy to avoid modifying the original list in memory
    questions_copy = [q.copy() for q in questions_db]
    
    # Shuffle the list of questions
    random.shuffle(questions_copy)
    
    # Shuffle the options within each question
    for question in questions_copy:
        random.shuffle(question["options"])
        
    return questions_copy

@app.post("/api/submit")
def submit_answers(user_answers: UserAnswers):
    """
    This endpoint receives the user's answers, calculates the score securely
    on the server, and returns the finl result.
    """
    score = 0
    submitted = user_answers.answers

    # Iterate through the submitted answers and compare with the correct ones
    for question_id, user_answer in submitted.items():
        # Check if the submitted answer for the given question ID is correct
        if correct_answers_db.get(question_id) == user_answer:
            score += 1
            
    return {
        "score": score,
        "total": len(questions_db)
    }

@app.get("/")
def read_root():
    return {"message": f"Welcome to the Aptitude Test API. {len(questions_db)} questions loaded."}


class User(BaseModel):
    name: str
    userid: str
    didCheat: str
@app.post("/users")
async def handle_user(data:User):
    response = await users.insert_one({"name": data.name, "userid": data.userid, "didCheat": "NO"})
    return {"message": "Data Saved"}
class StudentID(BaseModel):
    userid: str
@app.post("/cheat")
async def handle_cheat(data:StudentID):
    response = await users.find_one_and_update({"userid": data.userid}, {"$set":{"didCheat": "YES"}})
    return {"message": "Cheat Added"}
