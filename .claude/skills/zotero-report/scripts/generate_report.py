#!/usr/bin/env python3
"""Collect data from a Zotero collection for report generation."""

import argparse
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# scripts -> zotero-report -> skills -> .claude -> project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import load_config
from zotero_client import ZoteroClient

# Import pdf_extractor from same directory
sys.path.insert(0, str(Path(__file__).parent))
from pdf_extractor import extract_text_from_pdf


def extract_arxiv_id(item: dict) -> str:
    """Extract arXiv ID from a Zotero item."""
    extra = item.get("data", {}).get("extra", "")
    for line in extra.split("\n"):
        if line.startswith("arXiv:"):
            return line.replace("arXiv:", "").strip()
    url = item.get("data", {}).get("url", "")
    if "arxiv.org/abs/" in url:
        return url.split("arxiv.org/abs/")[-1].split("?")[0]
    return ""


def extract_authors(item: dict) -> list[str]:
    """Extract author names from a Zotero item."""
    creators = item.get("data", {}).get("creators", [])
    authors = []
    for c in creators:
        if c.get("creatorType") == "author":
            name = c.get("name", "")
            if not name:
                first = c.get("firstName", "")
                last = c.get("lastName", "")
                name = f"{first} {last}".strip()
            if name:
                authors.append(name)
    return authors


def generate_search_queries(papers: list[dict], max_queries: int = 5) -> list[dict]:
    """Generate suggested search queries from existing papers."""
    from collections import Counter

    words = Counter()
    categories = Counter()

    for paper in papers:
        title = paper.get("title", "")
        for word in title.lower().split():
            if len(word) > 4:
                words[word] += 1

        for tag in paper.get("tags", []):
            words[tag.lower()] += 1

    top_words = [w for w, _ in words.most_common(20)]
    queries = []

    # Group top words into queries of 2-3 terms
    for i in range(0, min(len(top_words), max_queries * 3), 3):
        chunk = top_words[i : i + 3]
        if chunk:
            queries.append(
                {
                    "query": " ".join(chunk),
                    "source": f"derived from frequent terms in collection",
                    "category": None,
                }
            )
        if len(queries) >= max_queries:
            break

    return queries


def process_collection(
    client: ZoteroClient,
    collection_key: str,
    collection_name: str,
    max_papers: int = 50,
    skip_pdf: bool = False,
    include_full_text: bool = False,
    max_chars_per_paper: int = 10000,
    mode: str = "collection",
    language: str = "ko",
) -> dict:
    """Process a Zotero collection and return structured data."""
    items = client.get_collection_items(collection_key)
    items = items[:max_papers]

    papers = []
    total_chars = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        for item in items:
            data = item.get("data", {})

            if data.get("itemType") in ("attachment", "note"):
                continue

            paper = {
                "key": data.get("key", ""),
                "title": data.get("title", ""),
                "authors": extract_authors(item),
                "date": data.get("date", ""),
                "abstract": data.get("abstractNote", ""),
                "tags": [t.get("tag", "") for t in data.get("tags", [])],
                "url": data.get("url", ""),
                "doi": data.get("DOI", ""),
                "arxiv_id": extract_arxiv_id(item),
                "has_pdf": False,
                "pdf_text_preview": "",
                "full_text": None,
                "full_text_truncated": False,
            }

            if not skip_pdf:
                try:
                    children = client.get_item_children(data.get("key", ""))
                    for child in children:
                        child_data = child.get("data", {})
                        if child_data.get("contentType") == "application/pdf":
                            pdf_path = client.download_attachment(
                                child_data.get("key", ""),
                                tmp_dir,
                                item_data=child,
                            )
                            if pdf_path:
                                paper["has_pdf"] = True
                                text = extract_text_from_pdf(pdf_path)
                                if text:
                                    paper["pdf_text_preview"] = text[:2000]
                                    if include_full_text:
                                        truncated = text[:max_chars_per_paper]
                                        paper["full_text"] = truncated
                                        paper["full_text_truncated"] = (
                                            len(text) > max_chars_per_paper
                                        )
                                        total_chars += len(truncated)
                            break
                except Exception as e:
                    print(
                        f"PDF processing failed for {paper['title']}: {e}",
                        file=sys.stderr,
                    )

            papers.append(paper)

    result = {
        "mode": mode,
        "language": language,
        "collection_name": collection_name,
        "collection_key": collection_key,
        "total_items": len(papers),
        "generated_at": datetime.now().isoformat(),
        "warnings": [],
        "papers": papers,
    }

    if include_full_text:
        result["warnings"].append(
            f"Full text included: ~{total_chars:,} chars total. "
            f"Consider reducing --max-papers or --max-chars-per-paper "
            f"if context window issues occur."
        )
        print(
            f"Warning: Full text total ~{total_chars:,} chars",
            file=sys.stderr,
        )

    if mode == "extend":
        result["suggested_search_queries"] = generate_search_queries(papers)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect Zotero collection data for report generation"
    )
    parser.add_argument(
        "--mode",
        default="collection",
        choices=["collection", "extend", "topic"],
        help="Start mode (default: collection)",
    )
    parser.add_argument("--collection", help="Zotero collection name")
    parser.add_argument("--collection-key", help="Zotero collection key")
    parser.add_argument("--topic", help="Topic keywords (mode=topic)")
    parser.add_argument(
        "--max-papers", type=int, default=50, help="Max papers (default: 50)"
    )
    parser.add_argument(
        "--skip-pdf", action="store_true", help="Skip PDF download/extraction"
    )
    parser.add_argument(
        "--include-full-text",
        action="store_true",
        help="Include full PDF text in output",
    )
    parser.add_argument(
        "--max-chars-per-paper",
        type=int,
        default=10000,
        help="Max chars per paper for full text (default: 10000)",
    )
    parser.add_argument(
        "--language",
        default="ko",
        choices=["ko", "en"],
        help="Report language (default: ko)",
    )

    args = parser.parse_args()

    if args.mode == "topic":
        print(
            "Mode 'topic' requires Claude to first run arxiv-search and "
            "zotero-add. Then re-run with --mode collection.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.collection and not args.collection_key:
        print("Error: --collection or --collection-key required", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    client = ZoteroClient(
        library_id=config.zotero.library_id,
        library_type=config.zotero.library_type,
        api_key=config.zotero.api_key,
    )

    collection_key = args.collection_key
    collection_name = args.collection or ""

    if not collection_key and args.collection:
        collection_key = client.get_collection_key_by_name(args.collection)
        if not collection_key:
            print(
                f"Error: Collection '{args.collection}' not found",
                file=sys.stderr,
            )
            sys.exit(1)

    result = process_collection(
        client=client,
        collection_key=collection_key,
        collection_name=collection_name,
        max_papers=args.max_papers,
        skip_pdf=args.skip_pdf,
        include_full_text=args.include_full_text,
        max_chars_per_paper=args.max_chars_per_paper,
        mode=args.mode,
        language=args.language,
    )

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
