"""Project validation and deterministic identifiers."""

import json
from typing import Any

import pytest
from pydantic import ValidationError

from devforge.projects import ProjectConfig, project_id
from devforge.wizard import validate_text


@pytest.fixture
def values() -> dict[str, Any]:
    return dict(
        name=" My Project ",
        description=" A learning project ",
        difficulty="beginner",
        language="TypeScript",
        scaffold_level="minimal",
    )


def test_config_normalizes_whitespace(values: dict[str, Any]) -> None:
    config = ProjectConfig.model_validate(values)
    assert config.name == "My Project"
    assert config.description == "A learning project"
    assert config.project_id == "my-project"
    assert config.schema_version == 1
    assert ProjectConfig.model_validate_json(config.model_dump_json()) == config


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", " "),
        ("name", "../"),
        ("name", "你好"),
        ("name", "a" * 201),
        ("description", "\n"),
        ("description", "a" * 5001),
        ("difficulty", "expert"),
        ("language", "Ruby"),
        ("scaffold_level", "full"),
        ("schema_version", 2),
        ("api_key", "not-a-real-secret"),
    ],
)
def test_invalid_config(values: dict[str, Any], field: str, value: Any) -> None:
    values[field] = value
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate(values)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("My Project!", "my-project"),
        ("../../Hello World", "hello-world"),
        ("Café", "cafe"),
        ("CON", "project-con"),
        ("LPT1", "project-lpt1"),
        ("a" * 200, "a" * 80),
    ],
)
def test_project_ids(name: str, expected: str) -> None:
    assert project_id(name) == expected
    assert project_id(name) == project_id(name)


@pytest.mark.parametrize("difficulty", ["beginner", "intermediate"])
@pytest.mark.parametrize("language", ["TypeScript"])
@pytest.mark.parametrize("scaffold", ["minimal"])
def test_supported_selections(
    values: dict[str, Any],
    difficulty: str,
    language: str,
    scaffold: str,
) -> None:
    values.update(difficulty=difficulty, language=language, scaffold_level=scaffold)
    ProjectConfig.model_validate(values)


def test_prompt_validation() -> None:
    assert validate_text("name", "A project") is True
    assert isinstance(validate_text("name", "../"), str)
    assert isinstance(validate_text("description", " "), str)


@pytest.mark.parametrize(
    "field,value",
    [
        ("difficulty", "advanced"),
        ("language", "Python"),
        ("language", "JavaScript"),
        ("scaffold_level", "empty"),
        ("scaffold_level", "extended"),
    ],
)
def test_unsupported_mvp_preferences_are_rejected(
    values: dict[str, Any], field: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate({**values, field: value})


@pytest.mark.parametrize(
    "field,value", [("name", " "), ("name", "你好"), ("description", "\n")]
)
def test_structural_schema_requires_additional_domain_validation(
    values: dict[str, Any], field: str, value: str
) -> None:
    schema = ProjectConfig.model_json_schema()
    assert "Structural validation only" in schema["$comment"]
    constraints = schema["properties"][field]
    # These satisfy the published structural string constraints. Consumers must
    # still use the domain model, as explicitly required by the schema contract.
    assert constraints["type"] == "string"
    assert constraints["minLength"] <= len(value) <= constraints["maxLength"]
    assert "pattern" not in constraints
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate_json(json.dumps({**values, field: value}))
