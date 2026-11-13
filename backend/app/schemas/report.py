from typing import List, Optional
from pydantic import BaseModel, Field

class ExtractedParameter(BaseModel):
    name: str = Field(..., description="Laboratory test name")
    result: Optional[str] = Field(None, description="Measured result value")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g., g/dL, mg/dL)")
    reference_range: Optional[str] = Field(None, description="Normal reference interval (e.g., 70-100, <200)")
    flag: Optional[str] = Field(None, description="Evaluation flag: Normal, High, Low, Abnormal, or Needs Verification")
    raw_line: Optional[str] = Field(None, description="Original unparsed text line")
    confidence: str = Field("medium", description="Extraction confidence: high, medium, requires_verification")

class PrivacyMaskingStatus(BaseModel):
    masked_names_count: int = 0
    masked_identifiers_count: int = 0
    masked_contact_count: int = 0
    is_sanitized: bool = True
    notice: str = (
        "Heuristic pattern-based privacy masking applied. "
        "This enhances privacy but does not guarantee 100% anonymization."
    )

class ExtractionResponse(BaseModel):
    filename: str
    file_type: str
    extraction_method: str = Field(..., description="digital_pdf, scanned_pdf_ocr, or image_ocr")
    total_pages: int
    extracted_text: str
    extracted_parameters: List[ExtractedParameter] = []
    privacy_masking_status: PrivacyMaskingStatus
    warnings: List[str] = []

# Phase 3: AI Explanation Schemas
class ParameterExplanation(BaseModel):
    name: str
    observed_value: Optional[str] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    status: str = Field("Normal", description="Normal, High, Low, Abnormal, or Inconclusive")
    plain_english_explanation: str = Field(..., description="What this test measures in simple words")
    interpretation: str = Field(..., description="What the observed result generally indicates in lay terms")

class TerminologyItem(BaseModel):
    term: str
    simple_definition: str

class ReportAnalysisResponse(BaseModel):
    extraction: ExtractionResponse
    summary: str = Field(..., description="High-level patient-friendly summary of the overall lab report")
    key_findings: List[str] = Field(default_factory=list, description="Top takeaways and abnormal observations")
    parameters_explained: List[ParameterExplanation] = Field(default_factory=list)
    terminology_breakdown: List[TerminologyItem] = Field(default_factory=list)
    questions_for_doctor: List[str] = Field(default_factory=list, description="Curated questions for patient's doctor")
    educational_notes: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "This explanation is generated purely for educational and health literacy purposes. "
        "It is NOT a medical diagnosis, clinical opinion, or treatment advice. "
        "Laboratory values must always be interpreted by a qualified healthcare professional in the context of your complete medical history."
    )
    is_mock: bool = False
