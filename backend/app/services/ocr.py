"""
OCR Service for Image and Scanned PDF Text Extraction.

Uses Pillow for image preprocessing (grayscale, contrast, sharpness)
and Tesseract OCR for text recognition with tabular structure preservation.
"""

import os
import shutil
import io
import logging
from pathlib import Path
from typing import Tuple, List
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pypdfium2 as pdfium

logger = logging.getLogger("reportsaathi.ocr")

# Configure local tessdata prefix if available
LOCAL_TESSDATA = Path(__file__).resolve().parent.parent.parent / "tessdata"
if LOCAL_TESSDATA.exists() and (LOCAL_TESSDATA / "eng.traineddata").exists():
    os.environ["TESSDATA_PREFIX"] = str(LOCAL_TESSDATA)

# Configure tesseract executable path on Windows if needed
TESSERACT_EXE = shutil.which("tesseract")
if TESSERACT_EXE:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
else:
    # Common default location on Windows
    default_win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if shutil.which(default_win_path):
        pytesseract.pytesseract.tesseract_cmd = default_win_path

def is_ocr_available() -> bool:
    """Check if Tesseract binary is callable."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Enhance document image for optical character recognition:
    1. Convert to RGB if RGBA/palette, then to Grayscale ('L').
    2. Upscale low-resolution images to improve OCR on small font lab text.
    3. Increase contrast and sharpness to make faded printouts legible.
    """
    # Convert mode to RGB then L
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    gray = image.convert("L")

    # Upscale if dimensions are low (e.g., width < 1200)
    w, h = gray.size
    if w < 1200:
        scale = 1200 / float(w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        gray = gray.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.8)

    # Enhance sharpness
    sharpener = ImageEnhance.Sharpness(enhanced)
    sharpened = sharpener.enhance(1.4)

    return sharpened

def ocr_image(image: Image.Image, preprocess: bool = True) -> str:
    """
    Extract text from a PIL Image using Tesseract OCR.
    Uses PSM 6 (uniform block of text) and falls back to PSM 3 (fully automatic).
    """
    if not is_ocr_available():
        raise RuntimeError("Tesseract OCR is not installed or not found on the system PATH.")

    img_to_process = preprocess_image(image) if preprocess else image

    # First attempt with PSM 6 (good for structured lab reports/tables)
    config = "--oem 3 --psm 6"
    try:
        text = pytesseract.image_to_string(img_to_process, config=config)
    except Exception as e:
        logger.warning(f"OCR with PSM 6 failed: {e}. Retrying with PSM 3.")
        text = pytesseract.image_to_string(img_to_process, config="--oem 3 --psm 3")

    # If result was sparse, try PSM 3 fallback
    if len(text.strip()) < 20:
        fallback_text = pytesseract.image_to_string(img_to_process, config="--oem 3 --psm 3")
        if len(fallback_text.strip()) > len(text.strip()):
            text = fallback_text

    return text.strip()

def ocr_image_bytes(image_bytes: bytes) -> str:
    """Read image bytes and return extracted text."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return ocr_image(image)
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")

def ocr_scanned_pdf(pdf_bytes: bytes) -> Tuple[str, int]:
    """
    Convert each page of a scanned PDF into a high-resolution image
    and run OCR page-by-page.
    Returns (combined_text, total_pages).
    """
    if not is_ocr_available():
        raise RuntimeError("Tesseract OCR is not installed or not found on the system PATH.")

    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
    except Exception as e:
        raise ValueError(f"Could not parse PDF for OCR: {str(e)}")

    total_pages = len(pdf)
    if total_pages == 0:
        return "", 0

    page_texts: List[str] = []

    for page_idx in range(total_pages):
        page = pdf.get_page(page_idx)
        # Render at 2.5x scale (~180-200 DPI equivalent) for sharp text
        pil_image = page.render(scale=2.5).to_pil()
        page.close()

        extracted = ocr_image(pil_image, preprocess=True)
        page_header = f"--- Page {page_idx + 1} ---"
        page_texts.append(f"{page_header}\n{extracted}")

    pdf.close()
    combined = "\n\n".join(page_texts).strip()
    return combined, total_pages
