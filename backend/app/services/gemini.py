"""
Gemini AI Explanation Service for ReportSaathi.

Translates complex laboratory findings into simple, educational, and patient-friendly language.
Strictly adheres to medical safety rules:
- No medical diagnoses
- No drug/medication prescriptions
- Transparent reference intervals and original values
- Curated questions for the patient's doctor
- Fallback educational generator when GEMINI_API_KEY is not yet configured
"""

import json
import logging
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.report import (
    ExtractionResponse,
    ExtractedParameter,
    ReportAnalysisResponse,
    ParameterExplanation,
    TerminologyItem
)

logger = logging.getLogger("reportsaathi.gemini")

# Educational Knowledge Base for Local Fallback / Mock Mode
PARAMETER_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "hemoglobin": {
        "what": "A protein inside red blood cells that carries oxygen from your lungs to the rest of your body.",
        "normal": "Your oxygen-carrying capacity appears within the standard healthy range.",
        "high": "Higher levels can occur with dehydration, smoking, or living at high altitudes.",
        "low": "Lower levels may indicate anemia, which can cause fatigue or weakness."
    },
    "fasting blood glucose": {
        "what": "Measures the amount of sugar (glucose) circulating in your blood after fasting.",
        "normal": "Blood sugar levels are within the normal expected range after fasting.",
        "high": "Higher than normal levels may reflect elevated blood sugar or impaired glucose processing.",
        "low": "Lower than expected blood sugar, which may cause lightheadedness or sweating."
    },
    "serum creatinine": {
        "what": "A natural waste product produced by muscle metabolism that is filtered out by your kidneys.",
        "normal": "Creatinine levels are typical, indicating normal kidney filtration.",
        "high": "Elevated levels can suggest the kidneys may be filtering waste less efficiently.",
        "low": "Low levels are relatively uncommon and often related to low muscle mass."
    },
    "total cholesterol": {
        "what": "A measure of all the cholesterol types in your bloodstream, used to evaluate cardiovascular health.",
        "normal": "Overall blood cholesterol is within the standard desirable limit.",
        "high": "Higher cholesterol levels can contribute over time to plaque accumulation in blood vessels.",
        "low": "Levels are below typical thresholds."
    },
    "platelet count": {
        "what": "Tiny cell fragments that help your blood clot to stop bleeding from cuts or injuries.",
        "normal": "Platelet counts are within the expected clotting safety window.",
        "high": "Elevated platelets can occur in response to inflammation or infection.",
        "low": "Fewer platelets can increase the tendency to bruise or bleed easily."
    },
    "wbc": {
        "what": "White blood cells are the primary immune cells that fight infections and foreign invaders.",
        "normal": "White blood cell count is within the healthy baseline immune range.",
        "high": "Often rises temporarily when the body is fighting an active infection or inflammation.",
        "low": "May indicate temporary immune system suppression or viral recovery."
    }
}

SYSTEM_INSTRUCTION = """
You are ReportSaathi, an empathetic and highly knowledgeable medical laboratory educator.
Your mission is to explain medical laboratory results in clear, calm, and simple English for patients and family caregivers.

CRITICAL MEDICAL SAFETY RULES:
1. NEVER provide a definitive medical diagnosis (e.g., do NOT say "You have diabetes" or "You have kidney failure"). Instead, explain what the test measures and what elevated/low results may reflect in general terms (e.g., "Fasting glucose is slightly above standard limits, which doctors often evaluate for insulin sensitivity").
2. NEVER prescribe, recommend, or adjust medications, doses, or medical treatments.
3. ALWAYS display the original laboratory value, unit, and reference interval.
4. Explain all medical terminology in simple, everyday analogies.
5. Create 3 to 5 clear, proactive questions the patient can ask their physician during their next visit.
6. Emphasize that only a licensed medical doctor who knows the patient's full medical history can interpret these results in context.

Output ONLY a valid JSON object matching the requested schema.
"""

