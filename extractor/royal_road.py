"""
Royal Road extractor (https://www.royalroad.com).

The HTML selectors used here were verified against the live site (2026):
    - book title / author  :  div.fic-header  h1  /  a.font-white
    - table of contents    :  rows  tr.chapter-row  (each row contains the
                               chapter link; the same row repeats a "data"
                               link, so we filter and deduplicate by URL)
    - chapter content      :  div.chapter-content  ->  <p> paragraphs

If Royal Road ever changes its layout, just update the selectors in this
file, without touching the rest of the program.
"""

from __future__ import annotations

import time
from urllib.parse import urljoin, urlparse

from extractor.base import BaseExtractor
from extractor.models import Book, Chapter


class RoyalRoadExtractor(BaseExtractor):
    """Royal Road extractor."""

    source = "royalroad"

    # ------------------------------------------------------------------
    # URL recognition
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_url(url: str) -> bool:
        return "royalroad.com" in (url or "").lower()

    @classmethod
    def is_chapter_url(cls, url: str) -> bool:
        """An RR chapter has a path of the form:
        /fiction/<book_id>/<book_slug>/<chapter_id>/<chapter_slug>
        i.e. more than 2 segments after "fiction". The book page has only 2.
        """
        parts = [p for p in urlparse(url).path.split("/") if p]
        try:
            index = parts.index("fiction")
        except ValueError:
            return False
        return len(parts) - (index + 1) > 2

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
        """Downloads and returns the single chapter at the given URL."""
        soup = self._get_soup(url, headers)
        title = self._chapter_title(soup)
        content = self._chapter_paragraphs(soup)
        return Chapter(title=title, content=content, index=0, url=url)

    def fetch_book(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        delay: float = 0.0,
    ) -> Book:
        """Given the URL of the book page, returns the COMPLETE Book.

        Procedure:
          1. download the book page -> title, author, synopsis, table of contents;
          2. for each chapter in the table of contents, download the chapter page.

        `delay` parameter: seconds to wait between one chapter and the next
        (useful to be "polite" to the site and avoid being blocked).
        """
        soup = self._get_soup(url, headers)
        title, author = self._book_meta(soup)

        book = Book(
            source=self.source,
            title=title,
            author=author,
            url=url,
            synopsis=self._synopsis(soup),
        )

        for index, (chapter_url, toc_title) in enumerate(
            self._table_of_contents(soup, url), start=1
        ):
            try:
                chapter = self.fetch_chapter(chapter_url, headers)
            except Exception:
                # A chapter that does not respond must not block the whole book:
                # we still record it in the table of contents, with empty content.
                chapter = Chapter(title=toc_title, content=[], index=index, url=chapter_url)
            else:
                chapter.index = index
                if not chapter.title:
                    chapter.title = toc_title
            book.chapters.append(chapter)

            if delay > 0:
                time.sleep(delay)

        return book

    # ------------------------------------------------------------------
    # Private helpers (Royal Road specific selectors)
    # ------------------------------------------------------------------
    @staticmethod
    def _chapter_title(soup) -> str:
        """Chapter title from the chapter page."""
        info = soup.find("div", class_="fic-header")
        h1 = info.find("h1") if info else None
        return h1.get_text(strip=True) if h1 else ""

    @staticmethod
    def _paragraph_text(paragraph) -> str:
        """Reconstructs the text of a paragraph.

        Without this, <br> tags inside a <p> would split the text into several
        fragments; joining the fragments in order reassembles the full sentence.
        """
        parts = [part.strip() for part in paragraph.stripped_strings if part.strip()]
        return " ".join(parts)

    @staticmethod
    def _chapter_paragraphs(soup) -> list[str]:
        """List of paragraphs of the chapter content."""
        content_div = soup.find("div", class_="chapter-content")
        if not content_div:
            return []
        paragraphs = []
        for p in content_div.find_all("p"):
            text = RoyalRoadExtractor._paragraph_text(p)
            if text:
                paragraphs.append(text)
        return paragraphs

    @staticmethod
    def _book_meta(soup) -> tuple[str, str]:
        """(title, author) of the book from its main page."""
        info = soup.find("div", class_="fic-header")
        if info:
            h1 = info.find("h1")
            title = h1.get_text(strip=True) if h1 else ""
            author_tag = info.find("a", class_="font-white") or info.find("a", href=True)
            author = author_tag.get_text(strip=True) if author_tag else ""
        else:
            title = ""
            author = ""
        return title, author

    @staticmethod
    def _synopsis(soup) -> str:
        """Synopsis of the book, if present (best effort)."""
        for selector in (
            "div.fic-description",
            "div#fic-description",
            "div.description",
            "div[property='description']",
        ):
            node = soup.select_one(selector)
            if node:
                text = node.get_text(" ", strip=True)
                if text:
                    return text
        return ""

    def _table_of_contents(self, soup, book_url: str) -> list[tuple[str, str]]:
        """List of (absolute_chapter_url, chapter_title) as they appear in
        the book page's table of contents.

        Note: Royal Road shows only the most recently published chapters on
        the main page (not always the full archive). For very long novels
        this will need to be extended with the eventual "full table of
        contents" page.
        """
        links: list[tuple[str, str]] = []
        seen: set[str] = set()

        rows = soup.select("tr.chapter-row")
        if rows:
            for row in rows:
                anchor = row.find("a", href=True)
                if not anchor:
                    continue
                chapter_url = urljoin(book_url, anchor["href"])
                if not self.is_chapter_url(chapter_url) or chapter_url in seen:
                    continue
                seen.add(chapter_url)
                title = anchor.get_text(strip=True) or ""
                links.append((chapter_url, title))
            return links

        # Generic fallback in case the layout changes: every "/fiction/..."
        # link that looks like a chapter.
        for anchor in soup.find_all("a", href=True):
            chapter_url = urljoin(book_url, anchor["href"])
            if not self.is_chapter_url(chapter_url) or chapter_url in seen:
                continue
            seen.add(chapter_url)
            title = anchor.get_text(strip=True) or ""
            links.append((chapter_url, title))

        return links
