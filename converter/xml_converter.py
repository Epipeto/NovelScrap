"""
Converts a Book into XML (.xml).

This format is meant to be read by a possible future app: a clean and
stable structure, with the content of each chapter split into
<paragraph> elements.

Example of the generated structure:

    <?xml version='1.0' encoding='UTF-8'?>
    <book source="royalroad" url="https://...">
      <metadata>
        <title>My book</title>
        <author>Author</author>
        <source>royalroad</source>
        <url>https://...</url>
        <synopsis>...</synopsis>
        <exported>2026-09-04T...</exported>
      </metadata>
      <chapters>
        <chapter index="1" url="https://...">
          <title>Prologue</title>
          <content>
            <paragraph>First paragraph...</paragraph>
            <paragraph>Second paragraph...</paragraph>
          </content>
        </chapter>
      </chapters>
    </book>
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

from extractor.models import Book

from converter.common import default_output_path


def build_root(book: Book) -> ET.Element:
    """Builds the complete XML tree of the book."""
    root = ET.Element("book", source=book.source, url=book.url)

    # ---- metadata ----
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "title").text = book.title
    ET.SubElement(metadata, "author").text = book.author
    ET.SubElement(metadata, "source").text = book.source
    ET.SubElement(metadata, "url").text = book.url
    ET.SubElement(metadata, "synopsis").text = book.synopsis
    ET.SubElement(metadata, "exported").text = datetime.now(timezone.utc).isoformat()

    # ---- chapters ----
    chapters = ET.SubElement(root, "chapters")
    for chapter in book.chapters:
        node = ET.SubElement(
            chapters, "chapter", index=str(chapter.index), url=chapter.url
        )
        ET.SubElement(node, "title").text = chapter.title
        content = ET.SubElement(node, "content")
        for paragraph in chapter.content:
            ET.SubElement(content, "paragraph").text = paragraph

    return root


def to_xml_bytes(book: Book) -> bytes:
    """Converts the Book into XML bytes (with declaration and indentation)."""
    root = build_root(book)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True)


def convert(
    book: Book,
    output_path: str | Path | None = None,
    out_dir: str | Path | None = None,
) -> Path:
    """Saves the book as a .xml file and returns the created path."""
    path = default_output_path(book, "xml", out_dir=out_dir, output_path=output_path)
    path.write_bytes(to_xml_bytes(book))
    return path