def generate_local_educational_analysis(extraction: ExtractionResponse) -> ReportAnalysisResponse:
    """
    Intelligent rule-based educational explainer.
    Used when GEMINI_API_KEY is pending, ensuring zero downtime and instant testability.
    """
    explained_params: List[ParameterExplanation] = []
    key_findings: List[str] = []
    terms: List[TerminologyItem] = []
    questions: List[str] = [
        "What do these specific test results mean in the context of my current symptoms and health history?",
        "Are there any follow-up tests or repeat panels you recommend to confirm these findings?",
        "Are there any dietary, hydration, or lifestyle modifications that could help support my health?"
    ]

    for param in extraction.extracted_parameters:
        name_lower = param.name.lower()
        kb_entry = None
        for key, val in PARAMETER_KNOWLEDGE_BASE.items():
            if key in name_lower:
                kb_entry = val
                break

        what = kb_entry["what"] if kb_entry else f"A clinical blood test parameter evaluating {param.name}."
        
        status = param.flag or "Normal"
        if status == "High":
            interp = kb_entry["high"] if kb_entry else f"{param.name} is measured above the reference interval."
            key_findings.append(f"Elevated {param.name}: Observed {param.result} {param.unit or ''} (Ref: {param.reference_range or 'N/A'}).")
            questions.append(f"My {param.name} was flagged above normal at {param.result} {param.unit or ''}. Could this be temporary or require attention?")
        elif status == "Low":
            interp = kb_entry["low"] if kb_entry else f"{param.name} is measured below the reference interval."
            key_findings.append(f"Low {param.name}: Observed {param.result} {param.unit or ''} (Ref: {param.reference_range or 'N/A'}).")
            questions.append(f"My {param.name} was below the standard range. What could be contributing to this?")
        else:
            interp = kb_entry["normal"] if kb_entry else f"Result appears within standard reference expectations."

        explained_params.append(
            ParameterExplanation(
                name=param.name,
                observed_value=param.result,
                unit=param.unit,
                normal_range=param.reference_range,
                status=status,
                plain_english_explanation=what,
                interpretation=interp
            )
        )

        terms.append(
            TerminologyItem(
                term=param.name,
                simple_definition=what
            )
        )

    # General summary
    if key_findings:
        summary = (
            f"Your report contains {len(extraction.extracted_parameters)} extracted laboratory tests. "
            f"Most values are documented, with {len(key_findings)} parameter(s) showing results outside standard reference intervals. "
            f"These findings provide valuable data points for your doctor to review alongside your complete physical health."
        )
    else:
        summary = (
            f"Your report contains {len(extraction.extracted_parameters)} laboratory parameters. "
            f"The tested values generally appear consistent with standard reference expectations. "
            f"Review this summary with your doctor to interpret how these numbers fit into your overall well-being."
        )

    educational_notes = [
        "Reference ranges can vary slightly between different laboratories based on equipment and calibration.",
        "A result slightly outside the reference range does not necessarily mean something is wrong; hydration, recent meals, and time of day can influence numbers.",
        "ReportSaathi is currently running in Educational Demo Mode. To enable live Gemini 2.5 Flash explanations, add your GEMINI_API_KEY to backend/.env."
    ]

    return ReportAnalysisResponse(
        extraction=extraction,
        summary=summary,
        key_findings=key_findings,
        parameters_explained=explained_params,
        terminology_breakdown=terms[:6],
        questions_for_doctor=questions[:5],
        educational_notes=educational_notes,
        is_mock=True
    )

def explain_report_with_gemini(extraction: ExtractionResponse) -> ReportAnalysisResponse:
    """
    Generate an AI-powered patient explanation using Google Gemini API.
    If GEMINI_API_KEY is not configured or an API error occurs, falls back cleanly.
    """
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Using rule-based educational generator.")
        return generate_local_educational_analysis(extraction)

    try:
        client = genai.Client(api_key=api_key)
        
        # Build prompt incorporating extracted parameters and sanitized text
        extracted_info = {
            "total_pages": extraction.total_pages,
            "extraction_method": extraction.extraction_method,
            "extracted_parameters": [p.model_dump() for p in extraction.extracted_parameters],
            "sanitized_document_text": extraction.extracted_text[:4000]
        }

        user_prompt = f"""
Please analyze this sanitized medical laboratory report and explain it in clear, compassionate, and educational plain English.

REPORT DATA:
{json.dumps(extracted_info, indent=2)}

Please return a JSON object with this exact structure:
{{
  "summary": "2-3 sentences explaining the overall report in plain English",
  "key_findings": ["Bullet points of key findings or out-of-range parameters"],
  "parameters_explained": [
    {{
      "name": "Test name",
      "observed_value": "Value",
      "unit": "Unit",
      "normal_range": "Reference range",
      "status": "Normal | High | Low | Abnormal",
      "plain_english_explanation": "What this test measures in everyday terms",
      "interpretation": "What the result indicates in non-alarmist plain language"
    }}
  ],
  "terminology_breakdown": [
    {{
      "term": "Medical term or abbreviation",
      "simple_definition": "Plain English definition"
    }}
  ],
  "questions_for_doctor": [
    "Thoughtful, specific questions the patient can ask their doctor"
  ],
  "educational_notes": [
    "Educational context regarding reference intervals, fasting, or testing variations"
  ]
}}
"""

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2
            )
        )

        response_text = response.text or "{}"
        parsed = json.loads(response_text)

        parameters_explained = [
            ParameterExplanation(**p) for p in parsed.get("parameters_explained", [])
        ]
        terminology = [
            TerminologyItem(**t) for t in parsed.get("terminology_breakdown", [])
        ]

        return ReportAnalysisResponse(
            extraction=extraction,
            summary=parsed.get("summary", "Laboratory report explanation."),
            key_findings=parsed.get("key_findings", []),
            parameters_explained=parameters_explained,
            terminology_breakdown=terminology,
            questions_for_doctor=parsed.get("questions_for_doctor", []),
            educational_notes=parsed.get("educational_notes", []),
            is_mock=False
        )

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}. Falling back to local educational analysis.", exc_info=True)
        fallback = generate_local_educational_analysis(extraction)
        fallback.educational_notes.append(f"Note: Gemini AI explanation service encountered an error ({str(e)}). Displaying local educational synthesis.")
        return fallback
