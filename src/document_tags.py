"""
Document Tagging System
Manages tags for documents to enable better organization and discovery
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional
from threading import Lock
from datetime import datetime


class DocumentTagManager:
    """
    Manages document tags with persistent storage

    Features:
    - Add/remove tags to/from documents
    - Get all tags for a document
    - Get all unique tags in the system
    - Search documents by tags
    - Tag autocomplete
    - Persistent JSON storage
    """

    def __init__(self, storage_path: str = "data/document_tags.json"):
        """
        Initialize tag manager

        Args:
            storage_path: Path to JSON file for tag storage
        """
        self.storage_path = Path(storage_path)
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()

        # In-memory storage: {document_id: [tags]}
        self.document_tags: Dict[str, List[str]] = {}

        # Ensure data directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing tags
        self._load_tags()

        self.logger.info(f"✅ DocumentTagManager initialized: {self.storage_path}")

    def _load_tags(self):
        """Load tags from JSON file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.document_tags = json.load(f)
                self.logger.info(f"Loaded tags for {len(self.document_tags)} documents")
            except Exception as e:
                self.logger.error(f"Failed to load tags: {e}")
                self.document_tags = {}
        else:
            self.logger.info("No existing tag file found, starting fresh")
            self.document_tags = {}

    def _save_tags(self):
        """Save tags to JSON file"""
        try:
            with self._lock:
                with open(self.storage_path, 'w') as f:
                    json.dump(self.document_tags, f, indent=2)
            self.logger.debug(f"Saved tags for {len(self.document_tags)} documents")
        except Exception as e:
            self.logger.error(f"Failed to save tags: {e}")
            raise

    def add_tags(self, document_id: str, tags: List[str]) -> List[str]:
        """
        Add tags to a document

        Args:
            document_id: Document identifier
            tags: List of tags to add

        Returns:
            Updated list of all tags for the document
        """
        with self._lock:
            # Normalize tags (lowercase, strip whitespace)
            normalized_tags = [tag.lower().strip() for tag in tags if tag.strip()]

            # Get existing tags or create new list
            current_tags = self.document_tags.get(document_id, [])

            # Add new tags (avoid duplicates)
            for tag in normalized_tags:
                if tag not in current_tags:
                    current_tags.append(tag)

            # Update storage
            self.document_tags[document_id] = current_tags
            self._save_tags()

            self.logger.info(f"Added tags {normalized_tags} to document {document_id}")
            return current_tags

    def remove_tag(self, document_id: str, tag: str) -> List[str]:
        """
        Remove a tag from a document

        Args:
            document_id: Document identifier
            tag: Tag to remove

        Returns:
            Updated list of tags for the document
        """
        with self._lock:
            normalized_tag = tag.lower().strip()

            if document_id in self.document_tags:
                if normalized_tag in self.document_tags[document_id]:
                    self.document_tags[document_id].remove(normalized_tag)

                    # Remove document entry if no tags left
                    if not self.document_tags[document_id]:
                        del self.document_tags[document_id]

                    self._save_tags()
                    self.logger.info(f"Removed tag '{normalized_tag}' from document {document_id}")

            return self.document_tags.get(document_id, [])

    def get_tags(self, document_id: str) -> List[str]:
        """
        Get all tags for a document

        Args:
            document_id: Document identifier

        Returns:
            List of tags for the document
        """
        return self.document_tags.get(document_id, [])

    def get_all_tags(self) -> List[str]:
        """
        Get all unique tags in the system (sorted by frequency)

        Returns:
            List of all unique tags, sorted by usage count (descending)
        """
        tag_counts: Dict[str, int] = {}

        for tags in self.document_tags.values():
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort by count (descending), then alphabetically
        sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

        return [tag for tag, count in sorted_tags]

    def get_tag_stats(self) -> Dict[str, int]:
        """
        Get tag usage statistics

        Returns:
            Dictionary mapping tag names to usage counts
        """
        tag_counts: Dict[str, int] = {}

        for tags in self.document_tags.values():
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return tag_counts

    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[str]:
        """
        Find documents that have specific tags

        Args:
            tags: List of tags to search for
            match_all: If True, document must have ALL tags. If False, ANY tag matches.

        Returns:
            List of document IDs matching the criteria
        """
        normalized_tags = set(tag.lower().strip() for tag in tags)
        matching_docs = []

        for doc_id, doc_tags in self.document_tags.items():
            doc_tag_set = set(doc_tags)

            if match_all:
                # Document must have ALL searched tags
                if normalized_tags.issubset(doc_tag_set):
                    matching_docs.append(doc_id)
            else:
                # Document must have ANY of the searched tags
                if normalized_tags.intersection(doc_tag_set):
                    matching_docs.append(doc_id)

        return matching_docs

    def autocomplete_tags(self, prefix: str, limit: int = 10) -> List[str]:
        """
        Get tag suggestions for autocomplete

        Args:
            prefix: Tag prefix to search for
            limit: Maximum number of suggestions

        Returns:
            List of matching tags sorted by frequency
        """
        prefix_lower = prefix.lower().strip()
        all_tags = self.get_all_tags()  # Already sorted by frequency

        # Filter tags that start with the prefix
        matching = [tag for tag in all_tags if tag.startswith(prefix_lower)]

        return matching[:limit]

    def delete_document_tags(self, document_id: str) -> bool:
        """
        Remove all tags for a document (used when document is deleted)

        Args:
            document_id: Document identifier

        Returns:
            True if document had tags and they were deleted, False otherwise
        """
        with self._lock:
            if document_id in self.document_tags:
                del self.document_tags[document_id]
                self._save_tags()
                self.logger.info(f"Deleted all tags for document {document_id}")
                return True

        return False

    def rename_tag(self, old_tag: str, new_tag: str) -> int:
        """
        Rename a tag across all documents

        Args:
            old_tag: Current tag name
            new_tag: New tag name

        Returns:
            Number of documents affected
        """
        old_normalized = old_tag.lower().strip()
        new_normalized = new_tag.lower().strip()

        if old_normalized == new_normalized:
            return 0

        count = 0

        with self._lock:
            for doc_id, tags in self.document_tags.items():
                if old_normalized in tags:
                    # Replace old tag with new tag
                    index = tags.index(old_normalized)
                    tags[index] = new_normalized
                    count += 1

            if count > 0:
                self._save_tags()
                self.logger.info(f"Renamed tag '{old_tag}' to '{new_tag}' in {count} documents")

        return count

    def get_stats(self) -> Dict[str, any]:
        """
        Get overall tagging statistics

        Returns:
            Dictionary with statistics
        """
        tag_stats = self.get_tag_stats()

        return {
            "total_documents_with_tags": len(self.document_tags),
            "total_unique_tags": len(tag_stats),
            "total_tag_assignments": sum(tag_stats.values()),
            "most_used_tags": sorted(tag_stats.items(), key=lambda x: -x[1])[:10],
            "avg_tags_per_document": sum(tag_stats.values()) / max(len(self.document_tags), 1)
        }
