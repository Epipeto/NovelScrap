"""
Configurable extractor – generic template for simple paginated sites.

This extractor is driven by a declarative ``config`` dictionary so that
adding a new similar site only requires a new subclass with
``domain`` / ``config`` / ``delay`` (see novel_full.py), without duplicating
extraction logic.

The selectors below were verified against the live sites that currently use
this template (e.g. novelfull.com, 2026):
    - book title / author / description : selectors in config["book"]
    - chapter title + number            : config["chapter_title"] (regex on title)
    - chapter content paragraphs        : config["content"] (selector + optional attribute)
    - chapter list pagination           : config["chapter_list"]["last_page"] -> pattern
    - chapter list per page             : ?{request_keyword}={index} -> chapter_info links

If a site changes its layout, just update the ``config`` in its subclass,
without touching the rest of the program.
"""

from extractor.base import BaseExtractor
from extractor.models import Book, Chapter

import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode
import requests


class ConfigurableExtractor(BaseExtractor):
    """Generic extractor driven by a declarative ``config`` dictionary."""

    #: Domain substring to match in ``is_valid_url`` (e.g. "novelfull.com").
    domain: str = ""
    #: Declarative selectors / patterns – see module docstring for schema.
    config: dict = {}
    #: Polite delay in seconds between chapter fetches.
    delay: int = 0.5

    # ------------------------------------------------------------------
    # URL recognition
    # ------------------------------------------------------------------
    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """True if this extractor can handle the given URL.

        Configurable check: ``domain`` must be a substring of the URL netloc.
        Subclasses set ``domain`` to enable automatic dispatch.
        """
        if not cls.domain:
            return False
        return cls.domain in urlparse(url).netloc.lower()

    # is_chapter_url is inherited from BaseExtractor:
    # default check is ``"chapter" in path.lower()`` (base.py).

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
        """Downloads and returns the single chapter at the given URL.

        Uses ``config["chapter_title"]`` for title and index (regex extraction)
        and ``config["content"]`` for paragraph list (attribute vs. text).
        """
        # Download and parse the chapter page.
        soup = self._get_soup(url=url, headers=headers)

        # Extract chapter title via configured selector.
        chapter_title_el = soup.select_one(self.__class__.config["chapter_title"]["selector"])
        chapter_title = None
        if chapter_title_el:
            chapter_title = chapter_title_el.get_text(strip=True)

        # Extract chapter index via regex on the title string, if a pattern is configured.
        # The pattern's first match is parsed as int(float(...)) to handle "32.5" cases.
        pattern = self.__class__.config["chapter_title"].get("chapter_number_pattern")
        if pattern and chapter_title:
            match = re.search(pattern, chapter_title)
            chapter_index = int(float(match.group(0))) if match else 0

        # Extract paragraph list via configured selector.
        chapter_content_els = soup.select(self.__class__.config["content"]["selector"])
        chapter_content = []

        # If an attribute is configured, extract that attribute; otherwise use text.
        attr_name = self.__class__.config["content"].get("attribute")
        if attr_name:
            chapter_content = [el.get(attr_name).strip() for el in chapter_content_els if el.get(attr_name)]
        else:
            chapter_content = [el.get_text(strip=True) for el in chapter_content_els]

        return Chapter(title=chapter_title, content=chapter_content, index=chapter_index, url=url)

    def fetch_book(self, url: str, headers: dict[str, str] | None = None) -> Book:
        """Given the URL of the book page, returns the COMPLETE Book.

        Procedure:
          1. download the book page -> pagination size + book metadata;
          2. for each pagination index (1..last_page_n) fetch the chapter list
             via ``_get_chapter_list``;
          3. for each chapter entry, download the chapter page (fallback to
             empty Chapter on failure so one bad chapter does not block the book).

        ``delay`` (class attribute) is respected between chapters.
        """
        soup = self._get_soup(url=url, headers=headers)
        # Determine how many pagination pages the chapter list spans.
        last_page_n = self._get_chapter_index_pages_number(soup=soup, last_page_config=self.__class__.config["chapter_list"]["last_page"])

        # Extract book metadata (title, author, description) from the main page.
        book_metadata = self._get_ln_metadata(soup=soup, book_config=self.__class__.config["book"])

        book = Book(
            source=self.domain,
            title=book_metadata["title"],
            author=book_metadata["author"],
            synopsis=book_metadata["description"],
            url=url
        )

        # Sequential index for fallback ordering (ensures 1..N even if chapter pages lack numbers).
        index = 0
        for page_n in range(1, last_page_n+1):
            # Fetch dict {chapter_title: chapter_url} for this pagination page.
            chapter_list = self._get_chapter_list(bookUrl=url, index=page_n, headers=headers)
            for chapter_title, chapter_url in chapter_list.items():
                index += 1
                try:
                    chapter = self.fetch_chapter(chapter_url, headers)
                except Exception:
                    # A chapter that does not respond must not block the whole book:
                    # we still record it in the table of contents, with empty content.
                    chapter = Chapter(title=chapter_title, content=[], index=index, url=chapter_url)
                else:
                    # Use sequential index so chapters stay ordered even if parsed index differs.
                    chapter.index = index
                    if not chapter.title:
                        chapter.title = chapter_title

                book.chapters.append(chapter)

                # Polite delay between chapter requests.
                time.sleep(self.__class__.delay)

        return book

    # ------------------------------------------------------------------
    # Private helpers (config-driven selectors)
    # ------------------------------------------------------------------
    @staticmethod
    def _get_ln_metadata(soup: BeautifulSoup, book_config: dict) -> dict:
        """Extracts book metadata from the main page soup.

        Args:
            soup: Parsed BeautifulSoup of the book page.
            book_config: Sub-dict ``config["book"]`` with keys
                ``title_selector``, ``author_selector``, ``description_selector``.

        Returns:
            dict with ``title``, ``author`` (comma-joined), ``description``.
        """
        title_el = soup.select_one(book_config["title_selector"])
        title = title_el.get_text(strip=True) if title_el else ""

        author_els = soup.select(book_config["author_selector"])
        author = ", ".join(el.get_text(strip=True) for el in author_els)

        description_els = soup.select(book_config["description_selector"])
        description = "\n\n".join(el.get_text(strip=True) for el in description_els)

        return {"title": title, "author": author, "description": description}

    @staticmethod
    def _get_chapter_index_pages_number(soup: BeautifulSoup, last_page_config: dict) -> int:
        """Number of pagination pages for the chapter list.

        Looks up ``last_page["selector"]`` and extracts the number via
        ``last_page["pattern"]`` on its ``last_page["attribute"]`` value.
        Falls back to 1 if not found or not parseable.
        """
        last_page_el = soup.select_one(last_page_config["selector"])

        if last_page_el:
            text = last_page_el.get(last_page_config["attribute"])
            match = re.search(last_page_config["pattern"], text)
            if match:
                try:
                    return int(float(match.group(0)))
                except ValueError:
                    return 1
        return 1

    def _get_chapter_list(self, bookUrl: str, index: int, headers: dict[str, str] | None = None) -> dict[str, str]:
        """Returns ``{chapter_title: absolute_chapter_url}`` for a pagination index.

        Builds ``{bookUrl}?{request_keyword}={index}`` and extracts links via
        ``config["chapter_list"]["chapter_info"]`` (selector + title/path attributes).
        """
        # Build paginated URL: e.g. https://.../book?page=2
        params = {self.__class__.config["chapter_list"]["request_keyword"]: index}
        query_string = urlencode(params)
        full_url = f"{bookUrl}?{query_string}"
        soup = self._get_soup(url=full_url, headers=headers)

        chapters_data = {}
        # Each element contains title and href attributes for one chapter.
        chapters_el = soup.select(self.__class__.config["chapter_list"]["chapter_info"]["selector"])

        if chapters_el:
            for el in chapters_el:
                chapter_name = el.get(self.__class__.config["chapter_list"]["chapter_info"]["title_attribute"])
                chapter_path = el.get(self.__class__.config["chapter_list"]["chapter_info"]["path_attribute"])
                # Resolve relative href against the book URL.
                full_chapter_path = urljoin(bookUrl, chapter_path)
                chapters_data[chapter_name] = full_chapter_path

        return chapters_data


