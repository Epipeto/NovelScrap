"""
Base class for all extractors

All extrators have the same name of the method, so the dispatcher can
call them without knowing which site we are on.

Public methods common to all extractors:
    is_valid_url(url)  (static)  -> True if this extractor can handle the URL
    is_book_url(url)   (class)   -> True if the URL points to the book page
    is_chapter_url(url)(class)   -> True if the URL points to a single chapter
    fetch_book(url, headers)     -> extracts a COMPLETE Book (all chapters)
    fetch_chapter(url, headers)  -> extracts a single Chapter
    
For adding a new site extractor, just subclass this class and implement the abstract methods.
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from extractor.models import Book, Chapter

## User-Agent used by default if the caller does not provide one.
## Some sites block requests without a "browser" User-Agent.
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

class BaseExtractor(ABC):
    """Common interface for all site extractors."""
    
    #Short name of the site handed (e.g. "royalroad"): identifies the extractor.
    source: str = "unknown"
    
    # ------------------------------------------------------------------
    # URL recognition
    # ------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def is_valid_url(url: str) -> bool:
        """True if this extractor can handle the given URL."""
        
    @classmethod
    def is_chapter_url(cls, url: str) -> bool:
        """True if the URL points to a single chapter (not to the book page).
        
        Default implementation: checks if "chapter" appears in the path.
        Individual extractors can override it with more precise rules.
        """
        path = urlparse(url).path.lower()
        return "chapter" in path
    
    @classmethod
    def is_book_url(cls, url: str) -> bool:
        """True if the URL points to the main book page."""
        return bool(cls.is_valid_url(url) and not cls.is_chapter_url(url))
    
    # ------------------------------------------------------------------
    # Content extraction (same names for all extractors)
    # ------------------------------------------------------------------
    @abstractmethod
    def fetch_book(self, url: str, headers: dict[str, str] | None = None) -> Book:
        """Given the URL of the book page, returns the complete Book."""
        
    @abstractmethod
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
        """Given the URL of a single chapter, returns the Chapter."""
        
    #------------------------------------------------------------------
    # Internal utility methods (not part of the public interface)
    #------------------------------------------------------------------
    
    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        """Returns the headers to use for the request.
        
        If the caller provides a `headers` dict, it is used as-is.
        Otherwise, the default headers (with User-Agent) are returned.
        """
        return headers if headers is not None else dict(DEFAULT_HEADERS)
    
    def _get_soup(self, url: str, headers: dict[str, str] | None = None) -> BeautifulSoup:
        """Downloads the page at the given URL and returns a BeautifulSoup object."""
        response = requests.get(url, headers=self._headers(headers))
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")