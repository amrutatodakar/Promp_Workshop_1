"""
Privacy and PII (Personally Identifiable Information) Sanitizer.

Applies pattern-based heuristics to mask sensitive patient identifiers
(names, contact details, dates of birth, MRN/UHID) before any further processing.

IMPORTANT LEGAL & COMPLIANCE DISCLAIMER:
Pattern-based regex masking is a heuristic enhancement and does not guarantee
100% anonymization (e.g., unusual name formats or handwritten notes might be missed).
"""

import re
from typing import Tuple
from app.schemas.report import PrivacyMaskingStatus

# Regex Patterns for Medical Lab Report PII (Strictly bounded to single lines)

# 1. Patient Name indicators (horizontal whitespace only: [^\S\r\n])
PATIENT_NAME_LABEL_PATTERN = re.compile(
    r"(?i)\b(?:patient(?:\s*name)?|pt(?:\s*name)?|name\s*of\s*patient)\s*[:\-]\s*(?:mr\.|mrs\.|ms\.|dr\.|master\.)?[^\S\r\n]*([A-Za-z]{2,}(?:[^\S\r\n]+[A-Za-z]{1,}){1,3})",
)
TITLE_NAME_PATTERN = re.compile(
    r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Master\.)[^\S\r\n]+([A-Z][a-z]+(?:[^\S\r\n]+[A-Z][a-z]+){1,2})\b"
)

# 2. Contact details: Email & Phone numbers
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
PHONE_LABEL_PATTERN = re.compile(
    r"(?i)\b(?:phone|mobile|cell|contact(?:\s*no)?|tel(?:\s*no)?)\s*[:\-][^\S\r\n]*(\+?[\d \-\(\)]{7,20})"
)
GENERIC_PHONE_PATTERN = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b[6-9]\d{9}\b"
)

# 3. Date of Birth
DOB_LABEL_PATTERN = re.compile(
    r"(?i)\b(?:dob|d\.o\.b\.|date\s+of\s+birth|birth\s*date)\s*[:\-][^\S\r\n]*([0-9]{1,4}[/\-\.][0-9]{1,2}[/\-\.][0-9]{1,4}|[A-Za-z]+[^\S\r\n]+\d{1,2},?[^\S\r\n]+\d{4})"
)

# 4. Medical Record Numbers, UHID, Patient ID, Registration IDs
PATIENT_ID_PATTERN = re.compile(
    r"(?i)\b(?:patient\s*(?:id|no)|mrn|uhid|ref(?:\s*no)?|reg(?:\s*no|\s*id)?|ipd\s*no|opd\s*no|lab\s*id|barcode)\s*[:\-][^\S\r\n]*([A-Za-z0-9\-_/]{4,25})"
)

# 5. Address lines
ADDRESS_PATTERN = re.compile(
    r"(?i)\b(?:address|residence)\s*[:\-][^\S\r\n]*([^\r\n]{4,})"
)

def mask_pii(text: str) -> Tuple[str, PrivacyMaskingStatus]:
    """
    Scrub identifiable patient information from extracted text.
    Returns the sanitized string and a PrivacyMaskingStatus summary.
    """
    if not text:
        return "", PrivacyMaskingStatus(is_sanitized=True)

    sanitized = text
    name_count = 0
    id_count = 0
    contact_count = 0

    # 1. Mask Patient Names with labels
    def replace_labeled_name(match):
        nonlocal name_count
        name_count += 1
        full_match = match.group(0)
        target = match.group(1)
        return full_match.replace(target, "[PATIENT NAME REDACTED]")

    sanitized = PATIENT_NAME_LABEL_PATTERN.sub(replace_labeled_name, sanitized)

    # Mask title-based names (e.g., Mr. John Doe)
    def replace_titled_name(match):
        nonlocal name_count
        name_count += 1
        return "[PATIENT NAME REDACTED]"

    sanitized = TITLE_NAME_PATTERN.sub(replace_titled_name, sanitized)

    # 2. Mask Emails
    def replace_email(match):
        nonlocal contact_count
        contact_count += 1
        return "[EMAIL REDACTED]"

    sanitized = EMAIL_PATTERN.sub(replace_email, sanitized)

    # 3. Mask Labeled Phones
    def replace_labeled_phone(match):
        nonlocal contact_count
        contact_count += 1
        full_match = match.group(0)
        target = match.group(1)
        return full_match.replace(target, "[PHONE REDACTED]")

    sanitized = PHONE_LABEL_PATTERN.sub(replace_labeled_phone, sanitized)

    # Mask standalone phone numbers
    def replace_phone(match):
        nonlocal contact_count
        contact_count += 1
        return "[PHONE REDACTED]"

    sanitized = GENERIC_PHONE_PATTERN.sub(replace_phone, sanitized)

    # 4. Mask Date of Birth
    def replace_dob(match):
        nonlocal id_count
        id_count += 1
        full_match = match.group(0)
        target = match.group(1)
        return full_match.replace(target, "[DOB REDACTED]")

    sanitized = DOB_LABEL_PATTERN.sub(replace_dob, sanitized)

    # 5. Mask Patient IDs / MRN
    def replace_id(match):
        nonlocal id_count
        id_count += 1
        full_match = match.group(0)
        target = match.group(1)
        return full_match.replace(target, "[ID REDACTED]")

    sanitized = PATIENT_ID_PATTERN.sub(replace_id, sanitized)

    # 6. Mask Address
    def replace_address(match):
        nonlocal id_count
        id_count += 1
        full_match = match.group(0)
        target = match.group(1)
        return full_match.replace(target, "[ADDRESS REDACTED]")

    sanitized = ADDRESS_PATTERN.sub(replace_address, sanitized)

    status = PrivacyMaskingStatus(
        masked_names_count=name_count,
        masked_identifiers_count=id_count,
        masked_contact_count=contact_count,
        is_sanitized=True,
    )

    return sanitized, status
