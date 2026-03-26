import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..state import state
from ..models.student import Student
from ..utils.pdf_parser import parse_pdf
from ..utils.excel_parser import parse_excel, merge_data
from ..core.ranker import assign_ranks

router = APIRouter()


@router.post("/ingest")
async def ingest_files(
    pdf_file: UploadFile = File(...),
    excel_file: UploadFile = File(...),
):
    """
    Upload result PDF and name Excel.
    Parses, merges, ranks students. Resets any prior allocation.
    """
    state.reset()

    # Save uploads to temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
        pdf_tmp.write(await pdf_file.read())
        pdf_path = pdf_tmp.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as xl_tmp:
        xl_tmp.write(await excel_file.read())
        xl_path = xl_tmp.name

    try:
        pdf_records = parse_pdf(pdf_path)
        excel_records = parse_excel(xl_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {str(e)}")
    finally:
        os.unlink(pdf_path)
        os.unlink(xl_path)

    if not pdf_records:
        raise HTTPException(status_code=422, detail="No student data extracted from PDF")
    if not excel_records:
        raise HTTPException(status_code=422, detail="No student data extracted from Excel")

    students, warnings = merge_data(excel_records, pdf_records)
    if not students:
        raise HTTPException(status_code=422, detail="No students matched between PDF and Excel")

    ranked = assign_ranks(students)
    state.students = ranked
    state.warnings = warnings

    return {
        "total_students": len(ranked),
        "warnings": warnings[:20],   # cap at 20 in response
        "preview": [s.to_dict() for s in ranked[:10]],
    }


@router.post("/ingest/json")
async def ingest_json(file: UploadFile = File(...)):
    """
    Upload a single JSON file with name, enrollment_number, and sgpa.
    Expected format: [{"name": "...", "enrollment_number": "...", "sgpa": 9.5}, ...]
    """
    state.reset()
    try:
        content = await file.read()
        data = json.loads(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"JSON parse error: {str(e)}")

    if not isinstance(data, list):
        raise HTTPException(status_code=422, detail="JSON must be a list of student objects")

    students = []
    for item in data:
        name = item.get("name")
        enrollment = item.get("enrollment_number")
        sgpa = item.get("sgpa")

        if not name or not enrollment or sgpa is None:
            continue

        students.append(Student(
            name=name,
            enrollment=enrollment,
            cgpa=float(sgpa)
        ))

    if not students:
        raise HTTPException(status_code=422, detail="No valid student records found in JSON")

    ranked = assign_ranks(students)
    state.students = ranked

    return {
        "total_students": len(ranked),
        "preview": [s.to_dict() for s in ranked[:10]],
    }


@router.get("/students")
def get_students():
    """Return all ranked students."""
    if not state.students:
        raise HTTPException(status_code=404, detail="No data loaded. Call /api/ingest first.")
    return {
        "total": len(state.students),
        "students": [s.to_dict() for s in state.students],
    }


@router.post("/ingest/dummy")
def ingest_dummy(n: int = 576, seed: int = 42):
    """
    Load dummy student data (no file upload needed).
    Useful for development and demos.

    Params:
      n    — number of students to generate (default 576)
      seed — random seed for reproducibility (default 42)
    """
    from ..utils.dummy_generator import generate_dummy_students

    state.reset()
    students = generate_dummy_students(n=n, seed=seed)
    ranked = assign_ranks(students)
    state.students = ranked

    tier_count = ranked[-1].tier if ranked else 0
    pts = {
        chr(65 + i): 0 for i in range(5)
    }  # placeholder — real pts after allocation

    return {
        "total_students": len(ranked),
        "seed": seed,
        "tiers": tier_count,
        "preview": [s.to_dict() for s in ranked[:10]],
        "message": f"Loaded {len(ranked)} dummy students. "
                   f"Run POST /api/allocate to assign sections.",
    }
