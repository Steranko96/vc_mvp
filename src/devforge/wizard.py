"""Questionary prompts for project configuration."""

from typing import Any, get_args

import questionary
from pydantic import ValidationError

from devforge.projects import Difficulty, Language, ProjectConfig, ScaffoldLevel


class WizardCancelled(Exception):
    """The learner cancelled before saving."""


def validate_text(field: str, value: str) -> bool | str:
    """Reuse domain validation to offer immediate feedback in text prompts."""
    values: dict[str, Any] = {
        "name": "Project",
        "description": "A learning project",
        "difficulty": "beginner",
        "language": "TypeScript",
        "scaffold_level": "minimal",
        field: value,
    }
    try:
        ProjectConfig.model_validate(values)
    except ValidationError as error:
        return str(error.errors()[0]["msg"])
    return True


def collect_project_config() -> ProjectConfig:
    """Collect all preferences before allowing any persistence."""
    values: dict[str, Any] = {}
    try:
        for field, label in (
            ("name", "Project name"),
            ("description", "Project description"),
        ):
            answer = questionary.text(
                label,
                validate=lambda value, field=field: validate_text(field, value),
            ).unsafe_ask()
            if answer is None:
                raise WizardCancelled
            values[field] = answer
        for field, label, choices, default in (
            ("difficulty", "Difficulty", get_args(Difficulty), "beginner"),
            ("language", "Language", get_args(Language), "TypeScript"),
            ("scaffold_level", "Scaffold level", get_args(ScaffoldLevel), "minimal"),
        ):
            answer = questionary.select(
                label, choices=choices, default=default
            ).unsafe_ask()
            if answer is None:
                raise WizardCancelled
            values[field] = answer
    except (KeyboardInterrupt, EOFError) as error:
        raise WizardCancelled from error
    return ProjectConfig.model_validate(values)
