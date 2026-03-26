"""
Excel Parser + Data Merger
--------------------------
Reads enrollment number and name from Excel file, then merges with
PDF-extracted SGPA data to produce Student objects.

Excel expected columns (flexible detection):
  - Enrollment: column containing 10-13 digit numbers
  - Name: any column labelled "name", "student name", "candidate", etc.

Merge: enrollment number is the join key.
Students in Excel but missing from PDF are skipped with a warning.
Students in PDF but missing from Excel are also skipped.
"""
import re
from typing import List, Dict, Tuple
from ..models.student import Student

try:
    import openpyxl
except ImportError:
    openpyxl = None

ENROLLMENT_PATTERN = re.compile(r'^\d{10,13}$')
NAME_COLUMN_HINTS = {"name", "student", "candidate", "sname", "studentname"}


def _is_enrollment(value) -> bool:
    return bool(value and ENROLLMENT_PATTERN.match(str(value).strip()))


def _detect_columns(header_row) -> Tuple[int, int]:
    """
    Returns (enrollment_col_idx, name_col_idx) from header row.
    Falls back to positional detection if headers are non-standard.
    """
    enrollment_idx = None
    name_idx = None

    for i, cell in enumerate(header_row):
        val = str(cell).strip().lower().replace(" ", "") if cell else ""
        if any(hint in val for hint in NAME_COLUMN_HINTS):
            name_idx = i
        if "enroll" in val or "rollno" in val or "roll" in val:
            enrollment_idx = i

    return enrollment_idx, name_idx


def parse_excel(excel_path: str) -> List[Dict[str, str]]:
    """
    Returns list of {"enrollment": str, "name": str}
    """
    if openpyxl is None:
        raise RuntimeError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    if not rows:
        return []

    # Try to detect column positions from header
    enr_idx, name_idx = _detect_columns(rows[0])
    data_start = 1  # skip header row

    results = []

    for row in rows[data_start:]:
        if not row or all(c is None for c in row):
            continue

        # If column detection failed, scan each cell
        enrollment = None
        name = None

        if enr_idx is not None and name_idx is not None:
            enrollment = str(row[enr_idx]).strip() if row[enr_idx] else None
            name = str(row[name_idx]).strip() if row[name_idx] else None
        else:
            # Fallback: scan for enrollment pattern
            for i, cell in enumerate(row):
                if cell and _is_enrollment(cell):
                    enrollment = str(cell).strip()
                    # Name is likely the next or previous non-numeric cell
                    for j in [i - 1, i + 1]:
                        if 0 <= j < len(row) and row[j]:
                            candidate = str(row[j]).strip()
                            if not candidate.isdigit():
                                name = candidate
                                break
                    break

        if enrollment and _is_enrollment(enrollment):
            results.append({
                "enrollment": enrollment,
                "name": name or "Unknown"
            })

    wb.close()
    return results


def merge_data(
    excel_records: List[Dict[str, str]],
    pdf_records: List[Dict],
) -> Tuple[List[Student], List[str]]:
    """
    Merge Excel (enrollment, name) with PDF (enrollment, sgpa).
    Returns (students, warnings).
    """
    pdf_map = {r["enrollment"]: r["sgpa"] for r in pdf_records}
    excel_map = {r["enrollment"]: r["name"] for r in excel_records}

    students = []
    warnings = []

    for enrollment, name in excel_map.items():
        sgpa = pdf_map.get(enrollment)
        if sgpa is None:
            warnings.append(f"No SGPA found for {enrollment} ({name}) — skipped")
            continue
        students.append(Student(
            enrollment=enrollment,
            name=name,
            cgpa=sgpa,
        ))

    for enrollment in pdf_map:
        if enrollment not in excel_map:
            warnings.append(f"Enrollment {enrollment} in PDF but not in Excel — skipped")

    return students, warnings
