"""
schema/pydantic_models.py
--------------------------
Pydantic models for data validation.

WHY PYDANTIC HERE?
  The LLM may return slightly malformed or incomplete JSON.
  Before we attempt any INSERT into PostgreSQL, we run the data through
  these models so that:
    • Required fields are present (first_name, last_name, email)
    • Types are coerced correctly (e.g. "5" → 5.0 for experience)
    • Lists/dicts default to [] / {} if missing (skills, education, etc.)
    • None values are allowed for optional fields

  The MCP `save_candidate` tool calls `CandidateSchema.model_validate()`
  before executing any SQL — this gives a clean error message instead of
  a cryptic psycopg2 exception.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Education entry (nested inside CandidateSchema)
# ─────────────────────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    degree:      str = ""
    institution: str = ""
    year:        str = ""


# ─────────────────────────────────────────────────────────────────────────────
# Candidate — primary schema used by the MCP save_candidate tool
# ─────────────────────────────────────────────────────────────────────────────

class CandidateSchema(BaseModel):
    # ── Required ─────────────────────────────────────────────────────────────
    first_name: str
    last_name:  str
    email:      str          # EmailStr would be ideal but LLM output isn't always RFC-valid

    # ── Optional contact ─────────────────────────────────────────────────────
    phone:        str | None = None
    linkedin_url: str | None = None

    # ── Current role ─────────────────────────────────────────────────────────
    current_company:   str | None = None
    current_job_title: str | None = None

    # ── Experience ───────────────────────────────────────────────────────────
    total_experience_years: float = 0.0

    # ── Structured data (stored as JSONB in Postgres) ─────────────────────────
    skills:           list[str]        = []
    skill_experience: dict[str, float] = {}
    education:        list[EducationEntry] = []

    # ── Raw content ──────────────────────────────────────────────────────────
    raw_text:    str | None = None
    source_file: str | None = None

    # ── Validators ───────────────────────────────────────────────────────────

    @field_validator("first_name", "last_name", "email", mode="before")
    @classmethod
    def must_not_be_empty(cls, v: Any) -> str:
        if not str(v).strip():
            raise ValueError("Field cannot be empty")
        return str(v).strip()

    @field_validator("total_experience_years", mode="before")
    @classmethod
    def coerce_experience(cls, v: Any) -> float:
        """Accept int, float, or numeric string."""
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return 0.0

    @field_validator("skills", mode="before")
    @classmethod
    def coerce_skills(cls, v: Any) -> list[str]:
        """Accept a list or a comma-separated string."""
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return []

    @field_validator("skill_experience", mode="before")
    @classmethod
    def coerce_skill_experience(cls, v: Any) -> dict[str, float]:
        """Ensure all values are floats."""
        if not isinstance(v, dict):
            return {}
        result = {}
        for skill, years in v.items():
            try:
                result[str(skill)] = round(float(years), 2)
            except (TypeError, ValueError):
                result[str(skill)] = 0.0
        return result

    @field_validator("education", mode="before")
    @classmethod
    def coerce_education(cls, v: Any) -> list[dict]:
        """Accept list of dicts or empty."""
        if isinstance(v, list):
            return v
        return []