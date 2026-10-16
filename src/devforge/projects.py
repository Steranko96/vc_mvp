"""Validated project preferences and deterministic filesystem-safe identifiers."""

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Difficulty = Literal["beginner", "intermediate"]
Language = Literal["TypeScript"]
ScaffoldLevel = Literal["minimal"]


def project_id(name: str) -> str:
    """Create a bounded ASCII slug, requiring at least one ASCII letter or digit."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:80].rstrip("-")
    if not slug:
        raise ValueError(
            "Project name must contain at least one ASCII letter or digit."
        )
    if slug in {"con", "prn", "aux", "nul"} or re.fullmatch(r"(?:com|lpt)[0-9]", slug):
        slug = f"project-{slug}"
    return slug


class ProjectConfig(BaseModel):
    """Version 1 of the local project configuration; no runtime or credential state."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
        json_schema_extra={
            "$comment": (
                "Structural validation only. Validate with ProjectConfig before use: "
                "text is trimmed before length checks, and names must yield an ASCII "
                "letter or digit after Unicode NFKD normalization."
            )
        },
    )

    schema_version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    difficulty: Difficulty
    language: Language
    scaffold_level: ScaffoldLevel

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        project_id(value)
        return value

    @property
    def project_id(self) -> str:
        return project_id(self.name)
