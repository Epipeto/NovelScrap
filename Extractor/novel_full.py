import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_content(headers, url, site_config):
    """ Extract content from the url

    Args:
        headers (dict): Headers for the http request
        url (str): URL of the site to extract content from
        site_config (dict): Dictionary used to correctly select each field of the paragraph

    Returns:
        str, str, str: Return in following order: title of the light novel, chapter title, chapter content
    """

    # Get the html page
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract light novel title
    title_element = soup.select_one(site_config["light_novel_title"]["selector"])
    title = None
    if title_element:
        title = title_element.text

    # Extract light chapter title
    chapter_title_el = soup.select_one(site_config["chapter_title"]["selector"])
    chapter_title = None
    if chapter_title_el:
        chapter_title = chapter_title_el.text

    # Extract light chapter content
    chapter_content_els = soup.select(site_config["content"]["selector"])
    chapter_content = None
    if chapter_content_els:
        chapter_content = site_config["content"]["join"].join([el.get(site_config["content"]["attribute"]) for el in chapter_content_els])

    return title, chapter_title, chapter_content


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
                    "selector": "div:has(> h3.truyen-title)",
                    "title": {
                        "selector": "h3.truyen-title a[title]",
                        "attribute": "title"
                    },
                    "author" : {
                        "selector": "span.author",
                    }
                }
            },
            
            "light_novel_title": {
                "selector": "a.truyen-title"
            },
            "chapter_title": {
                "selector": "a.chapter-title"
            },
            "content": {
                "selector": "p[data-reader-original-text]",
                "attribute": "data-reader-original-text",
                "join": "\n"
            }
        }
    }

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    #url = "https://novelfull.com/reborn-space-intelligent-woman/chapter-2786-experiments-related-to-cultivators.html"
    #title, chapter_title, chapter_content = extract_content(headers, url, config["https://novelfull.com"])

    #print(f"NOVEL TITLE: {title}")
    #print("---------------------------------")
    #print(f"CHAPTER TITLE: {chapter_title}")
    #print(chapter_content)
    search_res = search(headers, "https://novelfull.com", "Reincarnated", config["https://novelfull.com"])
    for res in search_res:
        print(f"Title : {res["title"]}\nAuthor: {res["author"]}\n")
    