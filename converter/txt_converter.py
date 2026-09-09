"""
Converts a Book into plain text (.txt).

The information is organized in a logical way:

    <Book title>
    by <Author>

    Source: royalroad   |   URL: ...
    Chapters: 42

    ----------------------------------------
    1. <Chapter title>
    ----------------------------------------

    <paragraph 1>

    <paragraph 2>
"""

from __future__ import annotations

from pathlib import Path

from extractor.models import Book

from converter.common import default_output_path

#: Horizontal separator used between one chapter and the next.
_RULE = "-" * 40


def to_text(book: Book) -> str:
    """Converts the Book into a single readable text string."""
    lines: list[str] = []
    lines.append(book.title or "Senza titolo")
    if book.author:
        lines.append(f"di {book.author}")
    lines.append("")
    lines.append(f"Sorgente: {book.source}   |   URL: {book.url}")
    lines.append(f"Capitoli: {book.chapter_count}")
    lines.append("")

    for chapter in book.chapters:
        title = chapter.title or f"Capitolo {chapter.index}"
        lines.append(_RULE)
        if chapter.index:
            lines.append(f"{chapter.index}. {title}")
        else:
            lines.append(title)
        lines.append(_RULE)
        lines.append("")
        for paragraph in chapter.content:
            lines.append(paragraph)
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def convert(
    book: Book,
    output_path: str | Path | None = None,
    out_dir: str | Path | None = None,
) -> Path:
    """Saves the book as a .txt file and returns the created path."""
    path = default_output_path(book, "txt", out_dir=out_dir, output_path=output_path)
    path.write_text(to_text(book), encoding="utf-8")
    return path
