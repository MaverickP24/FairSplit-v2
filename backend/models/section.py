from dataclasses import dataclass, field
from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .student import Student


@dataclass
class Section:
    name: str
    members: List["Student"] = field(default_factory=list)
    tier_set: Set[int] = field(default_factory=set)

    @property
    def size(self) -> int:
        return len(self.members)

    @property
    def total_rank_points(self) -> float:
        return sum(s.rank_points for s in self.members)

    def has_tier(self, tier: int) -> bool:
        return tier in self.tier_set

    def add(self, student: "Student") -> None:
        self.members.append(student)
        self.tier_set.add(student.tier)
        student.section = self.name

    def remove(self, student: "Student") -> None:
        self.members.remove(student)
        self.tier_set = {s.tier for s in self.members}
        student.section = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size": self.size,
            "total_rank_points": self.total_rank_points,
            "members": [s.to_dict() for s in self.members],
        }
