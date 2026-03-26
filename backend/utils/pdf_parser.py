"""
PDF Parser
----------
Extracts Enrollment Number and SGPA from university result PDFs.

Strategy:
  1. Try table extraction first (pdfplumber). Most university PDFs are tabular.
  2. Fallback to regex line-by-line scan if table extraction yields nothing.

Expected PDF format (common in Indian universities):
  Columns: Roll No | Student Name | ... | SGPA
  The enrollment number is typically 10-13 digits.
  SGPA is a float like 8.5 or 9.23, in the last or second-to-last column.

Returns: List[dict] with keys "enrollment" and "sgpa"
"""
import re
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


ENROLLMENT_PATTERN = re.compile(r'\b(\d{10,13})\b')
SGPA_PATTERN = re.compile(r'\b([0-9](?:\.[0-9]{1,3})?|10(?:\.0{1,3})?)\b')


def _clean_sgpa(value: str) -> Optional[float]:
    """Parse and validate SGPA string. Must be between 0 and 10."""
    try:
        v = float(value.strip())
        if 0.0 <= v <= 10.0:
            return round(v, 3)
    except (ValueError, AttributeError):
        pass
    return None


def _extract_from_tables(pdf_path: str) -> List[Dict[str, float]]:
    """Try structured table extraction."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                for row in table:
                    if not row:
                        continue
                    # Find enrollment in any cell
                    enrollment = None
                    for cell in row:
                        if cell and ENROLLMENT_PATTERN.search(str(cell)):
                            enrollment = ENROLLMENT_PATTERN.search(str(cell)).group(1)
                            break
                    if not enrollment:
                        continue
                    # SGPA is typically in the last non-empty cell
                    non_empty = [c for c in reversed(row) if c and str(c).strip()]
                    for cell in non_empty:
                        sgpa = _clean_sgpa(str(cell))
                        if sgpa is not None:
                            results.append({
                                "enrollment": enrollment,
                                "sgpa": sgpa
                            })
                            break
    return results


def _extract_from_text(pdf_path: str) -> List[Dict[str, float]]:
    """Fallback: scan raw text line by line."""
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.split('\n'):
                enr_match = ENROLLMENT_PATTERN.search(line)
                if not enr_match:
                    continue
                enrollment = enr_match.group(1)
                # Find all float-like numbers, take the last one as SGPA
                numbers = SGPA_PATTERN.findall(line)
                if not numbers:
                    continue
                # Last valid SGPA candidate
                for candidate in reversed(numbers):
                    sgpa = _clean_sgpa(candidate)
                    if sgpa is not None:
                        results.append({
                            "enrollment": enrollment,
                            "sgpa": sgpa
                        })
                        break
    return results


def parse_pdf(pdf_path: str) -> List[Dict]:
    """
    Main entry point. Returns list of {"enrollment": str, "sgpa": float}.
    Deduplicates by enrollment (keeps last occurrence).
    Raises RuntimeError if pdfplumber is not installed.
    """
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is not installed. Run: pip install pdfplumber")

    results = _extract_from_tables(pdf_path)

    if not results:
        results = _extract_from_text(pdf_path)

    # Deduplicate — keep last seen (usually most recent semester)
    seen = {}
    for r in results:
        seen[r["enrollment"]] = r["sgpa"]

    return [{"enrollment": k, "sgpa": v} for k, v in seen.items()]
