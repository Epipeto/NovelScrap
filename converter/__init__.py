"""
Package `converter`: converts a `Book` into the various output formats.

Available formats (one module per format):
    txt  -> txt_converter.py   (plain text)
    epub -> epub_converter.py  (EPUB ebook)
    xml  -> xml_converter.py   (XML for the future app)

Single entry point:
    from converter import convert_book
    convert_book(book, "epub", out_dir="output")

Every module exposes the same signature:
    convert(book, output_path=None, out_dir=None) -> Path
"""

from __future__ import annotations

from pathlib import Path

from extractor.models import Book

from converter import epub_converter, txt_converter, xml_converter

#: Map format name -> convert function
CONVERTERS = {
    "txt": txt_converter.convert,
    "epub": epub_converter.convert,
    "xml": xml_converter.convert,
}

__all__ = ["CONVERTERS", "convert_book", "txt_converter", "epub_converter", "xml_converter"]


def supported_formats() -> list[str]:
    """List of supported format names (sorted)."""
    return sorted(CONVERTERS)


def convert_book(
    book: Book,
    fmt: str,
    output_path: str | Path | None = None,
    out_dir: str | Path | None = None,
) -> Path:
    """Converts a Book into the requested format and returns the created file.

    `fmt` can be "txt", "epub" or "xml".
    """
    key = fmt.lower()
    if key not in CONVERTERS:
        raise ValueError(
            f"Formato non supportato: {fmt!r}. "
            f"Formati disponibili: {', '.join(supported_formats())}"
        )
    return CONVERTERS[key](book, output_path=output_path, out_dir=out_dir)
