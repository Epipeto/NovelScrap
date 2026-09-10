import time
from urllib.parse import urljoin, urlparse
import re, requests
from extractor.base import BaseExtractor
from extractor.models import Book, Chapter
from bs4 import NavigableString, BeautifulSoup
import json

class NovelBuddy(BaseExtractor):
    source = "novelbuddy"
    delay: int = 0.05

    @staticmethod
    def is_valid_url(url: str) -> bool:
        return urlparse(url).hostname.lower() == "novelbuddy.me"
    
    def fetch_chapter(self, url: str, headers: dict[str, str] | None = None) -> Chapter:
        soup = self._get_soup(url=url, headers=headers)

        script_tag = soup.find("script", id="__NEXT_DATA__")

        if not script_tag and not script_tag.string:
            return
    
        data = json.loads(script_tag.string.strip())
        
        chapter_title = data["props"]["pageProps"]["initialChapter"]["name"]

        chapter_content_el = BeautifulSoup(data["props"]["pageProps"]["initialChapter"]["content"], "html.parser")
        chapter_content = [p.text.strip() for p in chapter_content_el.find_all("p") if p.text.strip()]

        chapter_index = data["props"]["pageProps"]["initialChapter"]["number"]

        #chapter_el = soup.select_one("div.novel-tts-content div div")
        #chapter_title = next(
        #    (child.strip() for child in chapter_el.children if isinstance(child, NavigableString) and child.strip()),
        #    ""
        #)
#
        #match = re.search(r"\d+", chapter_title)
        #chapter_index = int(match.group(0)) if match else 0
#
        #chapter_content = [p.text.strip() for p in chapter_el.find_all("p") if p.text.strip()]

        return Chapter(title=chapter_title, content=chapter_content, index=chapter_index, url=url)

    def fetch_book(self, url: str, headers: dict[str, str] | None = None) -> Book:
        soup = self._get_soup(url=url, headers=headers)

        script_tag = soup.find("script", id="__NEXT_DATA__")

        if not script_tag and not script_tag.string:
            return
        
        data = json.loads(script_tag.string.strip())
        
        book = Book(
            source= "novelbuddy.me",
            title= data["props"]["pageProps"]["initialManga"]["name"],
            author= ", ".join(aut["name"] for aut in data["props"]["pageProps"]["initialManga"]["authors"]),
            synopsis= data["props"]["pageProps"]["initialManga"]["summary"],
            url=url
        )

        book_id = data["props"]["pageProps"]["initialManga"]["id"]
        api_url = data["props"]["pageProps"]["siteConfig"]["apiUrl"]
        chapter_list__api_url = f"{api_url}/titles/{book_id}/chapters"

        response = requests.get(chapter_list__api_url)
        all_chapter = response.json()
        #print(all_chapter["data"]["chapters"])

        for chapter_data in reversed(all_chapter["data"]["chapters"]):
            chapter_url = urljoin(url, chapter_data["url"])
            chapter = self.fetch_chapter(url=chapter_url, headers=headers)

            book.chapters.append(chapter)
            time.sleep(self.__class__.delay)

        return book

        
    
#https://novelbuddy.me/supreme-daily-login-system
