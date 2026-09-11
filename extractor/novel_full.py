"""
Novelfull extractor (https://novelfull.com).

Thin declarative subclass of ``ConfigurableExtractor`` – all logic lives in
``configurable.py``. This file only provides the site-specific ``domain``,
``config`` selectors and polite ``delay``.

The selectors below were verified against the live site (2026):
    - search              : /search?keyword=... -> div:has(> h3.truyen-title)
    - book title / author : h3.title / div.info div > a[href^="/author/"] / div.desc-text p
    - chapter title       : a.chapter-title (number via regex ``\\d+``)
    - chapter content     : div#chapter-content p
    - chapter list        : ul.list-chapter li a[title] (paginated via ?page=N, last page li.last a)

If Novelfull ever changes its layout, just update the ``config`` dict here,
without touching the rest of the program.
"""

from extractor.configurable import ConfigurableExtractor


class novelfullExtractor(ConfigurableExtractor):
    """Novelfull extractor – configurable template for novelfull.com."""

    #: Source identifier used by the dispatcher.
    source = "novelfull"
    #: Domain used by ``is_valid_url`` (ConfigurableExtractor checks substring in netloc).
    domain = "novelfull.com"
    # ------------------------------------------------------------------
    # Declarative site config (see configurable.py module docstring for schema)
    # ------------------------------------------------------------------
    config = {
            # Search page: /search?keyword={keyword}
            "search": {
                "path": "/search",
                "query_key": "keyword",
                "light_novel": {
                    "selector": "div:has(> h3.truyen-title)",
                    "title": {
                        "selector": "h3.truyen-title a[title]",
                        "attribute": "title"
                    },
                    "author" : {
                        "selector": "span.author"
                    }
                }
            },
            # Book page metadata
            "book": {
                "title_selector": "h3.title",
                "author_selector": 'div.info div > a[href^="/author/"]',
                "description_selector": "div.desc-text p"
            },
            # Unused helper selector for light-novel title links (kept for compatibility)
            "light_novel_title": {
                "selector": "a.truyen-title"
            },
            # Chapter page title + number extraction
            "chapter_title": {
                "selector": "a.chapter-title",
                "chapter_number_pattern": "\\d+"
            },
            # Chapter content paragraphs
            "content": {
                "selector": "div#chapter-content p",
                #"attribute": "data-reader-original-text",
                "join": "\n"
            },
            # Paginated chapter list
            "chapter_list": {
                "last_page": {
                    "selector": "li.last a",
                    "attribute": "href",
                    "pattern": "\\d+"
                },
                "request_keyword": "page",
                "chapter_info": {
                    "selector": "ul.list-chapter li a[title]",
                    "title_attribute": "title",
                    "path_attribute": "href"
                }
            }
        }
    #: Polite delay in seconds between chapter fetches.
    delay = 0.05
