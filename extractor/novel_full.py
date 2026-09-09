from extractor.configurable import ConfigurableExtractor


class novelfullExtractor(ConfigurableExtractor):
    source ="novelfull"
    domain = "novelfull.com"
    config = {
            "search": {
                "path": "/search",
                "query_key": "keyword",
                "light_novel": {
                    #TODO path of novel
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
            "book": {
                "title_selector": "h3.title",
                "author_selector": 'div.info div > a[href^="/author/"]',
                "description_selector": "div.desc-text p"
            },
            "light_novel_title": {
                "selector": "a.truyen-title"
            },
            "chapter_title": {
                "selector": "a.chapter-title",
                "chapter_number_pattern": "\\d+"
            },
            "content": {
                "selector": "div#chapter-content p",
                #"attribute": "data-reader-original-text",
                "join": "\n"
            },
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
    delay = 0.05
