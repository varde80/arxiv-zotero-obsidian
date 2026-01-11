"""Obsidian markdown note writer for paper summaries."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class ObsidianWriter:
    """Writer for creating paper summary notes in Obsidian vault."""

    def __init__(self, vault_path: str, papers_folder: str = "Papers"):
        """Initialize the Obsidian writer.

        Args:
            vault_path: Path to the Obsidian vault.
            papers_folder: Subfolder within vault for paper notes.
        """
        self.vault_path = Path(vault_path)
        self.papers_folder = self.vault_path / papers_folder
        self.papers_folder.mkdir(parents=True, exist_ok=True)

    def slugify(self, text: str, max_length: int = 50) -> str:
        """Create URL-safe slug from text.

        Args:
            text: Text to slugify.
            max_length: Maximum length of slug.

        Returns:
            Slugified text.
        """
        # Convert to lowercase
        text = text.lower()
        # Remove special characters
        text = re.sub(r"[^\w\s-]", "", text)
        # Replace spaces with hyphens
        text = re.sub(r"[-\s]+", "-", text).strip("-")
        # Limit length
        return text[:max_length]

    def create_summary(
        self,
        arxiv_id: str,
        title: str,
        authors: List[str],
        abstract: str,
        zotero_key: Optional[str] = None,
        summary: Optional[str] = None,
        key_findings: Optional[List[str]] = None,
        methodology: Optional[str] = None,
        contributions: Optional[str] = None,
        limitations: Optional[str] = None,
        future_work: Optional[str] = None,
        personal_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        published: Optional[str] = None,
    ) -> str:
        """Create a paper summary markdown file.

        Args:
            arxiv_id: arXiv paper ID.
            title: Paper title.
            authors: List of author names.
            abstract: Paper abstract.
            zotero_key: Optional Zotero item key for linking.
            summary: Optional summary of the paper.
            key_findings: Optional list of key findings.
            methodology: Optional methodology description.
            contributions: Optional main contributions.
            limitations: Optional limitations.
            future_work: Optional future work directions.
            personal_notes: Optional personal notes.
            tags: Optional list of tags.
            published: Optional publication date.

        Returns:
            Path to the created markdown file.
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        slug = self.slugify(title)
        filename = f"{date_str}-{slug}.md"
        filepath = self.papers_folder / filename

        # Build frontmatter
        tag_list = tags or []
        authors_yaml = ", ".join(f'"{a}"' for a in authors)

        frontmatter = f"""---
title: "{self._escape_yaml(title)}"
authors: [{authors_yaml}]
arxiv_id: "{arxiv_id}"
date_added: "{date_str}"
published: "{published or ''}"
tags: [{', '.join(tag_list)}]
zotero_key: "{zotero_key or ''}"
arxiv_url: "https://arxiv.org/abs/{arxiv_id}"
pdf_url: "https://arxiv.org/pdf/{arxiv_id}"
status: "unread"
---
"""

        # Build Zotero link
        zotero_link = (
            f"[Open in Zotero](zotero://select/items/{zotero_key})"
            if zotero_key
            else "Not linked"
        )

        # Build content
        content = f"""# {title}

> [!info] Paper Overview
> - **Authors**: {', '.join(authors)}
> - **arXiv**: [{arxiv_id}](https://arxiv.org/abs/{arxiv_id})
> - **PDF**: [Download](https://arxiv.org/pdf/{arxiv_id})
> - **Zotero**: {zotero_link}
> - **Published**: {published or 'N/A'}

## Abstract

{abstract}

## Summary

{summary or '*Add your summary here*'}

## Key Findings

{self._format_list(key_findings) if key_findings else '- *Add key findings*'}

## Methodology

{methodology or '*Describe the methodology*'}

## Contributions

{contributions or '*List main contributions*'}

## Limitations & Future Work

### Limitations
{limitations or '*Identify limitations*'}

### Future Work
{future_work or '*Potential future directions*'}

## Personal Notes

{personal_notes or '*Your thoughts and insights*'}

## Related Papers

*Link to related paper notes here*

---
*Created: {date_str}*
"""

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(frontmatter + content)

        return str(filepath)

    def _format_list(self, items: Optional[List[str]]) -> str:
        """Format a list of items as markdown bullet points."""
        if not items:
            return ""
        return "\n".join(f"- {item}" for item in items)

    def _escape_yaml(self, text: str) -> str:
        """Escape special characters for YAML strings."""
        return text.replace('"', '\\"').replace("\n", " ")

    def note_exists(self, arxiv_id: str) -> Optional[str]:
        """Check if a note for the given paper already exists.

        Args:
            arxiv_id: arXiv paper ID.

        Returns:
            Path to existing note if found, None otherwise.
        """
        for note_file in self.papers_folder.glob("*.md"):
            with open(note_file, encoding="utf-8") as f:
                content = f.read(500)  # Read first 500 chars for frontmatter
                if f'arxiv_id: "{arxiv_id}"' in content:
                    return str(note_file)
        return None
