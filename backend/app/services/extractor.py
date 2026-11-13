"""
Report Extraction Pipeline for ReportSaathi.

Orchestrates:
1. Digital PDF extraction via pdfplumber (with pypdf fallback)
2. Scanned PDF fallback via OCR
3. Image file OCR (JPG, JPEG, PNG)
4. Structured tabular & regex-based lab parameter parsing
5. Privacy/PII sanitization
"""

import io
import re
import logging
from typing import List, Tuple, Optional, Dict, Any
import pdfplumber
import pypdf
from PIL import Image

from app.schemas.report import ExtractedParameter, PrivacyMaskingStatus, ExtractionResponse
from app.services.ocr import ocr_image_bytes, ocr_scanned_pdf
from app.utils.privacy import mask_pii

logger = logging.getLogger("reportsaathi.extractor")

# Known lab units for pattern matching
LAB_UNITS = [
    r"mg/dL", r"g/dL", r"mmol/L", r"µmol/L", r"umol/L", r"uIU/mL", r"mIU/L",
    r"10\^3/uL", r"10\^6/uL", r"10\^3/µL", r"10\^6/µL", r"x10\^3/uL", r"x10\^6/uL",
    r"/cumm", r"cells/cumm", r"cells/mcL", r"fl", r"fL", r"pg", r"%",
    r"U/L", r"IU/L", r"ng/mL", r"ug/dL", r"mcg/dL", r"mg/L", r"g/L",
    r"mEq/L", r"sec", r"seconds", r"ratio", r"copies/mL"
]
UNITS_REGEX = r"(?:" + "|".join(re.escape(u) for u in LAB_UNITS) + r")"

# Common lab test names to assist heuristic identification
COMMON_TEST_NAMES = [
    "hemoglobin", "haemoglobin", "hb", "rbc", "wbc", "platelet count", "platelets",
    "hematocrit", "pcv", "mcv", "mch", "mchc", "rdw",
    "neutrophils", "lymphocytes", "monocytes", "eosinophils", "basophils",
    "fasting blood glucose", "fasting blood sugar", "fbs", "post prandial blood glucose", "ppbs",
    "random blood sugar", "rbs", "hba1c", "glycated hemoglobin",
    "serum creatinine", "creatinine", "blood urea nitrogen", "bun", "uric acid",
    "total cholesterol", "hdl cholesterol", "ldl cholesterol", "vldl cholesterol", "triglycerides",
    "sgot", "ast", "sgpt", "alt", "alkaline phosphatase", "alp", "total bilirubin",
    "direct bilirubin", "indirect bilirubin", "total protein", "albumin", "globulin",
    "tsh", "t3", "t4", "free t3", "free t4", "vitamin d", "vitamin b12",
    "calcium", "potassium", "sodium", "chloride", "esr", "crp"
]

def evaluate_numeric_flag(result_val: float, ref_range_str: str) -> Optional[str]:
    """
    Safely compare a numeric result against a reference range string
    such as '13.0 - 17.0', '< 200', or '> 50'.
    """
    try:
        # Match range like "70 - 100" or "70-100" or "70 to 100"
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–—to]+\s*(\d+(?:\.\d+)?)", ref_range_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            if result_val < low:
                return "Low"
            elif result_val > high:
                return "High"
            else:
                return "Normal"

        # Match inequality like "< 200" or "<= 100"
        upper_match = re.search(r"[<≤]\s*(\d+(?:\.\d+)?)", ref_range_str)
        if upper_match:
            limit = float(upper_match.group(1))
            return "High" if result_val > limit else "Normal"

        # Match inequality like "> 50"
        lower_match = re.search(r"[>≥]\s*(\d+(?:\.\d+)?)", ref_range_str)
        if lower_match:
            limit = float(lower_match.group(1))
            return "Low" if result_val < limit else "Normal"
    except Exception:
        pass
    return None

