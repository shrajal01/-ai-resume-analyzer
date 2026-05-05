"""
Resume Service — the core business logic layer.

Responsibilities:
  1. Validate the uploaded file (size, content type)
  2. Delegate text extraction to the PDF utility
  3. Return structured mock analysis (Demo Mode — no API key needed)
  4. Return a typed ResumeAnalysisResult

NOTE FOR CLIENT:
  To enable real AI analysis, uncomment the Gemini OR OpenAI section below
  and provide the respective API key in the .env file.
"""

import logging
import asyncio

from app.core.config import get_settings
from app.models.schemas import ResumeAnalysisResult
from app.utils.pdf_parser import extract_text_from_pdf, PDFParsingError

logger = logging.getLogger(__name__)
settings = get_settings()


# ══════════════════════════════════════════════════════════════════
# OPTION 1 — GEMINI (uncomment when client provides Gemini API key)
# ══════════════════════════════════════════════════════════════════
# import json
# from google import genai
# from google.genai import types
# _gemini_client = genai.Client(api_key=settings.gemini_api_key)


# ══════════════════════════════════════════════════════════════════
# OPTION 2 — OPENAI (uncomment when client provides OpenAI API key)
# ══════════════════════════════════════════════════════════════════
# import json
# from openai import AsyncOpenAI
# _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


# ── Custom Exceptions ─────────────────────────────────────────────

class FileTooLargeError(Exception):
    pass

class InvalidFileTypeError(Exception):
    pass

class ResumeTextExtractionError(Exception):
    pass

class LLMAnalysisError(Exception):
    pass


# ── System Prompt (for when real LLM is enabled) ─────────────────

_SYSTEM_PROMPT = """
You are an expert technical recruiter and career coach with 15+ years of experience
evaluating resumes for top-tier technology companies.

Analyze the provided resume text and return a JSON object with EXACTLY this structure:

{
  "key_skills": ["skill1", "skill2", ...],
  "strengths": ["strength1", "strength2", ...],
  "weaknesses": ["weakness1", "weakness2", ...],
  "suggestions": ["suggestion1", "suggestion2", ...],
  "score": <integer 0-100>,
  "summary": "<one concise paragraph>"
}

Rules:
- key_skills: List 5-15 concrete skills (languages, tools, frameworks, soft skills).
- strengths: List 3-6 genuine positives backed by resume evidence.
- weaknesses: List 2-5 honest, constructive gaps.
- suggestions: List 3-6 specific, actionable improvements (not vague advice).
- score: Integer from 0-100. Be calibrated: 50 = average, 75 = strong, 90+ = exceptional.
- summary: 2-3 sentences. Professional tone. Third person.

Return ONLY valid JSON. No markdown, no explanation, no preamble.
""".strip()


# ── Mock Analysis (Demo Mode) ─────────────────────────────────────

def _generate_mock_analysis(resume_text: str) -> ResumeAnalysisResult:
    """
    Returns a realistic mock analysis — no API key needed.
    Score adjusts based on resume length for demo realism.
    """
    word_count = len(resume_text.split())

    if word_count > 500:
        score = 82
    elif word_count > 300:
        score = 74
    else:
        score = 61

    return ResumeAnalysisResult(
        key_skills=[
            "Python", "FastAPI", "REST API Design",
            "PostgreSQL", "Docker", "Git",
            "Problem Solving", "Communication"
        ],
        strengths=[
            "Well-structured resume with clear section headings",
            "Demonstrates hands-on project experience",
            "Shows progression and growth in technical skills",
            "Good balance of technical and soft skills mentioned"
        ],
        weaknesses=[
            "Quantified achievements are missing (add numbers and impact)",
            "No links to GitHub, portfolio, or LinkedIn",
            "Summary section could be more compelling"
        ],
        suggestions=[
            "Add measurable impact to each bullet (e.g. 'reduced load time by 40%')",
            "Include a GitHub profile link to showcase your actual code",
            "Write a 2-3 line professional summary at the top",
            "Add relevant certifications if any (AWS, Google Cloud, etc.)",
            "Tailor resume keywords to match job descriptions"
        ],
        score=score,
        summary=(
            "A motivated software developer with hands-on experience building "
            "modern web applications and APIs. Demonstrates a solid foundation "
            "in backend development and is well-positioned for junior to mid-level "
            "engineering roles. With a few targeted improvements, this resume "
            "could stand out significantly to technical recruiters."
        )
    )


