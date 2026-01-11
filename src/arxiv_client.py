"""arXiv API client for searching and downloading papers."""

import arxiv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class PaperResult:
    """Represents a paper from arXiv search results."""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    published: datetime
    updated: datetime
    pdf_url: str
    categories: List[str]
    doi: Optional[str] = None
    journal_ref: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "published": self.published.isoformat(),
            "updated": self.updated.isoformat(),
            "pdf_url": self.pdf_url,
            "categories": self.categories,
            "doi": self.doi,
            "journal_ref": self.journal_ref,
        }


class ArxivClient:
    """Client for interacting with arXiv API."""

    # Sort criteria mapping
    SORT_CRITERIA = {
        "relevance": arxiv.SortCriterion.Relevance,
        "submitted_date": arxiv.SortCriterion.SubmittedDate,
        "last_updated": arxiv.SortCriterion.LastUpdatedDate,
    }

    def __init__(self, delay_seconds: float = 3.0):
        """Initialize the arXiv client.

        Args:
            delay_seconds: Delay between API requests to respect rate limits.
        """
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=delay_seconds,
            num_retries=3,
        )

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[PaperResult]:
        """Search arXiv for papers matching the query.

        Args:
            query: Search query. Supports field prefixes:
                   ti: (title), au: (author), abs: (abstract), cat: (category)
            max_results: Maximum number of results to return.
            sort_by: Sort criterion: 'relevance', 'submitted_date', 'last_updated'.
            category: Filter by arXiv category (e.g., 'cs.AI', 'physics.cond-mat').
            date_from: Filter papers from date (YYYY-MM-DD).
            date_to: Filter papers until date (YYYY-MM-DD).

        Returns:
            List of PaperResult objects.
        """
        # Build query with category filter
        full_query = query
        if category:
            full_query = f"cat:{category} AND ({query})"

        # Add date filters if specified
        if date_from or date_to:
            date_filter = self._build_date_filter(date_from, date_to)
            if date_filter:
                full_query = f"({full_query}) AND {date_filter}"

        # Get sort criterion
        sort_criterion = self.SORT_CRITERIA.get(sort_by, arxiv.SortCriterion.Relevance)

        search = arxiv.Search(
            query=full_query,
            max_results=max_results,
            sort_by=sort_criterion,
        )

        results = []
        for result in self.client.results(search):
            results.append(
                PaperResult(
                    arxiv_id=result.get_short_id(),
                    title=result.title,
                    authors=[author.name for author in result.authors],
                    abstract=result.summary,
                    published=result.published,
                    updated=result.updated,
                    pdf_url=result.pdf_url,
                    categories=result.categories,
                    doi=result.doi,
                    journal_ref=result.journal_ref,
                )
            )

        return results

    def download_pdf(
        self,
        arxiv_id: str,
        download_dir: str,
        filename: Optional[str] = None,
    ) -> str:
        """Download PDF for a paper.

        Args:
            arxiv_id: arXiv paper ID (e.g., '2401.12345').
            download_dir: Directory to save the PDF.
            filename: Optional custom filename. If not provided,
                      uses arxiv_id with .pdf extension.

        Returns:
            Path to the downloaded PDF file.
        """
        # Ensure download directory exists
        dir_path = Path(download_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Search for the paper by ID
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(self.client.results(search))

        # Generate filename
        if filename is None:
            filename = f"{arxiv_id.replace('/', '_')}.pdf"

        # Download the PDF
        paper.download_pdf(dirpath=str(dir_path), filename=filename)

        return str(dir_path / filename)

    def get_paper(self, arxiv_id: str) -> Optional[PaperResult]:
        """Get details for a specific paper by ID.

        Args:
            arxiv_id: arXiv paper ID.

        Returns:
            PaperResult if found, None otherwise.
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            return PaperResult(
                arxiv_id=result.get_short_id(),
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                published=result.published,
                updated=result.updated,
                pdf_url=result.pdf_url,
                categories=result.categories,
                doi=result.doi,
                journal_ref=result.journal_ref,
            )
        except StopIteration:
            return None

    def _build_date_filter(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> Optional[str]:
        """Build date filter string for arXiv query.

        Args:
            date_from: Start date (YYYY-MM-DD).
            date_to: End date (YYYY-MM-DD).

        Returns:
            Date filter string or None.
        """
        # arXiv uses submittedDate field for date filtering
        # Format: submittedDate:[YYYYMMDD TO YYYYMMDD]
        if not date_from and not date_to:
            return None

        from_str = date_from.replace("-", "") if date_from else "*"
        to_str = date_to.replace("-", "") if date_to else "*"

        return f"submittedDate:[{from_str} TO {to_str}]"