def parse_line_for_parameter(line: str) -> Optional[ExtractedParameter]:
    """
    Heuristic extraction of a single lab parameter line:
    e.g. 'Hemoglobin 14.5 g/dL 13.0 - 17.0'
    or 'Serum Creatinine: 1.1 mg/dL (Ref: 0.7 - 1.3)'
    """
    cleaned = line.strip()
    if not cleaned or len(cleaned) < 5:
        return None

    # Skip common document headers and patient demographic metadata
    lower_line = cleaned.lower()
    skip_headers = [
        "patient", "pt name", "name:", "date of birth", "dob", "phone", "mobile",
        "cell", "tel", "email", "address", "residence", "mrn", "uhid", "sample",
        "specimen", "collected", "reported", "received", "doctor", "physician",
        "referred by", "hospital", "clinic", "laboratory", "page ", "age:", "gender:", "sex:"
    ]
    if any(header in lower_line for header in skip_headers):
        return None

    # Check for unit presence
    unit_match = re.search(r"\b(" + UNITS_REGEX + r")\b", cleaned, re.IGNORECASE)

    # Match test name followed by a numeric result (or known qualitative result)
    # Allows multi-word test names (e.g. "Platelet Count", "Serum Creatinine")
    pattern = re.compile(
        r"^([A-Za-z][A-Za-z0-9\s\(\)/\-_,\.]{1,40}?)"  # Test name
        r"[^\S\r\n]*[:\t]?[^\S\r\n]+"
        r"(\d+(?:\.\d+)?|Positive|Negative|Reactive|Non-Reactive|Detected|Not Detected)"  # Result value
        r"[^\S\r\n]*"
        rf"({UNITS_REGEX}|[^\s\d\(\)]+)?"             # Optional unit or unit-like token
        r"[^\S\r\n]*"
        r"(?:\((.*?)\)|(?:Ref|Normal|Range)?[:\s]*(\d+(?:\.\d+)?\s*[-–—to]+\s*\d+(?:\.\d+)?|[<≤>≥]\s*\d+(?:\.\d+)?))?",
        re.IGNORECASE
    )

    match = pattern.search(cleaned)
    if not match:
        return None

    name = match.group(1).strip()
    result = match.group(2).strip()
    raw_unit = match.group(3)
    unit = unit_match.group(1) if unit_match else (raw_unit.strip() if raw_unit and len(raw_unit) <= 10 else None)
    ref_range = match.group(4) or match.group(5)
    if ref_range:
        ref_range = ref_range.strip()

    # Filter out false positives (e.g. single character names or pure numbers)
    if len(name) < 2 or name.isdigit() or name.lower() in ["total", "date", "time", "status", "test", "result", "normal", "range", "flag"]:
        return None

    flag = None
    confidence = "medium"

    # Evaluate flag if result is numeric
    try:
        val_float = float(result)
        if ref_range:
            flag = evaluate_numeric_flag(val_float, ref_range)
    except ValueError:
        # Non-numeric result (e.g., 'Positive', 'Negative', 'Reactive')
        if result.lower() in ["positive", "reactive", "detected"]:
            flag = "Abnormal"
        elif result.lower() in ["negative", "non-reactive", "not detected"]:
            flag = "Normal"
        else:
            confidence = "requires_verification"

    # Check for explicit flags in line (e.g. 'HIGH', 'LOW', 'H', 'L')
    if not flag:
        if re.search(r"\b(HIGH|H)\b", cleaned):
            flag = "High"
        elif re.search(r"\b(LOW|L)\b", cleaned):
            flag = "Low"

    return ExtractedParameter(
        name=name,
        result=result,
        unit=unit,
        reference_range=ref_range,
        flag=flag,
        raw_line=cleaned,
        confidence=confidence
    )

def parse_table_rows(tables: List[List[List[Optional[str]]]]) -> List[ExtractedParameter]:
    """Parse structured tables extracted by pdfplumber."""
    parameters: List[ExtractedParameter] = []

    for table in tables:
        if not table or len(table) < 2:
            continue

        header_idx = -1
        col_map: Dict[str, int] = {}

        # Locate header row
        for row_i, row in enumerate(table):
            if not row:
                continue
            row_str = " ".join(str(cell or "").lower() for cell in row)
            if any(term in row_str for term in ["test", "investigation", "parameter", "analyte"]):
                header_idx = row_i
                for col_i, cell in enumerate(row):
                    if not cell:
                        continue
                    text = str(cell).lower().strip()
                    if any(k in text for k in ["test", "investigation", "parameter", "analyte"]):
                        col_map["name"] = col_i
                    elif any(k in text for k in ["result", "observed", "value"]):
                        col_map["result"] = col_i
                    elif any(k in text for k in ["unit"]):
                        col_map["unit"] = col_i
                    elif any(k in text for k in ["ref", "reference", "biological", "normal", "interval"]):
                        col_map["range"] = col_i
                    elif any(k in text for k in ["flag", "status"]):
                        col_map["flag"] = col_i
                break

        if "name" not in col_map or "result" not in col_map:
            continue

        for row in table[header_idx + 1:]:
            if not row:
                continue

            name_val = row[col_map["name"]] if col_map["name"] < len(row) else None
            result_val = row[col_map["result"]] if col_map["result"] < len(row) else None

            if not name_val or not result_val:
                continue

            name_str = str(name_val).strip()
            result_str = str(result_val).strip()

            if not name_str or len(name_str) < 2:
                continue

            unit_str = None
            if "unit" in col_map and col_map["unit"] < len(row) and row[col_map["unit"]]:
                unit_str = str(row[col_map["unit"]]).strip()

            range_str = None
            if "range" in col_map and col_map["range"] < len(row) and row[col_map["range"]]:
                range_str = str(row[col_map["range"]]).strip()

            flag_str = None
            if "flag" in col_map and col_map["flag"] < len(row) and row[col_map["flag"]]:
                flag_str = str(row[col_map["flag"]]).strip()

            # Automatic evaluation if flag is missing
            confidence = "high"
            if not flag_str and range_str:
                try:
                    num_val = float(re.sub(r"[^\d\.]", "", result_str))
                    flag_str = evaluate_numeric_flag(num_val, range_str)
                except ValueError:
                    pass

            raw_row_line = " | ".join(str(c or "").strip() for c in row if c)
            parameters.append(
                ExtractedParameter(
                    name=name_str,
                    result=result_str,
                    unit=unit_str,
                    reference_range=range_str,
                    flag=flag_str,
                    raw_line=raw_row_line,
                    confidence=confidence
                )
            )

    return parameters

