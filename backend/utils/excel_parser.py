"""
Excel parser — reads enrollment + name, merges with PDF SGPA data.
Flexible column detection: looks for enrollment patterns and name-like headers.
"""
import re
from typing import List, Dict, Tuple
from ..models.student import Student

try:
    import openpyxl
except ImportError:
    openpyxl = None

ENROLLMENT_RE = re.compile(r'^\d{10,13}$')
NAME_HINTS = {"name", "student", "candidate", "sname", "studentname"}


def _is_enrollment(value) -> bool:
    return bool(value and ENROLLMENT_RE.match(str(value).strip()))


def _detect_columns(header_row) -> Tuple[int, int]:
    enrollment_idx = name_idx = None
    for i, cell in enumerate(header_row):
        val = str(cell).strip().lower().replace(" ", "") if cell else ""
        if any(hint in val for hint in NAME_HINTS):
            name_idx = i
        if "enroll" in val or "rollno" in val or "roll" in val:
            enrollment_idx = i
    return enrollment_idx, name_idx


def parse_excel(excel_path: str) -> List[Dict[str, str]]:
    """Returns [{enrollment, name}, ...]"""
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    rows = list(wb.active.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    enr_idx, name_idx = _detect_columns(rows[0])
    results = []

    for row in rows[1:]:
        if not row or all(c is None for c in row):
            continue

        enrollment = name = None

        if enr_idx is not None and name_idx is not None:
            enrollment = str(row[enr_idx]).strip() if row[enr_idx] else None
            name = str(row[name_idx]).strip() if row[name_idx] else None
        else:
            for i, cell in enumerate(row):
                if cell and _is_enrollment(cell):
                    enrollment = str(cell).strip()
                    for j in [i - 1, i + 1]:
                        if 0 <= j < len(row) and row[j]:
                            candidate = str(row[j]).strip()
                            if not candidate.isdigit():
                                name = candidate
                                break
                    break

        if enrollment and _is_enrollment(enrollment):
            results.append({"enrollment": enrollment, "name": name or "Unknown"})

    return results


def merge_data(
    excel_records: List[Dict[str, str]],
    pdf_records: List[Dict],
) -> Tuple[List[Student], List[str]]:
    """Join Excel names with PDF SGPAs on enrollment. Returns (students, warnings)."""
    pdf_map = {r["enrollment"]: r["sgpa"] for r in pdf_records}
    excel_map = {r["enrollment"]: r["name"] for r in excel_records}

    students = []
    warnings = []

    for enrollment, name in excel_map.items():
        sgpa = pdf_map.get(enrollment)
        if sgpa is None:
            warnings.append(f"No SGPA for {enrollment} ({name}) — skipped")
            continue
        students.append(Student(enrollment=enrollment, name=name, cgpa=sgpa))

    for enrollment in pdf_map:
        if enrollment not in excel_map:
            warnings.append(f"{enrollment} in PDF but not in Excel — skipped")

    return students, warnings
