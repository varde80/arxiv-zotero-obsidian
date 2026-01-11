#!/usr/bin/env python3
"""Add paper to Zotero script for Claude Code skill."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

# Add src to path (scripts -> zotero-add -> skills -> .claude -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import load_config
from zotero_client import ZoteroClient
from arxiv_client import ArxivClient


def main():
    parser = argparse.ArgumentParser(description="Add paper to Zotero")
    parser.add_argument("--arxiv-id", required=True, help="arXiv paper ID")
    parser.add_argument("--title", required=True, help="Paper title")
    parser.add_argument("--authors", required=True, help="Comma-separated authors")
    parser.add_argument("--abstract", default="", help="Paper abstract")
    parser.add_argument("--published", default="", help="Publication date")
    parser.add_argument("--collection", default="", help="Zotero collection name")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF download")
    parser.add_argument("--doi", default="", help="Paper DOI")

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate Zotero config
    if not config.zotero.api_key:
        print(
            "Error: Zotero API key not configured.\n"
            "Set ZOTERO_API_KEY environment variable or add to .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not config.zotero.library_id:
        print(
            "Error: Zotero library_id not configured.\n"
            "Add library_id to config/config.json",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize client
    try:
        client = ZoteroClient(
            library_id=config.zotero.library_id,
            library_type=config.zotero.library_type,
            api_key=config.zotero.api_key,
        )
    except Exception as e:
        print(f"Error connecting to Zotero: {e}", file=sys.stderr)
        sys.exit(1)

    # Find or create collection
    collection_key = None
    collection_name = args.collection or config.zotero.default_collection

    if collection_name:
        try:
            collection_key = client.find_or_create_collection(collection_name)
            print(f"Using collection: {collection_name}")
        except Exception as e:
            print(f"Warning: Could not create collection: {e}", file=sys.stderr)

    # Parse authors and tags
    authors = [a.strip() for a in args.authors.split(",") if a.strip()]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    # Create item
    try:
        item_key = client.create_paper_item(
            title=args.title,
            authors=authors,
            abstract=args.abstract,
            arxiv_id=args.arxiv_id,
            published=args.published,
            collection_key=collection_key,
            tags=tags,
            doi=args.doi if args.doi else None,
        )
        print(f"Created Zotero item: {item_key}")
    except Exception as e:
        print(f"Error creating Zotero item: {e}", file=sys.stderr)
        sys.exit(1)

    # Download and attach PDF
    pdf_attached = False
    pdf_path = None

    if not args.skip_pdf:
        print("Downloading PDF from arXiv...")
        try:
            # Use project's downloads directory for persistence
            download_dir = PROJECT_ROOT / config.arxiv.download_dir
            download_dir.mkdir(parents=True, exist_ok=True)

            arxiv_client = ArxivClient()
            pdf_path = arxiv_client.download_pdf(args.arxiv_id, str(download_dir))
            print(f"Downloaded: {pdf_path}")

            print("Uploading PDF to Zotero...")
            pdf_attached = client.attach_pdf(item_key, pdf_path)

            if pdf_attached:
                print("PDF attached successfully")
            else:
                print("Warning: Failed to attach PDF (saved locally)", file=sys.stderr)
        except Exception as e:
            print(f"Warning: PDF download/upload failed: {e}", file=sys.stderr)

    # Output result
    result = {
        "success": True,
        "item_key": item_key,
        "collection_key": collection_key,
        "collection_name": collection_name,
        "pdf_attached": pdf_attached,
        "arxiv_id": args.arxiv_id,
        "title": args.title,
    }

    print("\n" + "=" * 50)
    print("Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