def extract_from_digital_pdf(pdf_bytes: bytes) -> Tuple[str, List[ExtractedParameter], int]:
    """
    Extract text and structured tables from a digital PDF using pdfplumber,
    falling back to pypdf if needed.
    """
    total_pages = 0
    all_page_texts: List[str] = []
    all_tables: List[List[List[Optional[str]]]] = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            for idx, page in enumerate(pdf.pages):
                page_text = page.extract_text(layout=False) or ""
                page_header = f"--- Page {idx + 1} ---"
                all_page_texts.append(f"{page_header}\n{page_text}")

                extracted_tables = page.extract_tables()
                if extracted_tables:
                    all_tables.extend(extracted_tables)
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}. Falling back to pypdf.")
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_header = f"--- Page {idx + 1} ---"
            all_page_texts.append(f"{page_header}\n{page_text}")

    full_text = "\n\n".join(all_page_texts).strip()

    # Parse parameters: prioritize tables, then fallback to line matching
    parameters = parse_table_rows(all_tables)
    if not parameters:
        for line in full_text.splitlines():
            param = parse_line_for_parameter(line)
            if param:
                parameters.append(param)

    return full_text, parameters, total_pages

def process_report_file(file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> ExtractionResponse:
    """
    Main entry point for report extraction:
    - Identifies file format (.pdf, .jpg, .jpeg, .png)
    - Validates encryption & corruption
    - Chooses digital extraction vs OCR
    - Applies PII privacy masking
    - Organizes medical parameters
    """
    lower_name = filename.lower()
    warnings: List[str] = []

    # 1. Validation & File Type Detection
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    MAX_SIZE = 15 * 1024 * 1024  # 15MB
    if len(file_bytes) > MAX_SIZE:
        raise ValueError("File exceeds maximum allowable size of 15MB.")

    is_pdf = lower_name.endswith(".pdf") or (content_type and "pdf" in content_type.lower())
    is_image = any(lower_name.endswith(ext) for ext in [".jpg", ".jpeg", ".png"]) or (
        content_type and any(t in content_type.lower() for t in ["jpeg", "jpg", "png"])
    )

    if not is_pdf and not is_image:
        raise ValueError(f"Unsupported file format '{filename}'. Allowed formats: PDF, JPG, JPEG, PNG.")

    raw_text = ""
    parameters: List[ExtractedParameter] = []
    total_pages = 1
    method = ""

    # 2. Process PDF
    if is_pdf:
        # Check for PDF encryption
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            if reader.is_encrypted:
                raise ValueError("Password-protected or encrypted PDF cannot be processed.")
        except Exception as e:
            if "encrypted" in str(e).lower():
                raise
            raise ValueError(f"Corrupted or invalid PDF file: {str(e)}")

        # Attempt digital extraction
        text, params, pages = extract_from_digital_pdf(file_bytes)
        total_pages = pages

        # Check if text is sufficient or if it's a scanned PDF
        # Low text threshold: average < 40 characters per page or total < 50 chars
        clean_text_len = len(re.sub(r"[\s\-\–—Page\d]+", "", text))
        if clean_text_len < 40:
            logger.info("PDF has insufficient digital text. Routing to scanned PDF OCR pipeline.")
            ocr_text, ocr_pages = ocr_scanned_pdf(file_bytes)
            raw_text = ocr_text
            total_pages = ocr_pages
            method = "scanned_pdf_ocr"
            warnings.append("Document appears to be a scanned copy. Text was extracted using optical character recognition (OCR).")

            # Parse parameters from OCR text lines
            for line in raw_text.splitlines():
                p = parse_line_for_parameter(line)
                if p:
                    parameters.append(p)
        else:
            raw_text = text
            parameters = params
            method = "digital_pdf"

    # 3. Process Image
    elif is_image:
        method = "image_ocr"
        total_pages = 1
        raw_text = ocr_image_bytes(file_bytes)
        for line in raw_text.splitlines():
            p = parse_line_for_parameter(line)
            if p:
                parameters.append(p)

    if not raw_text.strip():
        warnings.append("No readable text could be extracted from the document. Please ensure the image or scan is clear and legible.")

    # 4. Privacy & PII Masking
    sanitized_text, privacy_status = mask_pii(raw_text)

    # Also sanitize raw_line in parameters so no patient name is retained in structured objects
    sanitized_parameters: List[ExtractedParameter] = []
    for param in parameters:
        masked_line, _ = mask_pii(param.raw_line or "")
        sanitized_param = param.model_copy(update={"raw_line": masked_line})
        sanitized_parameters.append(sanitized_param)

    file_type = "pdf" if is_pdf else lower_name.split(".")[-1]

    return ExtractionResponse(
        filename=filename,
        file_type=file_type,
        extraction_method=method,
        total_pages=total_pages,
        extracted_text=sanitized_text,
        extracted_parameters=sanitized_parameters,
        privacy_masking_status=privacy_status,
        warnings=warnings
    )
