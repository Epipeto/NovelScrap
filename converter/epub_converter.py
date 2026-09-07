"""
Converts a Book into EPUB (.epub).

A valid EPUB 3 is generated using ONLY the standard library (zipfile +
xml): no extra dependency. The resulting file is a .zip archive with the
following structure:

    mimetype                     (mandatory, first file, uncompressed)
    META-INF/container.xml
    OEBPS/content.opf            (manifest + spine of the book)
    OEBPS/toc.ncx                (table of contents for EPUB 2 compatibility)
    OEBPS/nav.xhtml              (EPUB 3 table of contents)
    OEBPS/style.css
    OEBPS/chapter_0001.xhtml     (one file per chapter)
    ...
"""

from __future__ import annotations

import datetime as _dt
import io
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from extractor.models import Book

from converter.common import default_output_path

# ----------------------------------------------------------------------
# Small XML escaping helpers
# ----------------------------------------------------------------------
def _esc(text: str) -> str:
    """Escapes an XML text (text nodes)."""
    return escape(text or "")


def _modified_now() -> str:
    """Modification date in the format required by the EPUB standard."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----------------------------------------------------------------------
# Generation of the single internal files
# ----------------------------------------------------------------------
def _chapter_filename(index: int, total: int) -> str:
    """chapter_0001.xhtml, chapter_0002.xhtml ..."""
    width = max(3, len(str(total)))
    return f"chapter_{index:0{width}d}.xhtml"


def _chapter_xhtml(chapter) -> str:
    title = chapter.title or f"Capitolo {chapter.index}"
    paragraphs = chapter.content or ["(capitolo vuoto)"]

    body = "\n".join(f"    <p>{_esc(p)}</p>" for p in paragraphs)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title>{_esc(title)}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <h2 class="chapter-title">{_esc(title)}</h2>
{body}
</body>
</html>
"""


def _nav_xhtml(book: Book) -> str:
    items = []
    for ch in book.chapters:
        filename = _chapter_filename(ch.index, book.chapter_count)
        title = ch.title or f"Capitolo {ch.index}"
        items.append(f'      <li><a href="{filename}">{_esc(title)}</a></li>')
    ol = "\n".join(items) if items else "      <li>(nessun capitolo)</li>"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head>
  <title>Table of Contents</title>
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>Table of Contents</h1>
    <ol>
{ol}
    </ol>
  </nav>
</body>
</html>
"""


def _ncx_xhtml(book: Book, uid: str) -> str:
    points = []
    for ch in book.chapters:
        title = ch.title or f"Capitolo {ch.index}"
        filename = _chapter_filename(ch.index, book.chapter_count)
        points.append(
            f'    <navPoint id="navpoint-{ch.index}" playOrder="{ch.index}">\n'
            f"      <navLabel><text>{_esc(title)}</text></navLabel>\n"
            f'      <content src="{filename}"/>\n'
            f"    </navPoint>"
        )
    navmap = "\n".join(points) if points else ""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{uid}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{_esc(book.title)}</text></docTitle>
  <navMap>
{navmap}
  </navMap>
</ncx>
"""


def _content_opf(book: Book, uid: str) -> str:
    total = book.chapter_count

    manifest = [
        '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '    <item id="css" href="style.css" media-type="text/css"/>',
    ]
    spine = []
    for ch in book.chapters:
        cid = f"c{ch.index}"
        filename = _chapter_filename(ch.index, total)
        manifest.append(
            f'    <item id="{cid}" href="{filename}" media-type="application/xhtml+xml"/>'
        )
        spine.append(f'    <itemref idref="{cid}"/>')

    manifest_str = "\n".join(manifest)
    spine_str = "\n".join(spine)
    author = _esc(book.author) if book.author else "Unknown"

    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="en">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{_esc(book.title)}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">{_modified_now()}</meta>
  </metadata>
  <manifest>
{manifest_str}
  </manifest>
  <spine toc="ncx">
{spine_str}
  </spine>
</package>
"""


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def to_epub_bytes(book: Book) -> bytes:
    """Generates the binary content of the .epub file in memory."""
    if not book.chapters:
        raise ValueError("Il libro non ha capitoli: impossibile creare un EPUB.")

    uid = str(uuid.uuid4())
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" '
        'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/content.opf" '
        'media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>\n"
    )
    css = (
        "body { font-family: serif; line-height: 1.5; margin: 5%; }\n"
        "h2.chapter-title { text-align: center; }\n"
        "p { text-indent: 1.2em; margin: 0.4em 0; }\n"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        # "mimetype" MUST be the first file and must be uncompressed.
        zf.writestr(
            zipfile.ZipInfo("mimetype"),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        zf.writestr("META-INF/container.xml", container)
        zf.writestr("OEBPS/content.opf", _content_opf(book, uid))
        zf.writestr("OEBPS/toc.ncx", _ncx_xhtml(book, uid))
        zf.writestr("OEBPS/nav.xhtml", _nav_xhtml(book))
        zf.writestr("OEBPS/style.css", css)
        for chapter in book.chapters:
            filename = _chapter_filename(chapter.index, book.chapter_count)
            zf.writestr(f"OEBPS/{filename}", _chapter_xhtml(chapter))

    return buffer.getvalue()


def convert(
    book: Book,
    output_path: str | Path | None = None,
    out_dir: str | Path | None = None,
) -> Path:
    """Saves the book as a .epub file and returns the created path."""
    path = default_output_path(book, "epub", out_dir=out_dir, output_path=output_path)
    path.write_bytes(to_epub_bytes(book))
    return path
