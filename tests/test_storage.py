"""Persistence protects existing data and never publishes partial JSON."""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from devforge.projects import ProjectConfig
from devforge.storage import save_project


@pytest.fixture
def config() -> ProjectConfig:
    return ProjectConfig(
        name="My Project",
        description="Learn by building",
        difficulty="intermediate",
        language="TypeScript",
        scaffold_level="minimal",
    )


def test_save_project(tmp_path: Path, config: ProjectConfig) -> None:
    path = save_project(config, tmp_path)
    assert path == tmp_path / ".devforge/projects/my-project.json"
    assert json.loads(path.read_text(encoding="utf-8")) == config.model_dump()
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("name", ["My Project", "my-project!"])
def test_collision_preserves_existing(
    tmp_path: Path, config: ProjectConfig, name: str
) -> None:
    path = save_project(config, tmp_path)
    original = path.read_bytes()
    other = ProjectConfig.model_validate({**config.model_dump(), "name": name})
    with pytest.raises(FileExistsError):
        save_project(other, tmp_path)
    assert path.read_bytes() == original
    assert list(path.parent.iterdir()) == [path]


def test_directory_error(tmp_path: Path, config: ProjectConfig) -> None:
    (tmp_path / ".devforge").write_text("existing file")
    with pytest.raises(OSError):
        save_project(config, tmp_path)
    assert (tmp_path / ".devforge").read_text() == "existing file"


@pytest.mark.parametrize("operation", ["os.link", "os.fsync"])
def test_write_failure_cleans_up(
    tmp_path: Path, config: ProjectConfig, operation: str
) -> None:
    with patch(f"devforge.storage.{operation}", side_effect=OSError("disk failure")):
        with pytest.raises(OSError, match="disk failure"):
            save_project(config, tmp_path)
    assert list((tmp_path / ".devforge/projects").iterdir()) == []


def test_schema_matches_model() -> None:
    schema = Path(__file__).parents[1] / "docs/project-config-v1.schema.json"
    assert json.loads(schema.read_text()) == ProjectConfig.model_json_schema()


@pytest.mark.parametrize("component", [".devforge", "projects"])
@pytest.mark.parametrize("dangling", [False, True])
def test_metadata_symlinks_are_rejected(
    tmp_path: Path, config: ProjectConfig, component: str, dangling: bool
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    if not dangling:
        outside.mkdir()
    link = root / ".devforge"
    if component == "projects":
        link.mkdir()
        link /= "projects"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        save_project(config, root)
    if dangling:
        assert not outside.exists()
    else:
        assert list(outside.iterdir()) == []


def test_destination_symlink_is_not_overwritten(
    tmp_path: Path, config: ProjectConfig
) -> None:
    directory = tmp_path / ".devforge/projects"
    directory.mkdir(parents=True)
    outside = tmp_path / "existing.json"
    outside.write_text("preserve me")
    destination = directory / "my-project.json"
    destination.symlink_to(outside)
    with pytest.raises(FileExistsError):
        save_project(config, tmp_path)
    assert outside.read_text() == "preserve me"
    assert destination.is_symlink()
    assert list(directory.iterdir()) == [destination]


def test_cleanup_failure_after_publication_is_success(
    tmp_path: Path, config: ProjectConfig, caplog: pytest.LogCaptureFixture
) -> None:
    with patch(
        "devforge.storage.os.unlink", side_effect=PermissionError("cleanup denied")
    ):
        path = save_project(config, tmp_path)
    assert json.loads(path.read_text()) == config.model_dump()
    assert "Configuration saved" in caplog.text
    assert "Remove it manually" in caplog.text
    temporary = next(path.parent.glob(".tmp-*"))
    assert str(temporary) in caplog.text


def test_cleanup_failure_preserves_primary_error(
    tmp_path: Path, config: ProjectConfig, caplog: pytest.LogCaptureFixture
) -> None:
    with (
        patch("devforge.storage.os.link", side_effect=OSError("publication failed")),
        patch(
            "devforge.storage.os.unlink", side_effect=PermissionError("cleanup denied")
        ),
    ):
        with pytest.raises(OSError, match="publication failed"):
            save_project(config, tmp_path)
    assert not (tmp_path / ".devforge/projects/my-project.json").exists()
    assert "Configuration save failed" in caplog.text
    assert "cleanup denied" in caplog.text


def test_unsupported_filesystem_api_fails_before_writing(
    tmp_path: Path, config: ProjectConfig
) -> None:
    with patch("devforge.storage._DIRECTORY_RELATIVE_SUPPORTED", False):
        with pytest.raises(OSError, match="directory-relative"):
            save_project(config, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_directory_symlink_swap_cannot_redirect_writes(
    tmp_path: Path, config: ProjectConfig
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    original_open = os.open
    moved = root / "original-metadata"

    def swap_after_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original_open(path, flags, *args, **kwargs)
        if path == ".devforge":
            (root / ".devforge").rename(moved)
            (root / ".devforge").symlink_to(outside, target_is_directory=True)
        return descriptor

    with patch("devforge.storage.os.open", side_effect=swap_after_open):
        save_project(config, root)
    assert list(outside.iterdir()) == []
    saved = moved / "projects/my-project.json"
    assert json.loads(saved.read_text()) == config.model_dump()
