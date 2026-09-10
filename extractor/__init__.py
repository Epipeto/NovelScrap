"""
Package `extractor`: collects the extractors for the various book sites.

Recommended entry point: `extractor.dispatcher`, which automatically picks
the right extractor based on the URL.

Every file in this package (except models.py, base.py and dispatcher.py)
must contain a class extending BaseExtractor to register a new site.
Existing example: royal_road.py -> RoyalRoadExtractor.
"""
#from extractor.novelbuddy import NovelBuddy


from extractor.models import Book, Chapter
from extractor.base import BaseExtractor
from extractor.dispatcher import (
    UnsupportedUrlError,
    extractors,
    fetch,
    fetch_book,
    fetch_chapter,
    get_extractor,
)

__all__ = [
    "Book",
    "Chapter",
    "BaseExtractor",
    "extractors",
    "fetch",
    "fetch_book",
    "fetch_chapter",
    "get_extractor",
    "UnsupportedUrlError",
]
