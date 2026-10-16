"""Collision-safe publication of complete local project configurations."""

import logging
import os
from contextlib import ExitStack
from pathlib import Path
from secrets import token_hex

from devforge.projects import ProjectConfig

logger = logging.getLogger(__name__)
_DIRECTORY_RELATIVE_SUPPORTED = all(
    operation in os.supports_dir_fd
    for operation in (os.open, os.mkdir, os.link, os.unlink)
) and hasattr(os, "O_NOFOLLOW")


def save_project(config: ProjectConfig, root: Path) -> Path:
    """Publish JSON without overwrites or following metadata directory symlinks."""
    if not _DIRECTORY_RELATIVE_SUPPORTED:
        raise OSError(
            "Safe project storage requires directory-relative filesystem support."
        )

    root = root.resolve(strict=True)
    destination = root / ".devforge" / "projects" / f"{config.project_id}.json"
    payload = config.model_dump_json(indent=2) + "\n"
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        directory_fd = os.open(root, flags)
        stack.callback(os.close, directory_fd)
        for component in (".devforge", "projects"):
            try:
                os.mkdir(component, dir_fd=directory_fd)
            except FileExistsError:
                pass
            # Keep operations anchored to open directories even if a path is
            # subsequently replaced with a symlink.
            directory_fd = os.open(component, flags, dir_fd=directory_fd)
            stack.callback(os.close, directory_fd)

        temporary = f".tmp-{token_hex(16)}"
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
            dir_fd=directory_fd,
        )
        published = False
        try:
            with os.fdopen(file_fd, "w", encoding="utf-8") as file:
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.link(
                temporary,
                destination.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            published = True
        finally:
            try:
                os.unlink(temporary, dir_fd=directory_fd)
            except OSError as error:
                outcome = (
                    "Configuration saved" if published else "Configuration save failed"
                )
                logger.warning(
                    "%s; could not remove temporary file %s: %s. Remove it manually.",
                    outcome,
                    destination.parent / temporary,
                    error,
                )
    return destination
