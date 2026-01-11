"""CLI entry points for arxiv-zotero-obsidian."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from .arxiv_client import ArxivClient
from .config import load_config
from .obsidian_writer import ObsidianWriter
from .zotero_client import ZoteroClient


def search_arxiv():
    """Search arXiv for papers."""
    parser = argparse.ArgumentParser(description="Search arXiv papers")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Max results")
    parser.add_argument(
        "--sort-by",
        choices=["relevance", "submitted_date", "last_updated"],
        default="relevance",
        help="Sort criterion",
    )
    parser.add_argument("--category", help="arXiv category filter (e.g., cs.AI)")
    parser.add_argument("--date-from", help="Filter from date (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="Filter until date (YYYY-MM-DD)")
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()
    client = ArxivClient()

    try:
        results = client.search(
            query=args.query,
            max_results=args.max_results,
            sort_by=args.sort_by,
            category=args.category,
            date_from=args.date_from,
            date_to=args.date_to,
        )
    except Exception as e:
        print(f"Error searching arXiv: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No papers found matching your query.")
        sys.exit(0)

    if args.output == "json":
        output = [r.to_dict() for r in results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\nFound {len(results)} papers:\n")
        print("=" * 70)

        for i, r in enumerate(results, 1):
            abstract = r.abstract[:200].replace("\n", " ")
            if len(r.abstract) > 200:
                abstract += "..."

            authors = r.authors[:3]
            if len(r.authors) > 3:
                authors_str = ", ".join(authors) + f" (+{len(r.authors) - 3} more)"
            else:
                authors_str = ", ".join(authors)

            print(f"[{i}] {r.title}")
            print(f"    arXiv ID  : {r.arxiv_id}")
            print(f"    Authors   : {authors_str}")
            print(f"    Published : {r.published.strftime('%Y-%m-%d')}")
            print(f"    Categories: {', '.join(r.categories)}")
            print(f"    Abstract  : {abstract}")
            print(f"    PDF       : {r.pdf_url}")
            print("-" * 70)


def add_to_zotero():
    """Add paper to Zotero."""
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

    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    if not config.zotero.api_key:
        print("Error: Zotero API key not configured.", file=sys.stderr)
        sys.exit(1)

    if not config.zotero.library_id:
        print("Error: Zotero library_id not configured.", file=sys.stderr)
        sys.exit(1)

    client = ZoteroClient(
        library_id=config.zotero.library_id,
        library_type=config.zotero.library_type,
        api_key=config.zotero.api_key,
    )

    collection_key = None
    collection_name = args.collection or config.zotero.default_collection

    if collection_name:
        try:
            collection_key = client.find_or_create_collection(collection_name)
            print(f"Using collection: {collection_name}")
        except Exception as e:
            print(f"Warning: Could not create collection: {e}", file=sys.stderr)

    authors = [a.strip() for a in args.authors.split(",") if a.strip()]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

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

    pdf_attached = False

    if not args.skip_pdf:
        print("Downloading PDF from arXiv...")
        try:
            download_dir = Path(config.arxiv.download_dir)
            download_dir.mkdir(parents=True, exist_ok=True)

            arxiv_client = ArxivClient()
            pdf_path = arxiv_client.download_pdf(args.arxiv_id, str(download_dir))
            print(f"Downloaded: {pdf_path}")

            print("Uploading PDF to Zotero...")
            pdf_attached = client.attach_pdf(item_key, pdf_path)

            if pdf_attached:
                print("PDF attached successfully")
            else:
                print("Warning: Failed to attach PDF", file=sys.stderr)
        except Exception as e:
            print(f"Warning: PDF failed: {e}", file=sys.stderr)

    result = {
        "success": True,
        "item_key": item_key,
        "collection_key": collection_key,
        "pdf_attached": pdf_attached,
    }
    print(json.dumps(result, indent=2))


def create_summary():
    """Create Obsidian paper summary."""
    parser = argparse.ArgumentParser(description="Create Obsidian paper summary")
    parser.add_argument("--arxiv-id", required=True, help="arXiv paper ID")
    parser.add_argument("--title", required=True, help="Paper title")
    parser.add_argument("--authors", required=True, help="Comma-separated authors")
    parser.add_argument("--abstract", default="", help="Paper abstract")
    parser.add_argument("--published", default="", help="Publication date")
    parser.add_argument("--zotero-key", default="", help="Zotero item key")
    parser.add_argument("--summary", default="", help="Summary")
    parser.add_argument("--key-findings", default="", help="Pipe-separated findings")
    parser.add_argument("--methodology", default="", help="Methodology")
    parser.add_argument("--tags", default="", help="Comma-separated tags")

    args = parser.parse_args()

    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    if not config.obsidian.vault_path:
        print("Error: Obsidian vault_path not configured.", file=sys.stderr)
        sys.exit(1)

    vault_path = Path(config.obsidian.vault_path)
    if not vault_path.exists():
        print(f"Error: Vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    writer = ObsidianWriter(
        vault_path=str(vault_path),
        papers_folder=config.obsidian.papers_folder,
    )

    authors = [a.strip() for a in args.authors.split(",") if a.strip()]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    key_findings = (
        [f.strip() for f in args.key_findings.split("|") if f.strip()]
        if args.key_findings
        else None
    )

    try:
        filepath = writer.create_summary(
            arxiv_id=args.arxiv_id,
            title=args.title,
            authors=authors,
            abstract=args.abstract,
            zotero_key=args.zotero_key if args.zotero_key else None,
            summary=args.summary if args.summary else None,
            key_findings=key_findings,
            methodology=args.methodology if args.methodology else None,
            tags=tags if tags else None,
            published=args.published if args.published else None,
        )
        print(f"Created: {filepath}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
