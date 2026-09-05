"""
DISPATCHER: given an URL, automatically chooses the right extractor.

Usage:
    from extractor import fetch, fetch_book, fetch_chapter

    # Get extractor for a specific URL
    >>> cls = get_extracto("https://royalroad.com/fiction/12345/my-book")
    >>> print(cls.source)  # e.g. "royalroad"
    

    # Automatic fetching: get the info for the book
    >>> book = fetch("https://royalroad.com/fiction/12345/my-book")
    >>> print(book.title, len(book.chapters))  # e.g. "My Book 10"
    
For adding a new site extractor, just create a new file in this folder with a class 
that extends BaseExtractor (e.g. class FanFictionExtractor): the dispatcher will find it automatically, 
no manual registration is needed.

All extractors expose the same method names (see base.py):
    fetch_book(url)     -> complete Book
    fetch_chapter(url)  -> single Chapter
"""

from __future__ import annotations

import importlib
import inspect 
import pkgutil

from extractor.base import BaseExtractor
from extractor.models import Book, Chapter

#: Internal modules of the package that are NOT extractors to register.
_NON_EXTRACTOR_MODULES = {"base", "dispatcher", "models", "__init__"}

_registry: dict[str, type[BaseExtractor]] | None = None

class UnsupportedUrlError(ValueError):
    """Raised when no extractor can handle the provided URL."""
    
def extractors() -> dict[str, type[BaseExtractor]]:
    """Dictionary {source_name: extractor_class} of all extractors.

    The first call scans the `extractor` folder automatically;
    results are then cached.
    """
    global _registry
    if _registry is None:
        _registry = _discover()
    return _registry
                          
                          
def _discover() -> dict[str, type[BaseExtractor]]:
    """Scans the package folder and collects extractor classes."""
    import extractor  # local import to avoid circular dependencies

    found: dict[str, type[BaseExtractor]] = {}
    for module_info in pkgutil.iter_modules(extractor.__path__):
        if module_info.name in _NON_EXTRACTOR_MODULES:
            continue
        module = importlib.import_module(f"{extractor.__name__}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseExtractor)
                and obj is not BaseExtractor
                and not inspect.isabstract(obj)
                and obj.source not in found
            ):
                found[obj.source] = obj
    return found

def get_extractor(url: str) -> type[BaseExtractor]:
    """Returns the EXTRACTOR CLASS capable of handling `url`.

    Raises UnsupportedUrlError if no extractor can handle the URL.
    """
    url = (url or "").strip()
    for cls in extractors().values():
        if cls.is_valid_url(url):
            return cls
    raise UnsupportedUrlError(
        f"No extractor can handle this URL: {url!r} "
        f"(available sources: {', '.join(sorted(extractors())) or 'none'})"
    )
    
def fetch_book(url: str, headers: dict[str, str] | None = None) -> Book:
    """Extracts a complete book from the URL of its main page."""
    extractor_cls = get_extractor(url)
    return extractor_cls().fetch_book(url, headers)


def fetch_chapter(url: str, headers: dict[str, str] | None = None) -> Chapter:
    """Extracts a single chapter from the URL of the chapter."""
    extractor_cls = get_extractor(url)
    return extractor_cls().fetch_chapter(url, headers)


def fetch(url: str, headers: dict[str, str] | None = None) -> Book:
    """Extraction "automatic" based on the type of URL.
    
    - Chapter URL  -> returns a Book with that single chapter
    - Book page URL -> returns the complete Book
    """
    extractor_cls = get_extractor(url)
    if extractor_cls.is_chapter_url(url):
        chapter = extractor_cls().fetch_chapter(url, headers)
        if chapter.index == 0:
            chapter.index = 1
        return Book(
            source=extractor_cls.source,
            title=chapter.title,
            author="",
            url=url,
            synopsis="",
            chapters=[chapter],
        )
    return extractor_cls().fetch_book(url, headers) 