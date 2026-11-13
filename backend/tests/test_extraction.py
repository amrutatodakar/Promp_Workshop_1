import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.main import app
from app.utils.privacy import mask_pii

client = TestClient(app)

# Helper: Generate synthetic digital PDF using ReportLab
def create_synthetic_digital_pdf() -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Patient info (synthetic mock data)
    story.append(Paragraph("<b>LABORATORY INVESTIGATION REPORT</b>", styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Patient Name: Jane Doe", styles["Normal"]))
    story.append(Paragraph("DOB: 14/06/1988", styles["Normal"]))
    story.append(Paragraph("Phone: +1-555-839-2019", styles["Normal"]))
    story.append(Paragraph("Patient ID: PID-992384", styles["Normal"]))
    story.append(Spacer(1, 15))

    # Structured medical parameter table
    data = [
        ["Test Name", "Result", "Unit", "Biological Reference Interval"],
        ["Hemoglobin", "14.5", "g/dL", "13.0 - 17.0"],
        ["Fasting Blood Glucose", "118", "mg/dL", "70 - 100"],
        ["Serum Creatinine", "0.9", "mg/dL", "0.7 - 1.3"],
        ["Total Cholesterol", "225", "mg/dL", "< 200"],
    ]

    table = Table(data, colWidths=[180, 80, 80, 160])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)

    doc.build(story)
    return buffer.getvalue()

# Helper: Generate synthetic scanned PDF (Image wrapped in PDF)
def create_synthetic_scanned_pdf() -> bytes:
    img = Image.new("RGB", (800, 250), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), "SCANNED REPORT - METABOLIC PANEL", fill="black")
    draw.text((30, 70), "Patient Name: Robert Smith", fill="black")
    draw.text((30, 110), "Uric Acid: 5.2 mg/dL (Range: 3.5 - 7.2)", fill="black")
    draw.text((30, 150), "Calcium: 9.4 mg/dL (Range: 8.5 - 10.5)", fill="black")

    buffer = io.BytesIO()
    img.save(buffer, format="PDF")
    return buffer.getvalue()

# Helper: Generate synthetic JPG / PNG image
def create_synthetic_image(fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (750, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 20), "Patient Name: Emily Clark", fill="black")
    draw.text((20, 60), "Phone: 555-827-1928", fill="black")
    draw.text((20, 100), "Platelet Count: 250 10^3/uL (Normal: 150 - 450)", fill="black")
    draw.text((20, 140), "WBC: 12.5 10^3/uL (Normal: 4.0 - 11.0)", fill="black")

    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    return buffer.getvalue()

# 1. Test Health Endpoint
def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["api"] == "up"
    assert data["services"]["tesseract_ocr"] == "available"

# 2. Test Privacy Masking Logic
def test_privacy_masking_comprehensive():
    sample = (
        "Patient Name: Johnathan Doe\n"
        "DOB: 12/05/1982\n"
        "Phone: +1-555-234-5678\n"
        "Patient ID: PT-982341\n"
        "Email: patient.test@example.com\n"
        "Address: 742 Evergreen Terrace\n"
        "Test: Hemoglobin 14.5 g/dL"
    )
    sanitized, status = mask_pii(sample)

    assert "Johnathan Doe" not in sanitized
    assert "[PATIENT NAME REDACTED]" in sanitized
    assert "12/05/1982" not in sanitized
    assert "[DOB REDACTED]" in sanitized
    assert "555-234-5678" not in sanitized
    assert "[PHONE REDACTED]" in sanitized
    assert "PT-982341" not in sanitized
    assert "[ID REDACTED]" in sanitized
    assert "patient.test@example.com" not in sanitized
    assert "[EMAIL REDACTED]" in sanitized
    assert "742 Evergreen Terrace" not in sanitized
    assert "[ADDRESS REDACTED]" in sanitized
    assert "Hemoglobin 14.5 g/dL" in sanitized
    assert status.masked_names_count >= 1
    assert status.masked_identifiers_count >= 2
    assert status.masked_contact_count >= 2

# 3. Test Digital PDF Extraction
def test_digital_pdf_extraction():
    pdf_bytes = create_synthetic_digital_pdf()
    files = {"file": ("synthetic_report.pdf", pdf_bytes, "application/pdf")}

    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["filename"] == "synthetic_report.pdf"
    assert data["file_type"] == "pdf"
    assert data["extraction_method"] == "digital_pdf"
    assert data["total_pages"] >= 1

    # Check PII redaction
    assert "Jane Doe" not in data["extracted_text"]
    assert "[PATIENT NAME REDACTED]" in data["extracted_text"]

    # Check extracted parameters
    params = {p["name"]: p for p in data["extracted_parameters"]}
    assert "Hemoglobin" in params
    assert params["Hemoglobin"]["result"] == "14.5"
    assert params["Hemoglobin"]["unit"] == "g/dL"
    assert params["Hemoglobin"]["flag"] == "Normal"

    assert "Fasting Blood Glucose" in params
    assert params["Fasting Blood Glucose"]["result"] == "118"
    assert params["Fasting Blood Glucose"]["flag"] == "High"

    assert "Total Cholesterol" in params
    assert params["Total Cholesterol"]["flag"] == "High"

# 4. Test Scanned PDF OCR Fallback
def test_scanned_pdf_ocr():
    scanned_bytes = create_synthetic_scanned_pdf()
    files = {"file": ("scanned_lab.pdf", scanned_bytes, "application/pdf")}

    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["extraction_method"] == "scanned_pdf_ocr"
    assert "Robert Smith" not in data["extracted_text"]
    assert len(data["warnings"]) > 0
    assert any("scanned" in w.lower() for w in data["warnings"])

# 5. Test PNG Image OCR
def test_image_ocr_png():
    img_bytes = create_synthetic_image("PNG")
    files = {"file": ("report_scan.png", img_bytes, "image/png")}

    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["extraction_method"] == "image_ocr"
    assert data["file_type"] == "png"
    assert "Emily Clark" not in data["extracted_text"]
    assert len(data["extracted_text"]) > 20

# 6. Test JPEG Image OCR
def test_image_ocr_jpeg():
    img_bytes = create_synthetic_image("JPEG")
    files = {"file": ("report_scan.jpg", img_bytes, "image/jpeg")}

    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["extraction_method"] == "image_ocr"
    assert data["file_type"] == "jpg"
    assert len(data["extracted_text"]) > 20

# 7. Test Unsupported File Format
def test_unsupported_file_format():
    files = {"file": ("notes.txt", b"Unsupported plain text file", "text/plain")}
    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()

# 8. Test Empty File Upload
def test_empty_file_upload():
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

# 9. Test Corrupted PDF File
def test_corrupted_pdf_upload():
    files = {"file": ("corrupted.pdf", b"NOT_A_VALID_PDF_HEADER_DATA_12345", "application/pdf")}
    response = client.post("/api/reports/extract", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()

# 10. Test Full End-to-End Analyze Pipeline (Extract + Redact + Explain)
def test_full_analyze_pipeline():
    pdf_bytes = create_synthetic_digital_pdf()
    files = {"file": ("report_to_analyze.pdf", pdf_bytes, "application/pdf")}

    response = client.post("/api/reports/analyze", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "extraction" in data
    assert data["extraction"]["extraction_method"] == "digital_pdf"
    assert "summary" in data and len(data["summary"]) > 20
    assert len(data["parameters_explained"]) >= 3
    assert len(data["questions_for_doctor"]) >= 2
    assert "disclaimer" in data
    assert "Jane Doe" not in data["extraction"]["extracted_text"]

