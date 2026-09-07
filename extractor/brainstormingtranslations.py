"""
Brainstorming Translations extractor

The HTML selectors used here were verified against the live site (2026):
    - book title / author  :  div.fic-header  h1 
    - table of contents    :  rows  bixbox bxcl epcheck .li  (each row contains the
                               chapter link; the same row repeats a "data"
                               link, so we filter and deduplicate by URL)
    - chapter content      :  div.cat-series  ->  <p> paragraphs

If Brainstorming Translations ever changes its layout, just update the selectors in this
file, without touching the rest of the program.
"""

from __future__ import annotations

import time
from urllib.parse import urljoin, urlparse

from extractor.base import BaseExtractor
from extractor.models import Book, Chapter

class BrainstormingTranslationsExtractor(BaseExtractor):
    """Brainstorming Translations extractor."""

    source = "brainstormingtranslations"

    # ------------------------------------------------------------------
    # URL recognition
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_url(url: str) -> bool:
        return "brainstormingtranslations.com" in (url or "").lower()

    @classmethod
    def is_chapter_url(cls, url: str) -> bool:
        """
        True if chapter is in the URL, false otherwise 
        """
        return "chapter" in url.lower()

    #------------------------------------------------------------------
    # Extraction
    #------------------------------------------------------------------
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
            """Downloads and returns the single chapter at the given URL."""
            soup = self._get_soup(url, headers)
            title_box = soup.find("div", class_="cat-series")
            title = title_box.get_text(strip=True) if title_box else ""
            content = self._chapter_paragraphs(soup)
            return Chapter(title=title, content=content, index=0, url=url)
        
    def fetch_book(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        delay: float = 0.0 #Used to avoid being blocked by the site (default: 0.0 = no delay)
    ) -> Book:
        """Given the URL of the book page, returns the COMPLETE Book.

        Procedure:
          1. download the book page -> title, author, synopsis, table of contents;
          2. for each chapter in the table of contents, download the chapter page.
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
        
        for index, (chapter_url, toc_title) in enumerate (
            self._table_of_contents(soup, url), start = 1
        ):
            try:
                chapter = self.fetch_chapter(chapter_url)
            except Exception as e:
                print(f"Error fetching chapter: {e}")
                chapter = Chapter(title=toc_title, content=[], index=index, url=chapter_url)
                
            book.chapters.append(chapter)
            
            if (delay > 0):
                time.sleep(delay)
            
        return book
            


    # ------------------------------------------------------------------
    # Private helpers (Brainstorming Translations specific selectors)
    # ------------------------------------------------------------------
    @staticmethod
    def _chapter_title(soup) -> str:
        """Chapter title from the chapter page."""
        info = soup.find("div", class_="fic-header")
        h1 = info.find("h1") if info else None
        return h1.get_text(strip=True) if h1 else ""


    @staticmethod
    def _chapter_paragraphs(soup) -> list[str]:
        """List of paragraphs of the chapter content."""
        content_div = soup.find("div", class_="epcontent entry-content")
        if not content_div:
            return []
        paragraphs = []
        for p in content_div.find_all("p"):
            if p:
                paragraphs.append(p.get_text(strip=True))
        return paragraphs

    @staticmethod
    def _book_meta(soup) -> tuple[str, str]:
        """(title, author) of the book from its main page."""
        info = soup.find("div", class_="infox")
        title = ""
        author = ""
        if info:
            title = info.find("h1", class_="entry-title").get_text(strip=True) or ""
            author_labels = soup.find(lambda tag: tag.name == 'b' and 'Author:' in tag.text)
            if (author_labels):
                author = author_labels.find_next_sibling('a').get_text(strip=True) or ""
                
        return title, author

    @staticmethod
    def _synopsis(soup) -> str:
        """Synopsis of the book, if present (best effort)."""
        node = soup.find("div", class_="bixbox synp")
        if node:
            return node.get_text(strip=True) or ""
        return ""
        
    def _table_of_contents(self, soup, book_url: str) -> list[tuple[str, str]]:
        """List of (absolute_chapter_url, chapter_title) as they appear in
        the book page's table of contents.
        """
        links: list[tuple[str, str]] = []
        seen: set[str] = set()

        chapter_box = soup.find("div", class_="bixbox bxcl epcheck")
        rows = chapter_box.find_all("li")
        if rows:
            for row in rows:
                anchor = row.find("a", href=True)
                if not anchor:
                    continue
                chapter_url = urljoin(book_url, anchor["href"])
                if not self.is_chapter_url(chapter_url) or chapter_url in seen:
                    continue
                seen.add(chapter_url)
                title = anchor.find("div", class_="epl-title").get_text(strip=True) or ""
                links.append((chapter_url, title))
            return links
        return links