# ----------------------------------------------------------------------
# Standalone search helper (not part of BaseExtractor)
# ----------------------------------------------------------------------
def search(headers, domain, keyword, site_config):
    """Search from a specified domain using the declarative search config.

    Args:
        headers (dict): Headers for the HTTP request.
        domain (str): Domain where to perform the search (e.g. "https://novelfull.com").
        keyword (str): Keyword to search for.
        site_config (dict): Config dict – expects ``search`` sub-dict with
            ``path``, ``query_key`` and ``light_novel`` selectors.

    Returns:
        list: List of dicts with keys ``title`` and ``author``.
    """
    # Build search URL and perform HTTP request.
    full_url = urljoin(domain, site_config["search"]["path"])
    params = {site_config["search"]["query_key"]: keyword}
    response = requests.get(full_url, headers=headers, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    # Each light-novel block contains title and author sub-elements.
    light_novels_els = soup.select(site_config["search"]["light_novel"]["selector"])

    res = []

    # Extract title (via attribute) and author (via text) for each result.
    for el in light_novels_els:
        title_el = el.select_one(site_config["search"]["light_novel"]["title"]["selector"])
        title = title_el.get(site_config["search"]["light_novel"]["title"]["attribute"])
        author_el = el.select_one(site_config["search"]["light_novel"]["author"]["selector"])
        author = author_el.get_text(strip=True)
        res.append({
            "title": title,
            "author": author
        })

    return res
