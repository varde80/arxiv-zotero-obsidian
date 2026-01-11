"""Zotero API client for managing papers in Zotero library."""

from pathlib import Path
from typing import List, Optional

from pyzotero import zotero


class ZoteroClient:
    """Client for interacting with Zotero Web API."""

    def __init__(
        self,
        library_id: str,
        library_type: str,
        api_key: str,
    ):
        """Initialize the Zotero client.

        Args:
            library_id: Zotero library ID (user ID or group ID).
            library_type: 'user' or 'group'.
            api_key: Zotero API key.
        """
        self.zot = zotero.Zotero(library_id, library_type, api_key)
        self._collection_cache: dict = {}

    def find_or_create_collection(self, name: str) -> str:
        """Find a collection by name or create it if it doesn't exist.

        Args:
            name: Collection name.

        Returns:
            Collection key.
        """
        # Check cache first
        if name in self._collection_cache:
            return self._collection_cache[name]

        # Search existing collections
        collections = self.zot.collections()
        for col in collections:
            if col["data"]["name"] == name:
                self._collection_cache[name] = col["data"]["key"]
                return col["data"]["key"]

        # Create new collection
        result = self.zot.create_collections([{"name": name}])

        if "successful" in result and result["successful"]:
            first_key = next(iter(result["successful"]))
            key = result["successful"][first_key]["key"]
            self._collection_cache[name] = key
            return key
        else:
            raise Exception(f"Failed to create collection: {result}")

    def create_paper_item(
        self,
        title: str,
        authors: List[str],
        abstract: str,
        arxiv_id: str,
        published: str,
        collection_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        doi: Optional[str] = None,
    ) -> str:
        """Create a journal article item in Zotero.

        Args:
            title: Paper title.
            authors: List of author names.
            abstract: Paper abstract.
            arxiv_id: arXiv paper ID.
            published: Publication date (ISO format).
            collection_key: Optional collection key to add item to.
            tags: Optional list of tags.
            doi: Optional DOI.

        Returns:
            Item key of the created item.
        """
        # Get template for journal article
        template = self.zot.item_template("journalArticle")

        # Fill in metadata
        template["title"] = title
        template["abstractNote"] = abstract
        template["url"] = f"https://arxiv.org/abs/{arxiv_id}"
        template["extra"] = f"arXiv:{arxiv_id}"
        template["date"] = published
        template["publicationTitle"] = "arXiv preprint"

        if doi:
            template["DOI"] = doi

        # Set creators (authors)
        template["creators"] = [
            {"creatorType": "author", "name": author} for author in authors
        ]

        # Set collection
        if collection_key:
            template["collections"] = [collection_key]

        # Set tags
        if tags:
            template["tags"] = [{"tag": t} for t in tags]

        # Create the item
        result = self.zot.create_items([template])

        # Handle response - pyzotero returns dict with 'successful', 'failed', etc.
        if "successful" in result and result["successful"]:
            # Get the first successful item key
            first_key = next(iter(result["successful"]))
            return result["successful"][first_key]["key"]
        elif "failed" in result and result["failed"]:
            first_key = next(iter(result["failed"]))
            error_msg = result["failed"][first_key].get("message", "Unknown error")
            raise Exception(f"Zotero API error: {error_msg}")
        else:
            raise Exception(f"Unexpected Zotero response: {result}")

    def attach_pdf(self, item_key: str, pdf_path: str) -> bool:
        """Attach a PDF file to an item.

        Args:
            item_key: Parent item key.
            pdf_path: Path to the PDF file.

        Returns:
            True if successful, False otherwise.
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"PDF file not found: {pdf_path}")
            return False

        try:
            # Use attachment_both for better compatibility
            result = self.zot.attachment_both(
                [str(pdf_file)],
                parentid=item_key
            )
            return True
        except Exception as e:
            # Try alternative method: create linked file attachment
            try:
                template = self.zot.item_template("attachment", "linked_file")
                template["title"] = pdf_file.name
                template["path"] = str(pdf_file)
                template["contentType"] = "application/pdf"
                template["parentItem"] = item_key
                self.zot.create_items([template])
                return True
            except Exception as e2:
                print(f"PDF attachment failed: {e}, {e2}")
                return False

    def get_item(self, item_key: str) -> Optional[dict]:
        """Get an item by its key.

        Args:
            item_key: Item key.

        Returns:
            Item data dict or None if not found.
        """
        try:
            return self.zot.item(item_key)
        except Exception:
            return None

    def list_collections(self) -> List[dict]:
        """List all collections in the library.

        Returns:
            List of collection data dicts.
        """
        return self.zot.collections()

    def search_items(self, query: str) -> List[dict]:
        """Search items in the library.

        Args:
            query: Search query.

        Returns:
            List of matching items.
        """
        return self.zot.items(q=query)
