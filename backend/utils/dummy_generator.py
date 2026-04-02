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
    rng = random.Random(seed)
    return [
        Student(
            enrollment=f"2021{str(1000 + i).zfill(5)}",
            name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
            cgpa=round(rng.uniform(4.0, 10.0), 2),
        )
        for i in range(n)
    ]