# ── Main Service Function ─────────────────────────────────────────

async def analyze_resume(
    file_bytes: bytes,
    file_name: str,
    content_type: str,
) -> tuple[ResumeAnalysisResult, int]:

    # ── Validate file size ────────────────────────────────────────
    file_size = len(file_bytes)
    if file_size > settings.max_file_size_bytes:
        max_mb = settings.max_file_size_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise FileTooLargeError(
            f"File is {actual_mb:.1f} MB; maximum allowed size is {max_mb:.0f} MB."
        )

    # ── Validate content type ─────────────────────────────────────
    if content_type not in settings.allowed_content_types:
        raise InvalidFileTypeError(
            f"Unsupported file type '{content_type}'. Only PDF files are accepted."
        )

    # ── Extract text from PDF ─────────────────────────────────────
    try:
        resume_text = extract_text_from_pdf(file_bytes)
    except PDFParsingError as exc:
        raise ResumeTextExtractionError(str(exc)) from exc

    character_count = len(resume_text)
    logger.info("Resume '%s' parsed: %d characters, %.1f KB",
                file_name, character_count, file_size / 1024)

    # ══════════════════════════════════════════════════════════════
    # DEMO MODE — mock response, no API call
    # To switch to real AI: comment out the 2 lines below and
    # uncomment the Gemini OR OpenAI block further down
    # ══════════════════════════════════════════════════════════════
    await asyncio.sleep(1.5)  # realistic delay for demo
    analysis_result = _generate_mock_analysis(resume_text)
    logger.info("Demo analysis complete for '%s' — score: %d",
                file_name, analysis_result.score)
    return analysis_result, character_count


    # ══════════════════════════════════════════════════════════════
    # OPTION 1 — GEMINI LIVE MODE
    # Uncomment this entire block when Gemini API key is available
    # ══════════════════════════════════════════════════════════════
    # import json
    # truncated_text = resume_text[:12_000]
    # full_prompt = f"{_SYSTEM_PROMPT}\n\nHere is the resume text:\n\n{truncated_text}"
    # try:
    #     response = await asyncio.get_event_loop().run_in_executor(
    #         None,
    #         lambda: _gemini_client.models.generate_content(
    #             model=settings.gemini_model,
    #             contents=full_prompt,
    #             config=types.GenerateContentConfig(
    #                 temperature=settings.gemini_temperature,
    #                 max_output_tokens=settings.gemini_max_tokens,
    #                 response_mime_type="application/json",
    #             ),
    #         ),
    #     )
    # except Exception as exc:
    #     logger.error("Gemini API error: %s", exc)
    #     raise LLMAnalysisError("AI service unavailable. Please try again later.") from exc
    # raw_json = response.text
    # try:
    #     analysis_result = ResumeAnalysisResult(**json.loads(raw_json))
    # except Exception as exc:
    #     raise LLMAnalysisError("AI returned unexpected format. Please retry.") from exc
    # logger.info("Gemini analysis complete for '%s' — score: %d", file_name, analysis_result.score)
    # return analysis_result, character_count


    # ══════════════════════════════════════════════════════════════
    # OPTION 2 — OPENAI LIVE MODE
    # Uncomment this entire block when OpenAI API key is available
    # ══════════════════════════════════════════════════════════════
    # import json
    # truncated_text = resume_text[:12_000]
    # try:
    #     response = await _openai_client.chat.completions.create(
    #         model=settings.openai_model,
    #         max_tokens=settings.openai_max_tokens,
    #         temperature=settings.openai_temperature,
    #         messages=[
    #             {"role": "system", "content": _SYSTEM_PROMPT},
    #             {"role": "user", "content": f"Analyze this resume:\n\n{truncated_text}"},
    #         ],
    #         response_format={"type": "json_object"},
    #     )
    # except Exception as exc:
    #     logger.error("OpenAI API error: %s", exc)
    #     raise LLMAnalysisError("AI service unavailable. Please try again later.") from exc
    # raw_json = response.choices[0].message.content
    # try:
    #     analysis_result = ResumeAnalysisResult(**json.loads(raw_json))
    # except Exception as exc:
    #     raise LLMAnalysisError("AI returned unexpected format. Please retry.") from exc
    # logger.info("OpenAI analysis complete for '%s' — score: %d", file_name, analysis_result.score)
    # return analysis_result, character_count