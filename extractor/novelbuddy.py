"""
NovelBuddy extractor (https://novelbuddy.me).

The site renders book and chapter data inside a JSON blob
``<script id="__NEXT_DATA__">`` (Next.js):
    - book metadata : props.pageProps.initialManga { name, authors[], summary, id }
    - chapter data  : props.pageProps.initialChapter { name, number, content (HTML) }
    - api base URL  : props.pageProps.siteConfig.apiUrl
    - chapter content HTML -> <p> paragraphs (parsed with BeautifulSoup)
    - chapter list via API: {apiUrl}/titles/{book_id}/chapters -> data.chapters[] { url }

If NovelBuddy changes its JSON layout or API path, update the selectors/keys
in this file without touching the rest of the program.
"""

import time
from urllib.parse import urljoin, urlparse
import re
import requests
from extractor.base import BaseExtractor
from extractor.models import Book, Chapter
from bs4 import NavigableString, BeautifulSoup
import json


class NovelBuddy(BaseExtractor):
    """NovelBuddy extractor (JSON via ``__NEXT_DATA__`` + chapters API)."""

    #: Source identifier used by the dispatcher.
    source = "novelbuddy"
    #: Polite delay in seconds between chapter fetches.
    delay: int = 0.05

    # ------------------------------------------------------------------
    # URL recognition
    # ------------------------------------------------------------------
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """True if this extractor can handle the given URL."""
        return urlparse(url).hostname.lower() == "novelbuddy.me"

    # is_chapter_url is inherited from BaseExtractor:
    # default check is ``"chapter" in path.lower()`` (base.py).

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
        """Downloads and returns the single chapter at the given URL.

        Procedure:
          1. download the chapter page and locate ``<script id="__NEXT_DATA__">``;
          2. parse its JSON – ``props.pageProps.initialChapter`` holds
             ``name``, ``number`` and ``content`` (HTML string);
          3. parse the HTML fragment and return ``<p>`` paragraphs.
        """
        soup = self._get_soup(url=url, headers=headers)

        # NovelBuddy embeds all data in a Next.js JSON blob.
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if not script_tag and not script_tag.string:
            return

        data = json.loads(script_tag.string.strip())

        # Title and index from the JSON payload.
        chapter_title = data["props"]["pageProps"]["initialChapter"]["name"]

        # Content is an HTML string – parse it and extract <p> texts.
        chapter_content_el = BeautifulSoup(data["props"]["pageProps"]["initialChapter"]["content"], "html.parser")
        chapter_content = [p.text.strip() for p in chapter_content_el.find_all("p") if p.text.strip()]

        chapter_index = data["props"]["pageProps"]["initialChapter"]["number"]

        return Chapter(title=chapter_title, content=chapter_content, index=chapter_index, url=url)

    def fetch_book(self, url: str, headers: dict[str, str] | None = None) -> Book:
        """Given the URL of the book page, returns the COMPLETE Book.

        Procedure:
          1. download the book page -> ``__NEXT_DATA__`` JSON;
          2. extract book metadata via ``props.pageProps.initialManga``
             (name, authors[], summary) and IDs/URLs
             (initialManga.id, siteConfig.apiUrl);
          3. call ``{apiUrl}/titles/{book_id}/chapters`` to get the full
             chapter list (``data.chapters``);
          4. for each chapter (reversed to go oldest -> newest), download
             the chapter page via ``fetch_chapter``.
        """
        soup = self._get_soup(url=url, headers=headers)

        # Same JSON blob as in fetch_chapter, but for the book page.
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if not script_tag and not script_tag.string:
            return

        data = json.loads(script_tag.string.strip())

        # Build Book from manga metadata in the JSON.
        book = Book(
            source="novelbuddy.me",
            title=data["props"]["pageProps"]["initialManga"]["name"],
            author=", ".join(aut["name"] for aut in data["props"]["pageProps"]["initialManga"]["authors"]),
            synopsis=data["props"]["pageProps"]["initialManga"]["summary"],
            url=url
        )

        # Resolve API URL for the full chapter list.
        book_id = data["props"]["pageProps"]["initialManga"]["id"]
        api_url = data["props"]["pageProps"]["siteConfig"]["apiUrl"]
        chapter_list__api_url = f"{api_url}/titles/{book_id}/chapters"

        response = requests.get(chapter_list__api_url)
        all_chapter = response.json()

        # API returns newest first – reverse to iterate in reading order.
        for chapter_data in reversed(all_chapter["data"]["chapters"]):
            # chapter url is relative – resolve against the book page URL.
            chapter_url = urljoin(url, chapter_data["url"])
            chapter = self.fetch_chapter(url=chapter_url, headers=headers)

            book.chapters.append(chapter)
            # Polite delay between chapter requests.
            time.sleep(self.__class__.delay)

        return book
