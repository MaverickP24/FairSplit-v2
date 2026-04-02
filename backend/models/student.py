from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Student:
    enrollment: str
    name: str
    cgpa: float

    rank: int = 0
    tier: int = 0
    rank_points: float = 0.0

    # {enrollment: priority} where priority 1 = most wanted, weight = 11 - priority
    preferences: Dict[str, int] = field(default_factory=dict)

    section: Optional[str] = None

    def preference_weight(self, other_enrollment: str) -> float:
        p = self.preferences.get(other_enrollment)
        return (11 - p) if p is not None else 0.0

    def to_dict(self) -> dict:
        return {
            "enrollment": self.enrollment,
            "name": self.name,
            "cgpa": self.cgpa,
            "rank": self.rank,
            "tier": self.tier,
            "rank_points": self.rank_points,
            "section": self.section,
            "preferences": self.preferences,
        }
