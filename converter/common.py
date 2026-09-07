"""Shared utilities for the converters (file names, output paths...)."""

from __future__ import annotations

import re
from pathlib import Path

from extractor.models import Book


def sanitize_filename(name: str, fallback: str = "libro") -> str:
    """Makes `name` a valid file name (removes forbidden characters)."""
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name).strip(" ._")
    return cleaned or fallback


def default_output_path(
    book: Book,
    extension: str,
    out_dir: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Computes the path where the converted file will be saved.

    - if `output_path` is passed, it is used (adding the extension if
      missing);
    - otherwise `out_dir` is created (default: current folder) with a name
      derived from the book: "<title> - <author>.<extension>".
    """
    if output_path:
        path = Path(output_path)
        return path if path.suffix else path.with_suffix(f".{extension}")

    folder = Path(out_dir) if out_dir else Path.cwd()
    folder.mkdir(parents=True, exist_ok=True)

    author_part = f" - {book.author}" if book.author else ""
    base_name = sanitize_filename(f"{book.title}{author_part}")
    return folder / f"{base_name}.{extension}"
