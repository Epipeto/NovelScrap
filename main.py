"""
Example CLI for NovelScrap.

Given a URL, it automatically picks the right extractor (dispatcher),
extracts the book and converts it into the requested formats (txt, epub,
xml).

Usage examples (from the project folder):

    # list the supported sites
    python main.py --list

    # extract a book and convert it into all formats (default)
    python main.py "https://www.royalroad.com/fiction/186557/shadows-of-a-second-life"

    # extract a single chapter and save it only as epub
    python main.py "https://www.royalroad.com/fiction/186557/.../chapter/3817130/..." --format epub

    # choose the output folder
    python main.py <url> --out ./books
"""

from __future__ import annotations

import argparse
import sys

from converter import convert_book, supported_formats
from extractor import extractors, fetch


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="novelscrap",
        description="Scarica un libro da un sito supportato e lo converte in txt/epub/xml.",
    )
    parser.add_argument("url", nargs="?", help="URL del libro o del capitolo da scaricare")
    parser.add_argument(
        "-f", "--format",
        choices=supported_formats() + ["all"],
        default="all",
        help="Formato di output (default: all = tutti i formati)",
    )
    parser.add_argument(
        "-o", "--out", default="output",
        help="Cartella dove salvare i file (default: ./output)",
    )
    parser.add_argument(
        "-l", "--list", action="store_true",
        help="Elenca i siti (estrattori) disponibili ed esce",
    )
    return parser.parse_args()


def _list_extractors() -> None:
    print("Siti supportati:")
    for source in sorted(extractors()):
        print(f"  - {source}")
    print("Formati di output:", ", ".join(supported_formats()))


def _run(url: str, fmt: str, out_dir: str) -> None:
    print(f"Scarico: {url}")
    try:
        book = fetch(url)
    except Exception as exc:  # noqa: BLE001 - we want a "friendly" error
        print(f"Errore durante l'estrazione: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"  Titolo : {book.title or '(sconosciuto)'}")
    print(f"  Autore : {book.author or '(sconosciuto)'}")
    print(f"  Fonte  : {book.source}")
    print(f"  Capitoli estratti: {book.chapter_count}")

    if book.chapter_count == 0:
        print("Nessun capitolo estratto: controllo l'URL e riprovo.", file=sys.stderr)
        sys.exit(1)

    formats = supported_formats() if fmt == "all" else [fmt]
    for name in formats:
        try:
            path = convert_book(book, name, out_dir=out_dir)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! conversione {name} fallita: {exc}", file=sys.stderr)
        else:
            print(f"  Salvato [{name}]: {path}")


def main() -> None:
    args = _parse_args()
    if args.list or not args.url:
        _list_extractors()
        return
    _run(args.url, args.format, args.out)


if __name__ == "__main__":
    main()
