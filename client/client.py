#!/usr/bin/env python3
"""Command line client for the bible API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List

import requests

DEFAULT_SERVER_URL = "http://api:4567"


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(description="Bible API CLI")
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER_URL,
        help=f"Base URL of the Bible API server (default: {DEFAULT_SERVER_URL})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verse = subparsers.add_parser("verse", help="Fetch verse or passage")
    verse.add_argument("reference", help="Bible reference, e.g. 'John 3:16'")
    verse.add_argument("--translation", "-t", help="Translation ID")

    subparsers.add_parser("translations", help="List translations")

    books = subparsers.add_parser("books", help="List books for a translation")
    books.add_argument(
        "--translation",
        "-t",
        default="web",
        help="Translation ID (default: web)",
    )

    chapters = subparsers.add_parser(
        "chapters", help="List chapters for a book in a translation"
    )
    chapters.add_argument("book", help="Book ID (e.g. JHN)")
    chapters.add_argument(
        "--translation",
        "-t",
        default="web",
        help="Translation ID (default: web)",
    )

    random = subparsers.add_parser("random", help="Get a random verse")
    group = random.add_mutually_exclusive_group()
    group.add_argument("--books", help="Comma-separated list of book IDs")
    group.add_argument(
        "--testament", choices=["OT", "NT"], help="Limit to Old or New Testament"
    )

    return parser


def request_json(url: str) -> Any:
    """Perform HTTP GET and return JSON data."""
    response = requests.get(url)
    if not response.ok:
        print(f"Error: HTTP {response.status_code}", file=sys.stderr)
        sys.exit(1)
    return response.json()


def main(argv: List[str] | None = None) -> Any:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    base = args.server.rstrip("/")

    if args.command == "verse":
        ref = args.reference.replace(" ", "+")
        url = f"{base}/{ref}"
        if args.translation:
            url += f"?translation={args.translation}"
        data = request_json(url)
    elif args.command == "translations":
        url = f"{base}/data"
        data = request_json(url)
    elif args.command == "books":
        url = f"{base}/data/{args.translation}"
        data = request_json(url)
    elif args.command == "chapters":
        url = f"{base}/data/{args.translation}/{args.book}"
        data = request_json(url)
    elif args.command == "random":
        url = f"{base}/data/web/random"
        if args.books:
            url += f"/{args.books}"
        elif args.testament:
            url += f"/{args.testament}"
        data = request_json(url)
    else:
        parser.error("Unknown command")

    print(json.dumps(data, indent=2))
    return data


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
