# NovelScrap

Web scraper modulare per libri/novel. Scarica i contenuti da vari siti ed li
converte in **txt**, **epub** e **xml** (l'XML ha una struttura pensata per
un'eventuale app futura).

## Struttura

```
NovelScrap/
├── extractor/               # estrazione dei contenuti (un file per sito)
│   ├── models.py            #   modello dati condiviso: Book, Chapter
│   ├── base.py              #   BaseExtractor: interfaccia comune
│   ├── dispatcher.py        #   sceglie l'estrattore giusto in base all'URL
│   └── royal_road.py        #   estrattore per Royal Road
├── converter/               # conversione nei formati di output
│   ├── common.py            #   utility condivise
│   ├── txt_converter.py     #   -> .txt
│   ├── epub_converter.py    #   -> .epub
│   └── xml_converter.py     #   -> .xml (per l'app futura)
├── main.py                  # CLI di esempio
└── requirements.txt
```

## Installazione

```bash
pip install -r requirements.txt
```

## Uso (CLI)

```bash
# siti supportati
python main.py --list

# scarica un libro e convertilo in tutti i formati (default: cartella ./output)
python main.py "https://www.royalroad.com/fiction/186557/shadows-of-a-second-life"

# solo un formato
python main.py <url> --format epub

# un singolo capitolo (URL del capitolo)
python main.py "<url-del-capitolo>"

# cartella di output personalizzata
python main.py <url> -o ./libri
```

## Uso (libreria)

```python
from extractor import fetch            # sceglie da solo l'estrattore giusto
from converter import convert_book

libro = fetch("https://www.royalroad.com/fiction/186557/shadows-of-a-second-life")
print(libro.title, libro.author, libro.chapter_count)

convert_book(libro, "txt",  out_dir="output")
convert_book(libro, "epub", out_dir="output")
convert_book(libro, "xml",  out_dir="output")
```

### Modello dati condiviso

Tutti gli estrattori restituiscono oggetti strutturati, mai dict grezzi:

- **`Book`**: `source`, `title`, `author`, `url`, `synopsis`, `chapters[]`
- **`Chapter`**: `title`, `content` (lista di paragrafi), `index`, `url`

Convertitori ed eventuale app futura lavorano sempre su questi stessi campi.

### Dispatcher

`extractor/dispatcher.py` sceglie automaticamente l'estrattore in base
all'URL. Tutti gli estrattori hanno gli **stessi nomi di metodo**:

| metodo | cosa fa |
| --- | --- |
| `is_valid_url(url)` | True se l'estrattore gestisce l'URL |
| `is_book_url(url)` / `is_chapter_url(url)` | tipo di pagina |
| `fetch_book(url)` | estrae un `Book` completo (tutti i capitoli) |
| `fetch_chapter(url)` | estrae un singolo `Chapter` |

`fetch(url)` fa da "scorciatoia": se l'URL è un capitolo restituisce un `Book`
con quel capitolo, altrimenti il `Book` completo.

## Aggiungere un nuovo sito

1. Crea un file nella cartella `extractor/` (es. `fanfiction.py`);
2. definisci una classe che estende `BaseExtractor`:

```python
from extractor.base import BaseExtractor
from extractor.models import Book, Chapter

class FanFictionExtractor(BaseExtractor):
    source = "fanfiction"

    @staticmethod
    def is_valid_url(url): ...          # True se il dominio è suo

    def fetch_book(self, url, headers=None) -> Book: ...
    def fetch_chapter(self, url, headers=None) -> Chapter: ...
```

Fatto: il dispatcher lo trova da solo (registrazione automatica), nessun altro
file va toccato. Attenzione solo a mantenere gli stessi nomi di metodo.

## Aggiungere un nuovo formato di conversione

1. Crea un modulo in `converter/` (es. `mobi_converter.py`) che esponga
   `convert(book, output_path=None, out_dir=None) -> Path`;
2. aggiungi la riga `"mobi": mobi_converter.convert` alla mappa `CONVERTERS`
   in `converter/__init__.py`.

## Note

- Royal Road mostra sulla pagina del libro solo gli ultimi capitoli
  pubblicati; per gli archivi completi dei romanzi lunghi andrà esteso
  l'estrattore con la pagina dell'indice completo.
- Usa un User-Agent "da browser" (già incluso di default in `base.py`) ed evita
  di fare troppe richieste ravvicinate per non essere bloccato.
