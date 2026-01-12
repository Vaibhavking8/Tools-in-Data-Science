from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import csv

app = FastAPI()

# Enable CORS (allow any origin for GET requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Read the CSV file once at startup
students_data = []
with open("q-fastapi.csv", newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # Convert studentId to int for proper typing
        students_data.append({
            "studentId": int(row["studentId"]),
            "class": row["class"]
        })

@app.get("/api")
def get_students(class_: list[str] = Query(None, alias="class")):
    """
    Returns all students as JSON.
    If ?class=1A or ?class=1A&class=1B is specified,
    returns only students in those classes.
    """
    if class_:
        filtered = [s for s in students_data if s["class"] in class_]
        return {"students": filtered}
    return {"students": students_data}
