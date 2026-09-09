from extractor.base import BaseExtractor
from extractor.models import Book, Chapter

import requests, re, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlencode

class ConfigurableExtractor(BaseExtractor):

    domain: str = ""
    config: dict = {}
    delay: int = 0.5

    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Verifica se il dominio dell'URL corrisponde a quello della classe."""
        if not cls.domain:
            return False
        return cls.domain in urlparse(url).netloc.lower()
    

    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
         # Get the html page
        soup = self._get_soup(url=url, headers=headers)

        # Extract light novel title
        #title_element = soup.select_one(self.__class__.config["light_novel_title"]["selector"])
        #title = None
        #if title_element:
        #    title = title_element.text

        # Extract light chapter title
        chapter_title_el = soup.select_one(self.__class__.config["chapter_title"]["selector"])
        chapter_title = None
        if chapter_title_el:
            chapter_title = chapter_title_el.get_text(strip=True)

        #Extract index
        pattern = self.__class__.config["chapter_title"].get("chapter_number_pattern")
        if pattern and chapter_title:
            match = re.search(pattern, chapter_title)
            chapter_index = int(float(match.group(0))) if match else 0

        # Extract light chapter content
        chapter_content_els = soup.select(self.__class__.config["content"]["selector"])
        chapter_content = []

        attr_name = self.__class__.config["content"].get("attribute")
        if attr_name:
            chapter_content = [el.get(attr_name) for el in chapter_content_els if el.get(attr_name)]
        else:
            chapter_content = [el.get_text(strip=True) for el in chapter_content_els]

        return Chapter(title=chapter_title, content=chapter_content, index=chapter_index, url=url)
    

    def fetch_book(self, url: str, headers: dict[str, str] | None = None) -> Book:
        soup = self._get_soup(url=url, headers=headers)
        last_page_n = self._get_chapter_index_pages_number(soup=soup, last_page_config=self.__class__.config["chapter_list"]["last_page"])
        
        book_metadata = self._get_ln_metadata(soup=soup, book_config=self.__class__.config["book"])

        book = Book(
            source= self.domain,
            title= book_metadata["title"],
            author= book_metadata["author"],
            synopsis= book_metadata["description"],
            url=url
        )

        # index for fallback
        index = 0
        for page_n in range(1, last_page_n+1):
            chapter_list = self._get_chapter_list(bookUrl= url, index=page_n, headers=headers)
            for chapter_title, chapter_url in chapter_list.items():
                index += 1
                try:
                    chapter = self.fetch_chapter(chapter_url, headers)
                except Exception:
                    # A chapter that does not respond must not block the whole book:
                    # we still record it in the table of contents, with empty content.
                    chapter = Chapter(title=chapter_title, content=[], index=index, url=chapter_url)

                book.chapters.append(chapter)

                time.sleep(self.__class__.delay)
        
        return book
        
    @staticmethod
    def _get_ln_metadata(soup: BeautifulSoup, book_config: dict) -> dict:
        title_el = soup.select_one(book_config["title_selector"])
        title = title_el.get_text(strip=True) if title_el else ""

        author_els = soup.select(book_config["author_selector"])
        author = ", ".join(el.get_text(strip=True) for el in author_els)

        description_els = soup.select(book_config["description_selector"])
        description = "\n\n".join(el.get_text(strip=True) for el in description_els)

        return {"title": title, "author": author, "description": description}


    @staticmethod
    def _get_chapter_index_pages_number(soup: BeautifulSoup, last_page_config: dict) -> int:
        last_page_el = soup.select_one(last_page_config["selector"])

        if last_page_el:
            text = last_page_el.get(last_page_config["attribute"])
            match = re.search(last_page_config["pattern"], text)
            if match:
                try:
                    return int(float(match.group(0)))
                except ValueError:
                    return -1
        return -1

    def _get_chapter_list(self, bookUrl: str, index: int, headers: dict[str, str] | None = None) -> dict[str, str]:
        params = {self.__class__.config["chapter_list"]["request_keyword"]: index}
        query_string = urlencode(params)
        full_url = f"{bookUrl}?{query_string}"
        soup = self._get_soup(url=full_url, headers=headers)

        chapters_data = {}
        chapters_el = soup.select(self.__class__.config["chapter_list"]["chapter_info"]["selector"])

        if chapters_el:
            for el in chapters_el:
                chapter_name = el.get(self.__class__.config["chapter_list"]["chapter_info"]["title_attribute"])
                chapter_path = el.get(self.__class__.config["chapter_list"]["chapter_info"]["path_attribute"])
                full_chapter_path = urljoin(bookUrl, chapter_path)
                chapters_data[chapter_name] = full_chapter_path
        
        return chapters_data



def search(headers, domain, keyword, site_config):
    """Search from a specified domain

    Args:
        headers (dict): Headers for the http request
        domain (str): Domain where to perform the search
        keyword (str): Keyword to search for
        site_config (dic): Dictionary used as config to request and parse results correctly.

    Returns:
        list: List of dictionaries with keys 'title' and 'author'
    """

    # HTTP request
    full_url = urljoin(domain, site_config["search"]["path"])
    params = {site_config["search"]["query_key"]: keyword}
    response = requests.get(full_url, headers=headers, params=params)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract parent element with necessary info
    light_novels_els = soup.select(site_config["search"]["light_novel"]["selector"])

    res = []

    # Extract title and author
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



    