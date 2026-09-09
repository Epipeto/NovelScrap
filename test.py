from converter import convert_book, supported_formats
from extractor import extractors, fetch, ConfigurableExtractor

class novelfullExtractor(ConfigurableExtractor):
    domain = "https://novelfull.com"
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
            
            "light_novel_title": {
                "selector": "a.truyen-title"
            },
            "chapter_title": {
                "selector": "a.chapter-title",
                "chapter_number_pattern": "\\d+"
            },
            "content": {
                "selector": "p[data-reader-original-text]",
                "attribute": "data-reader-original-text",
                "join": "\n"
            }
        }

if __name__ == "__main__":

    config = {
        "https://novelfull.com": {
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
            
            "light_novel_title": {
                "selector": "a.truyen-title"
            },
            "chapter_title": {
                "selector": "a.chapter-title",
                "chapter_number_pattern": "\\d+"
            },
            "content": {
                "selector": "p[data-reader-original-text]",
                "attribute": "data-reader-original-text",
                "join": "\n"
            }
        }
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    #search_res = search(headers, "https://novelfull.com", "Reincarnated", config["https://novelfull.com"])
    #for res in search_res:
    #    print(f"Title : {res["title"]}\nAuthor: {res["author"]}\n")
    
    #url = "https://novelfull.com/reborn-space-intelligent-woman/chapter-2786-experiments-related-to-cultivators.html"
    #title, chapter_title, chapter_content = extract_content(headers, url, config["https://novelfull.com"])

    #print(f"NOVEL TITLE: {title}")
    #print("---------------------------------")
    #print(f"CHAPTER TITLE: {chapter_title}")
    #print(chapter_content)

    url = "https://novelfull.com/reborn-space-intelligent-woman/chapter-2786-experiments-related-to-cultivators.html"
    nf = novelfullExtractor()
    print(nf.fetch_chapter(url, headers))

    