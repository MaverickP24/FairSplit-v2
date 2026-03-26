"""
PDF Debug Tool
--------------
Run this BEFORE deploying to understand your university's PDF structure.
It prints exactly what pdfplumber sees — tables, raw text, and extracted records.

Usage:
    python debug_pdf.py path/to/results.pdf

Output:
    - Page-by-page table structure
    - Raw text lines
    - What the parser would extract
    - Confidence score for each extracted record
"""
import sys
import re

try:
    import pdfplumber
except ImportError:
    print("Install pdfplumber first: pip install pdfplumber")
    sys.exit(1)

ENROLLMENT_PATTERN = re.compile(r'\b(\d{10,13})\b')
SGPA_PATTERN = re.compile(r'\b([0-9](?:\.[0-9]{1,3})?|10(?:\.0{1,3})?)\b')


def debug_pdf(path: str, max_pages: int = 3):
    print(f"\n{'='*60}")
    print(f"PDF DEBUG: {path}")
    print(f"{'='*60}\n")

    with pdfplumber.open(path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        pages_to_scan = min(max_pages, len(pdf.pages))
        print(f"Scanning first {pages_to_scan} pages...\n")

        all_extracted = []

        for page_num in range(pages_to_scan):
            page = pdf.pages[page_num]
            print(f"\n{'─'*50}")
            print(f"PAGE {page_num + 1}")
            print(f"{'─'*50}")

            # ── Table scan ────────────────────────────────────────
            tables = page.extract_tables()
            print(f"\n[Tables found: {len(tables)}]")

            for t_idx, table in enumerate(tables):
                print(f"\n  Table {t_idx + 1} ({len(table)} rows):")
                for r_idx, row in enumerate(table[:5]):  # first 5 rows
                    print(f"    Row {r_idx}: {row}")
                if len(table) > 5:
                    print(f"    ... ({len(table) - 5} more rows)")

                # Try to extract from this table
                table_records = []
                for row in table:
                    if not row:
                        continue
                    enrollment = None
                    for cell in row:
                        if cell and ENROLLMENT_PATTERN.search(str(cell)):
                            enrollment = ENROLLMENT_PATTERN.search(str(cell)).group(1)
                            break
                    if not enrollment:
                        continue
                    non_empty = [c for c in reversed(row) if c and str(c).strip()]
                    for cell in non_empty:
                        try:
                            v = float(str(cell).strip())
                            if 0.0 <= v <= 10.0:
                                table_records.append({
                                    "enrollment": enrollment,
                                    "sgpa": v,
                                    "source": f"p{page_num+1}_table{t_idx+1}"
                                })
                                break
                        except ValueError:
                            continue
                if table_records:
                    print(f"\n  Extracted from table {t_idx + 1}:")
                    for r in table_records[:3]:
                        print(f"    {r}")
                    all_extracted.extend(table_records)

            # ── Raw text scan ────────────────────────────────────
            text = page.extract_text() or ""
            lines = [l for l in text.split('\n') if l.strip()]
            print(f"\n[Raw text: {len(lines)} lines]")
            print("  First 10 lines:")
            for line in lines[:10]:
                print(f"    {repr(line)}")

            # Try text extraction
            text_records = []
            for line in lines:
                enr_match = ENROLLMENT_PATTERN.search(line)
                if not enr_match:
                    continue
                enrollment = enr_match.group(1)
                numbers = SGPA_PATTERN.findall(line)
                for candidate in reversed(numbers):
                    try:
                        v = float(candidate)
                        if 0.0 <= v <= 10.0:
                            text_records.append({
                                "enrollment": enrollment,
                                "sgpa": v,
                                "line": line.strip()[:80],
                                "source": f"p{page_num+1}_text"
                            })
                            break
                    except ValueError:
                        continue
            if text_records:
                print(f"\n  Text-extracted records (first 3):")
                for r in text_records[:3]:
                    print(f"    enr={r['enrollment']} sgpa={r['sgpa']}")
                    print(f"    line: {r['line']}")
                if not all_extracted:
                    all_extracted.extend(text_records)

    # ── Summary ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total records extracted: {len(all_extracted)}")
    if all_extracted:
        sgpa_vals = [r["sgpa"] for r in all_extracted]
        print(f"SGPA range: {min(sgpa_vals):.2f} – {max(sgpa_vals):.2f}")
        print(f"Sample records:")
        for r in all_extracted[:5]:
            print(f"  {r['enrollment']} → {r['sgpa']} (from {r['source']})")

        # Check for duplicates
        enrs = [r["enrollment"] for r in all_extracted]
        dupes = len(enrs) - len(set(enrs))
        if dupes:
            print(f"\nWARNING: {dupes} duplicate enrollments found (will keep last)")
        else:
            print(f"\nNo duplicates found.")
    else:
        print("\nNOTHING EXTRACTED.")
        print("Your PDF may need a custom parser. Common issues:")
        print("  1. Scanned PDF (image-only) — needs OCR (pytesseract)")
        print("  2. Enrollment numbers shorter/longer than 10-13 digits")
        print("  3. SGPA column not last — check column order above")
        print("  4. Non-standard encoding — check raw text output above")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf.py path/to/results.pdf [max_pages]")
        print("Example: python debug_pdf.py results.pdf 5")
        sys.exit(1)

    pdf_path = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    debug_pdf(pdf_path, max_pages)
