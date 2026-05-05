"""
API Routes — the HTTP adapter layer.

Responsibilities (and ONLY these):
  - Map HTTP verbs + paths to service calls
  - Translate service exceptions → correct HTTP status codes
  - Return typed response models

Business logic lives in services/. This file stays thin.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models.schemas import (
    ErrorResponse,
    HealthCheckResponse,
    ResumeAnalysisResponse,
)
from app.services.resume_service import (
    FileTooLargeError,
    InvalidFileTypeError,
    LLMAnalysisError,
    ResumeTextExtractionError,
    analyze_resume,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# ── Health Check ─────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description=(
        "Returns the current health status of the API. "
        "Use this endpoint for load-balancer liveness probes. "
        "Response is cacheable for up to 30 seconds."
    ),
    tags=["Health"],
)
async def health_check() -> HealthCheckResponse:
    """
    Liveness probe endpoint.

    - **Returns 200** when the API process is running.
    - Suitable for Kubernetes liveness/readiness probes.
    - **Caching**: clients and proxies may cache this response for 30 s
      (`Cache-Control: public, max-age=30`).
    """
    return HealthCheckResponse(
        status="healthy",
        application_name=settings.application_name,
        version=settings.application_version,
        timestamp=datetime.now(timezone.utc),
    )


# ── Resume Analysis ───────────────────────────────────────────────────────────

@router.post(
    "/resumes/analyze",
    response_model=ResumeAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a Resume",
    description=(
        "Upload a PDF resume (max 5 MB). "
        "The API extracts text, sends it to an LLM, and returns a structured "
        "analysis with skills, strengths, weaknesses, suggestions, and a score."
    ),
    tags=["Resume"],
    responses={
        200: {"description": "Resume analyzed successfully.", "model": ResumeAnalysisResponse},
        400: {"description": "Invalid file type or unreadable PDF.", "model": ErrorResponse},
        413: {"description": "File exceeds the 5 MB size limit.", "model": ErrorResponse},
        422: {"description": "Validation error (missing file, wrong field name).", "model": ErrorResponse},
        503: {"description": "LLM service temporarily unavailable.", "model": ErrorResponse},
    },
)
async def analyze_resume_endpoint(
    file: UploadFile = File(
        ...,
        description="PDF resume file. Must be a valid PDF. Maximum size: 5 MB.",
    ),
) -> ResumeAnalysisResponse:
    """
    **POST /resumes/analyze**

    Upload your resume as a multipart/form-data PDF file.

    ### What happens internally:
    1. File size and MIME type are validated.
    2. Text is extracted from the PDF using PyMuPDF.
    3. Extracted text is sent to an LLM with a structured prompt.
    4. The LLM response is validated and returned as typed JSON.

    ### Example curl:
    ```bash
    curl -X POST http://localhost:8000/resumes/analyze \\
         -F "file=@/path/to/resume.pdf"
    ```

    ### Caching strategy:
    Results are **not cached** by default because resumes are user-specific.
    For high-traffic scenarios, consider caching by SHA-256 hash of the PDF bytes
    with a TTL of 1 hour (see README for Redis example).
    """
    file_bytes = await file.read()
    file_name = file.filename or "unknown.pdf"
    content_type = file.content_type or ""

    try:
        analysis_result, character_count = await analyze_resume(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=content_type,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ErrorResponse(
                error_code="FILE_TOO_LARGE",
                message=str(exc),
            ).model_dump(),
        )
    except InvalidFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="INVALID_FILE_TYPE",
                message=str(exc),
            ).model_dump(),
        )
    except ResumeTextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error_code="PDF_PARSE_FAILED",
                message=str(exc),
            ).model_dump(),
        )
    except LLMAnalysisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse(
                error_code="LLM_UNAVAILABLE",
                message=str(exc),
            ).model_dump(),
        )

    return ResumeAnalysisResponse(
        success=True,
        message="Resume analyzed successfully.",
        file_name=file_name,
        character_count=character_count,
        analysis=analysis_result,
    )
