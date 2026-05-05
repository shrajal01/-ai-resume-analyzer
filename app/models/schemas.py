"""
Pydantic schemas — the single source of truth for all API contracts.

These models are used for:
  - Response serialization (FastAPI auto-generates JSON from them)
  - OpenAPI / Swagger documentation (field descriptions appear in the UI)
  - Runtime validation (Pydantic raises 422 on invalid data automatically)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Health Check ─────────────────────────────────────────────────────────────

class HealthCheckResponse(BaseModel):
    status: str = Field(..., example="healthy")
    application_name: str = Field(..., example="AI Resume Analyzer API")
    version: str = Field(..., example="1.0.0")
    timestamp: datetime = Field(..., example="2024-01-15T10:30:00Z")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "application_name": "AI Resume Analyzer API",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# ── Resume Analysis ───────────────────────────────────────────────────────────

class ResumeAnalysisResult(BaseModel):
    """
    Structured output from the LLM analysis.
    Every field is typed and documented so Swagger renders useful docs.
    """

    key_skills: list[str] = Field(
        ...,
        description="Technical and soft skills identified in the resume.",
        example=["Python", "System Design", "Leadership", "SQL"],
    )
    strengths: list[str] = Field(
        ...,
        description="Positive aspects of the resume content and presentation.",
        example=["Clear quantified achievements", "Strong technical breadth"],
    )
    weaknesses: list[str] = Field(
        ...,
        description="Areas where the resume could be improved.",
        example=["Missing cover-letter hook", "No open-source contributions listed"],
    )
    suggestions: list[str] = Field(
        ...,
        description="Actionable recommendations to improve the resume.",
        example=[
            "Add measurable impact numbers to each bullet",
            "Include a GitHub profile link",
        ],
    )
    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall resume quality score from 0 (poor) to 100 (excellent).",
        example=74,
    )
    summary: str = Field(
        ...,
        description="One-paragraph executive summary of the candidate profile.",
        example="An experienced backend engineer with 5 years in distributed systems...",
    )


class ResumeAnalysisResponse(BaseModel):
    """
    Top-level API response envelope for POST /resumes/analyze.
    Wraps the analysis result with metadata for traceability.
    """

    success: bool = Field(..., example=True)
    message: str = Field(..., example="Resume analyzed successfully.")
    file_name: str = Field(..., example="john_doe_resume.pdf")
    character_count: int = Field(
        ...,
        description="Number of characters extracted from the PDF.",
        example=4821,
    )
    analysis: ResumeAnalysisResult

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Resume analyzed successfully.",
                "file_name": "john_doe_resume.pdf",
                "character_count": 4821,
                "analysis": {
                    "key_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                    "strengths": ["Strong project ownership", "Quantified results"],
                    "weaknesses": ["No leadership experience mentioned"],
                    "suggestions": ["Add a concise summary section at the top"],
                    "score": 78,
                    "summary": "A full-stack engineer with deep Python expertise...",
                },
            }
        }


# ── Error Responses ───────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, example="file")
    message: str = Field(..., example="File size exceeds the 5 MB limit.")


class ErrorResponse(BaseModel):
    """Standard error envelope — all non-2xx responses use this shape."""

    success: bool = Field(False, example=False)
    error_code: str = Field(..., example="FILE_TOO_LARGE")
    message: str = Field(..., example="The uploaded file exceeds the maximum allowed size.")
    details: Optional[list[ErrorDetail]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "FILE_TOO_LARGE",
                "message": "The uploaded file exceeds the maximum allowed size of 5 MB.",
                "details": [{"field": "file", "message": "File is 7.2 MB; limit is 5 MB."}],
            }
        }
