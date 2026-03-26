"""
Dummy data generator
--------------------
Generates N students with random CGPAs (uniform 4.0–10.0).
Used for development and testing when real PDF/Excel data is not available.

Produces realistic-looking enrollment numbers and names.
Seed is fixed so results are reproducible across runs.
"""
import random
from typing import List
from ..models.student import Student

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Amit", "Ananya", "Anjali", "Arjun", "Aryan",
    "Ayesha", "Deepak", "Deepika", "Divya", "Gaurav", "Harsh", "Ishaan",
    "Ishita", "Karan", "Kavya", "Kunal", "Lakshmi", "Manish", "Meera",
    "Mohit", "Neha", "Nikhil", "Nisha", "Pankaj", "Pooja", "Priya", "Rahul",
    "Raj", "Rajesh", "Riya", "Rohit", "Sachin", "Sakshi", "Sanjay", "Sara",
    "Shivam", "Shreya", "Simran", "Sneha", "Sonam", "Suresh", "Tanvi",
    "Tushar", "Uday", "Varun", "Vikram", "Vishal",
]

LAST_NAMES = [
    "Agarwal", "Bansal", "Bhatt", "Chandra", "Chauhan", "Choudhary",
    "Dubey", "Gandhi", "Garg", "Gupta", "Jain", "Joshi", "Kapoor",
    "Kaur", "Khan", "Kumar", "Malhotra", "Mehta", "Mishra", "Nair",
    "Pandey", "Patel", "Pathak", "Rastogi", "Saxena", "Sharma", "Singh",
    "Sinha", "Srivastava", "Tiwari", "Tripathi", "Varma", "Verma", "Yadav",
]


def generate_dummy_students(n: int = 576, seed: int = 42) -> List[Student]:
    """
    Generate n students with random CGPAs.
    Enrollment format: 20210XXXXX (10 digits, year prefix 2021).
    """
    rng = random.Random(seed)
    students = []

    for i in range(n):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        name = f"{first} {last}"
        enrollment = f"2021{str(1000 + i).zfill(5)}"   # e.g. 2021001000
        cgpa = round(rng.uniform(4.0, 10.0), 2)

        students.append(Student(
            enrollment=enrollment,
            name=name,
            cgpa=cgpa,
        ))

    return students
