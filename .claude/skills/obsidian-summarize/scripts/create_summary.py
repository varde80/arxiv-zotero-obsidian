#!/usr/bin/env python3
"""Create Obsidian summary script for Claude Code skill."""

import argparse
import sys
from pathlib import Path

# Add src to path (scripts -> obsidian-summarize -> skills -> .claude -> project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import load_config
from obsidian_writer import ObsidianWriter


def main():
    parser = argparse.ArgumentParser(description="Create Obsidian paper summary")
    parser.add_argument("--arxiv-id", required=True, help="arXiv paper ID")
    parser.add_argument("--title", required=True, help="Paper title")
    parser.add_argument("--authors", required=True, help="Comma-separated authors")
    parser.add_argument("--abstract", default="", help="Paper abstract")
    parser.add_argument("--published", default="", help="Publication date")
    parser.add_argument("--zotero-key", default="", help="Zotero item key")
    parser.add_argument("--summary", default="", help="Your summary of the paper")
    parser.add_argument(
        "--key-findings", default="", help="Pipe-separated key findings"
    )
    parser.add_argument("--methodology", default="", help="Methodology description")
    parser.add_argument("--contributions", default="", help="Main contributions")
    parser.add_argument("--limitations", default="", help="Paper limitations")
    parser.add_argument("--future-work", default="", help="Future work directions")
    parser.add_argument("--personal-notes", default="", help="Your personal notes")
    parser.add_argument("--tags", default="", help="Comma-separated tags")

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate Obsidian config
    if not config.obsidian.vault_path:
        print(
            "Error: Obsidian vault_path not configured.\n"
            "Add vault_path to config/config.json",
            file=sys.stderr,
        )
        sys.exit(1)

    vault_path = Path(config.obsidian.vault_path)
    if not vault_path.exists():
        print(
            f"Error: Obsidian vault not found at: {vault_path}\n"
            "Check vault_path in config/config.json",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize writer
    writer = ObsidianWriter(
        vault_path=str(vault_path),
        papers_folder=config.obsidian.papers_folder,
    )

    # Check if note already exists
    existing = writer.note_exists(args.arxiv_id)
    if existing:
        print(f"Note already exists: {existing}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    # Parse list fields
    authors = [a.strip() for a in args.authors.split(",") if a.strip()]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    key_findings = (
        [f.strip() for f in args.key_findings.split("|") if f.strip()]
        if args.key_findings
        else None
    )

    # Create summary
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
            contributions=args.contributions if args.contributions else None,
            limitations=args.limitations if args.limitations else None,
            future_work=args.future_work if args.future_work else None,
            personal_notes=args.personal_notes if args.personal_notes else None,
            tags=tags if tags else None,
            published=args.published if args.published else None,
        )

        print(f"\nCreated summary note:")
        print(f"  Path: {filepath}")
        print(f"  Title: {args.title}")
        print(f"  arXiv: {args.arxiv_id}")
        if args.zotero_key:
            print(f"  Zotero: {args.zotero_key}")

    except Exception as e:
        print(f"Error creating summary: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
