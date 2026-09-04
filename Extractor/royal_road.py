import requests
from bs4 import BeautifulSoup

class RoyalRoadExtractor:
        
    def is_valid_url(url):
        if 'royalroad.com' in url:
            return True
        return False
    
    # This helper fixes the main bug: when a paragraph contains <br> tags,
    # BeautifulSoup may return the text as several separate fragments instead of
    # one continuous sentence. "stripped_strings" collects all text nodes in order,
    # and joining them with a space recreates the paragraph as a single string.
    def normalize_paragraph_text(paragraph):
        return ' '.join(part.strip() for part in paragraph.stripped_strings if part.strip())

    # Extract the chapter title and content from the Royal Road page.
    # We are not returning the raw HTML paragraph objects anymore; instead we
    # convert each <p> into one clean string so the output is readable and stable.
    def character_text(self, url, headers):
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get the chapter heading.
        general_info = soup.find('div', class_='fic-header')
        chapter_title = general_info.find('h1') if general_info else None

        # Gather all story paragraphs inside the chapter content block.
        content_div = soup.find('div', class_='chapter-content')
        paragraphs = content_div.find_all('p') if content_div else []

        # IMPORTANT: join each paragraph text into a single string.
        # Before this fix, iterating through paragraph children would split text such as:
        # "bathroom <br> before <br> I woke up!"
        # into separate strings like "bathroom", "before", "I woke up!".
        cleaned_text = '\n\n'.join(self.normalize_paragraph_text(p) for p in paragraphs)

        return {
            'chapter_title': chapter_title.text.strip() if chapter_title else 'No Title Found',
            'character_text': cleaned_text if cleaned_text else 'No Content Found'
        }

    def book_text (self, url, headers):
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #Get book info
        general_info = soup.find('div', class_='fic-header')
        title = general_info.find('h1') if general_info else None
        author = general_info.find('a', class_='font-white') if general_info else None
        
        #Get all chapter links
        chapter_links = []
        
        return 
    






