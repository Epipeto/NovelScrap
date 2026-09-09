"""
Models for the extractor and the converter

All the extractors return the same models, so the dispatcher can use them without knowing which site we are on.
So the converter can use the same models to convert them to different formats (epub, mobi, pdf, etc.)
    
Logical structure:
    Book                       -> a complete book
      .title                   ->    book title
      .author                  ->    author
      .source                  ->    source site (e.g. "royalroad")
      .url                     ->    URL from which it was extracted
      .synopsis                ->    description (if found)
      .chapters: list[Chapter] ->    all chapters, in order

    Chapter                    -> a single chapter
      .title                   ->    chapter title
      .content: list[str]      ->    content: ONE element = ONE paragraph
      .index                   ->    position in the book (1 = first)
      .url                     ->    chapter URL
"""

from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class Chapter:
    """A single chapter"""
    
    title: str
    #Content organized as a list of paragraphs (one element = one paragraph)
    content: list[str] = field(default_factory=list)
    #Index (1 = first chapter; 0 = unknown)
    index: int = 0
    #URL of the chapter page (when available)
    url: str = ""
    
    """Can be used to get the content as a single text, with paragraphs separated by an empty line."""
    @property
    def text(self) -> str:
        """Content as a single text: paragraphs are separated by an empty line."""
        return "\n\n".join(self.content)
    
@dataclass 
class Book:
    """A complete book (novel) with all chapters in order."""
    
    #Site of origin (identifies the extractor that created it)
    source: str
    title: str
    author: str
    url: str
    #Sinopsis / description of the book, if available
    synopsis: str
    chapters: list[Chapter] = field(default_factory=list)
    
    @property
    def chapter_count(self) -> int:
        """Number of extracted chapters."""
        return len(self.chapters)
    
    def add_chapter(
        self,
        title: str = "",
        content: list[str] | None = None,
        url: str = "",
    ) -> Chapter:
        """Creates a chapter, assigns it the next index and adds it to the book."""
        chapter = Chapter(
            title=title,
            content=content if content is not None else [],
            index=len(self.chapters) + 1,
            url=url,
        )
        self.chapters.append(chapter)
        return chapter