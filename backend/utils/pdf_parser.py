"""
PDF parser — extracts enrollment + SGPA from university result PDFs.
Tries table extraction first, falls back to regex line scan.
"""
import re
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

ENROLLMENT_RE = re.compile(r'\b(\d{10,13})\b')
SGPA_RE = re.compile(r'\b([0-9](?:\.[0-9]{1,3})?|10(?:\.0{1,3})?)\b')


def _clean_sgpa(value: str) -> Optional[float]:
    try:
        v = float(value.strip())
        return round(v, 3) if 0.0 <= v <= 10.0 else None
    except (ValueError, AttributeError):
        return None


def _extract_from_tables(pdf_path: str) -> List[Dict]:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue
                for row in table:
                    if not row:
                        continue
                    enrollment = None
                    for cell in row:
                        if cell and ENROLLMENT_RE.search(str(cell)):
                            enrollment = ENROLLMENT_RE.search(str(cell)).group(1)
                            break
                    if not enrollment:
                        continue
                    for cell in reversed([c for c in row if c and str(c).strip()]):
                        sgpa = _clean_sgpa(str(cell))
                        if sgpa is not None:
                            results.append({"enrollment": enrollment, "sgpa": sgpa})
                            break
    return results


def _extract_from_text(pdf_path: str) -> List[Dict]:
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").split('\n'):
                match = ENROLLMENT_RE.search(line)
                if not match:
                    continue
                enrollment = match.group(1)
                for candidate in reversed(SGPA_RE.findall(line)):
                    sgpa = _clean_sgpa(candidate)
                    if sgpa is not None:
                        results.append({"enrollment": enrollment, "sgpa": sgpa})
                        break
    return results


def parse_pdf(pdf_path: str) -> List[Dict]:
    """Returns [{enrollment, sgpa}, ...]. Deduplicates by enrollment (keeps last)."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber not installed. Run: pip install pdfplumber")

    results = _extract_from_tables(pdf_path) or _extract_from_text(pdf_path)

    seen = {}
    for r in results:
        seen[r["enrollment"]] = r["sgpa"]
    return [{"enrollment": k, "sgpa": v} for k, v in seen.items()]
