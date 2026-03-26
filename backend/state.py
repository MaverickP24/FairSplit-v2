"""
In-memory state store.
In production, replace with Redis or a database.
"""
from typing import Dict, List, Optional
from .models.student import Student
from .models.section import Section

class AppState:
    def __init__(self):
        self.students: List[Student] = []
        self.sections: List[Section] = []
        self.allocation_done: bool = False
        self.warnings: List[str] = []
        self.optimizer_stats: dict = {}

    def reset(self):
        self.__init__()

    def student_map(self) -> Dict[str, Student]:
        return {s.enrollment: s for s in self.students}

state = AppState()
