"""
Document Version Control System
Tracks document versions, enables rollback, and version comparison
"""

import sqlite3
import hashlib
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DocumentVersion:
    """Document version metadata"""
    version_id: int
    document_id: str
    version_number: int
    file_path: str
    file_name: str
    file_size: int
    file_hash: str
    uploaded_by: Optional[str]
    upload_timestamp: str
    is_current: bool
    chunks_count: int
    metadata: Optional[Dict[str, Any]] = None
    change_description: Optional[str] = None


class DocumentVersionManager:
    """Manages document versions with SQLite persistence"""

    def __init__(self, db_path: str = "data/document_versions.db", storage_path: str = "data/document_versions"):
        self.db_path = Path(db_path)
        self.storage_path = Path(storage_path)
        self._init_database()
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure version storage directory exists"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """Initialize database schema"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create document_versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                uploaded_by TEXT,
                upload_timestamp TEXT NOT NULL,
                is_current BOOLEAN NOT NULL DEFAULT 0,
                chunks_count INTEGER DEFAULT 0,
                metadata TEXT,
                change_description TEXT,
                UNIQUE(document_id, version_number)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_document_id ON document_versions(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_current ON document_versions(is_current)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_upload_timestamp ON document_versions(upload_timestamp)")

        conn.commit()
        conn.close()

        logger.info(f"✅ Document version database initialized: {self.db_path}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def create_version(
        self,
        document_id: str,
        file_path: str,
        file_name: str,
        file_size: int,
        uploaded_by: Optional[str] = None,
        chunks_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        change_description: Optional[str] = None
    ) -> DocumentVersion:
        """Create a new version of a document"""

        # Calculate file hash
        file_hash = self._calculate_file_hash(Path(file_path))

        # Get next version number
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(version_number) FROM document_versions WHERE document_id = ?
        """, (document_id,))
        result = cursor.fetchone()
        next_version = (result[0] or 0) + 1

        # Store file in version storage
        version_file_name = f"{document_id}_v{next_version}_{Path(file_name).name}"
        version_file_path = self.storage_path / version_file_name
        shutil.copy2(file_path, version_file_path)

        # Mark all previous versions as not current
        cursor.execute("""
            UPDATE document_versions SET is_current = 0 WHERE document_id = ?
        """, (document_id,))

        # Insert new version
        upload_timestamp = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO document_versions (
                document_id, version_number, file_path, file_name, file_size,
                file_hash, uploaded_by, upload_timestamp, is_current, chunks_count,
                metadata, change_description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            document_id, next_version, str(version_file_path), file_name, file_size,
            file_hash, uploaded_by, upload_timestamp, chunks_count,
            json.dumps(metadata) if metadata else None,
            change_description
        ))

        version_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ Created version {next_version} for document {document_id}")

        return DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            version_number=next_version,
            file_path=str(version_file_path),
            file_name=file_name,
            file_size=file_size,
            file_hash=file_hash,
            uploaded_by=uploaded_by,
            upload_timestamp=upload_timestamp,
            is_current=True,
            chunks_count=chunks_count,
            metadata=metadata,
            change_description=change_description
        )

    def get_versions(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions of a document"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM document_versions
            WHERE document_id = ?
            ORDER BY version_number DESC
        """, (document_id,))

        versions = []
        for row in cursor.fetchall():
            versions.append(DocumentVersion(
                version_id=row['version_id'],
                document_id=row['document_id'],
                version_number=row['version_number'],
                file_path=row['file_path'],
                file_name=row['file_name'],
                file_size=row['file_size'],
                file_hash=row['file_hash'],
                uploaded_by=row['uploaded_by'],
                upload_timestamp=row['upload_timestamp'],
                is_current=bool(row['is_current']),
                chunks_count=row['chunks_count'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None,
                change_description=row['change_description']
            ))

        conn.close()
        return versions

    def get_version(self, document_id: str, version_number: int) -> Optional[DocumentVersion]:
        """Get specific version of a document"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM document_versions
            WHERE document_id = ? AND version_number = ?
        """, (document_id, version_number))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DocumentVersion(
            version_id=row['version_id'],
            document_id=row['document_id'],
            version_number=row['version_number'],
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_size=row['file_size'],
            file_hash=row['file_hash'],
            uploaded_by=row['uploaded_by'],
            upload_timestamp=row['upload_timestamp'],
            is_current=bool(row['is_current']),
            chunks_count=row['chunks_count'],
            metadata=json.loads(row['metadata']) if row['metadata'] else None,
            change_description=row['change_description']
        )

    def get_current_version(self, document_id: str) -> Optional[DocumentVersion]:
        """Get current version of a document"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM document_versions
            WHERE document_id = ? AND is_current = 1
        """, (document_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return DocumentVersion(
            version_id=row['version_id'],
            document_id=row['document_id'],
            version_number=row['version_number'],
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_size=row['file_size'],
            file_hash=row['file_hash'],
            uploaded_by=row['uploaded_by'],
            upload_timestamp=row['upload_timestamp'],
            is_current=bool(row['is_current']),
            chunks_count=row['chunks_count'],
            metadata=json.loads(row['metadata']) if row['metadata'] else None,
            change_description=row['change_description']
        )

    def revert_to_version(self, document_id: str, version_number: int, reverted_by: Optional[str] = None) -> DocumentVersion:
        """Revert document to a specific version by creating a new version from it"""
        # Get the version to revert to
        old_version = self.get_version(document_id, version_number)
        if not old_version:
            raise ValueError(f"Version {version_number} not found for document {document_id}")

        # Create new version from old version file
        change_description = f"Reverted to version {version_number}"
        if reverted_by:
            change_description += f" by {reverted_by}"

        return self.create_version(
            document_id=document_id,
            file_path=old_version.file_path,
            file_name=old_version.file_name,
            file_size=old_version.file_size,
            uploaded_by=reverted_by,
            chunks_count=old_version.chunks_count,
            metadata=old_version.metadata,
            change_description=change_description
        )

    def delete_version(self, document_id: str, version_number: int) -> bool:
        """Delete a specific version (cannot delete current version)"""
        version = self.get_version(document_id, version_number)
        if not version:
            return False

        if version.is_current:
            raise ValueError("Cannot delete the current version")

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM document_versions
            WHERE document_id = ? AND version_number = ?
        """, (document_id, version_number))

        conn.commit()
        conn.close()

        # Delete file from storage
        try:
            Path(version.file_path).unlink()
        except Exception as e:
            logger.warning(f"Failed to delete version file: {e}")

        logger.info(f"✅ Deleted version {version_number} of document {document_id}")
        return True

    def get_version_count(self, document_id: str) -> int:
        """Get total number of versions for a document"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM document_versions WHERE document_id = ?
        """, (document_id,))

        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_all_documents_with_versions(self) -> List[Dict[str, Any]]:
        """Get all documents with their version information"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                document_id,
                COUNT(*) as version_count,
                MAX(version_number) as latest_version,
                MAX(upload_timestamp) as last_updated
            FROM document_versions
            GROUP BY document_id
            ORDER BY last_updated DESC
        """)

        documents = []
        for row in cursor.fetchall():
            documents.append({
                'document_id': row['document_id'],
                'version_count': row['version_count'],
                'latest_version': row['latest_version'],
                'last_updated': row['last_updated']
            })

        conn.close()
        return documents


# Global instance
_version_manager_instance: Optional[DocumentVersionManager] = None


def set_version_manager(manager: DocumentVersionManager):
    """Set global version manager instance"""
    global _version_manager_instance
    _version_manager_instance = manager


def get_version_manager() -> Optional[DocumentVersionManager]:
    """Get global version manager instance"""
    return _version_manager_instance
