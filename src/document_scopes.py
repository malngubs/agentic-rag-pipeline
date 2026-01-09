#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                       DOCUMENT SCOPES MODULE                                 ║
║                                                                              ║
║  PURPOSE:                                                                    ║
║  Manages document access scopes within a tenant. Documents can be:          ║
║  - COMPANY: Uploaded by admins, accessible to all tenant employees          ║
║  - PERSONAL: Uploaded by users, accessible only to that user                ║
║                                                                              ║
║  ACCESS MODEL:                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                        TENANT BOUNDARY                              │    ║
║  │                                                                     │    ║
║  │   ┌─────────────────────────────────────────────────────────┐      │    ║
║  │   │              COMPANY DOCUMENTS                          │      │    ║
║  │   │              (scope = "company")                        │      │    ║
║  │   │                                                         │      │    ║
║  │   │   • Uploaded by: Tenant Admins only                    │      │    ║
║  │   │   • Visible to: ALL tenant employees                   │      │    ║
║  │   │   • Stored in: Qdrant (permanent)                      │      │    ║
║  │   │   • Examples: Policies, procedures, company docs       │      │    ║
║  │   └─────────────────────────────────────────────────────────┘      │    ║
║  │                                                                     │    ║
║  │   ┌─────────────────────────────────────────────────────────┐      │    ║
║  │   │              PERSONAL DOCUMENTS                         │      │    ║
║  │   │              (scope = "personal")                       │      │    ║
║  │   │                                                         │      │    ║
║  │   │   ┌──────────┐  ┌──────────┐  ┌──────────┐             │      │    ║
║  │   │   │  User A  │  │  User B  │  │  User C  │             │      │    ║
║  │   │   │ My docs  │  │ My docs  │  │ My docs  │             │      │    ║
║  │   │   │ (only A) │  │ (only B) │  │ (only C) │             │      │    ║
║  │   │   └──────────┘  └──────────┘  └──────────┘             │      │    ║
║  │   └─────────────────────────────────────────────────────────┘      │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  USAGE:                                                                      ║
║  1. Import: from document_scopes import DocumentScopeManager                ║
║  2. Use with RAG system to filter documents during retrieval                ║
║                                                                              ║
║  INTEGRATES WITH:                                                            ║
║  - tenant_manager.py (tenant context)                                       ║
║  - rag_components.py (document processing)                                  ║
║  - auth.py (user context for personal docs)                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import sqlite3
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class DocumentScope(str, Enum):
    """
    Document visibility scope within a tenant.
    
    COMPANY: Visible to all tenant users (admin-uploaded)
    PERSONAL: Visible only to the uploading user
    """
    COMPANY = "company"
    PERSONAL = "personal"


class DocumentStatus(str, Enum):
    """
    Document processing status in the RAG pipeline.
    """
    PENDING = "pending"        # Uploaded, not yet processed
    PROCESSING = "processing"  # Currently being chunked/embedded
    READY = "ready"            # Processed and searchable
    FAILED = "failed"          # Processing failed
    ARCHIVED = "archived"      # Soft deleted, not searchable


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ScopedDocument:
    """
    Represents a document with scope information.
    
    Attributes:
        id: Unique document identifier (UUID)
        tenant_id: Owning tenant
        user_id: Uploading user (required for personal scope)
        filename: Original filename
        scope: Visibility scope (company/personal)
        status: Processing status
        file_path: Path to stored file on disk
        file_size: Size in bytes
        file_type: MIME type or extension
        chunk_count: Number of vector chunks created
        metadata: Additional document metadata
        created_at: Upload timestamp
        updated_at: Last modification timestamp
        processed_at: When processing completed
        tags: Document tags for categorization
        description: Optional description
    """
    id: str
    tenant_id: str
    user_id: Optional[str]
    filename: str
    scope: DocumentScope
    status: DocumentStatus = DocumentStatus.PENDING
    file_path: Optional[str] = None
    file_size: int = 0
    file_type: str = ""
    chunk_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    processed_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    @property
    def is_company_doc(self) -> bool:
        """Check if this is a company-wide document."""
        return self.scope == DocumentScope.COMPANY
    
    @property
    def is_personal_doc(self) -> bool:
        """Check if this is a personal document."""
        return self.scope == DocumentScope.PERSONAL
    
    @property
    def is_searchable(self) -> bool:
        """Check if document is ready for search."""
        return self.status == DocumentStatus.READY
    
    def can_access(self, user_id: str, is_admin: bool = False) -> bool:
        """
        Check if a user can access this document.
        
        Args:
            user_id: User attempting access
            is_admin: Whether user is a tenant admin
            
        Returns:
            True if access allowed
            
        Rules:
        - Admins can access everything in their tenant
        - Company docs are accessible to all tenant users
        - Personal docs only accessible to owner
        """
        # Admins can access everything in their tenant
        if is_admin:
            return True
        
        # Company docs are accessible to all tenant users
        if self.is_company_doc:
            return True
        
        # Personal docs only accessible to owner
        return self.user_id == user_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "scope": self.scope.value,
            "status": self.status.value,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_at": self.processed_at,
            "tags": self.tags,
            "description": self.description,
            "is_searchable": self.is_searchable,
            "is_company_doc": self.is_company_doc,
        }


@dataclass
class DocumentAccessFilter:
    """
    Filter for document queries based on user access rights.
    
    Use this when querying Qdrant to ensure proper access control.
    The filter ensures users only see documents they're allowed to access.
    """
    tenant_id: str
    user_id: str
    is_admin: bool = False
    include_company: bool = True
    include_personal: bool = True
    
    def to_qdrant_filter(self) -> Dict[str, Any]:
        """
        Generate Qdrant filter conditions.
        
        Returns a filter that matches:
        - All company documents (if include_company)
        - Only user's personal documents (if include_personal)
        
        Example output:
        {
            "must": [
                {"key": "tenant_id", "match": {"value": "tenant-123"}},
                {"should": [
                    {"key": "scope", "match": {"value": "company"}},
                    {"must": [
                        {"key": "scope", "match": {"value": "personal"}},
                        {"key": "user_id", "match": {"value": "user-456"}}
                    ]}
                ]}
            ]
        }
        """
        conditions = []
        
        # Always filter by tenant (critical for multi-tenant isolation!)
        conditions.append({
            "key": "tenant_id",
            "match": {"value": self.tenant_id}
        })
        
        # Build scope conditions
        scope_conditions = []
        
        if self.include_company:
            scope_conditions.append({
                "key": "scope",
                "match": {"value": DocumentScope.COMPANY.value}
            })
        
        if self.include_personal:
            # Personal docs: scope=personal AND user_id matches
            scope_conditions.append({
                "must": [
                    {"key": "scope", "match": {"value": DocumentScope.PERSONAL.value}},
                    {"key": "user_id", "match": {"value": self.user_id}}
                ]
            })
        
        if scope_conditions:
            if len(scope_conditions) == 1:
                conditions.append(scope_conditions[0])
            else:
                conditions.append({"should": scope_conditions})
        
        return {"must": conditions}
    
    def to_simple_filter(self) -> Dict[str, Any]:
        """
        Generate a simpler filter for basic Qdrant queries.
        
        Use this if the complex nested filter doesn't work with your Qdrant setup.
        """
        return {
            "must": [
                {"key": "tenant_id", "match": {"value": self.tenant_id}}
            ]
        }


# =============================================================================
# DOCUMENT SCOPE MANAGER
# =============================================================================

class DocumentScopeManager:
    """
    Manages document scoping and access control.
    
    Responsibilities:
    - Track document metadata and scope
    - Enforce access control rules
    - Generate filters for RAG queries
    - Manage document lifecycle
    
    Example:
        manager = DocumentScopeManager(db_path="data/document_scopes.db")
        
        # Register new document (call BEFORE processing)
        doc = await manager.register_document(
            tenant_id="tenant-123",
            user_id="user-456",
            filename="policy.pdf",
            scope=DocumentScope.COMPANY,
            file_path="/uploads/policy.pdf",
            file_size=1024
        )
        
        # After RAG processing completes
        await manager.update_document_status(
            doc.id, 
            status=DocumentStatus.READY,
            chunk_count=15
        )
        
        # Get accessible documents for user
        docs = await manager.get_accessible_documents(
            tenant_id="tenant-123",
            user_id="user-456"
        )
    """
    
    def __init__(self, db_path: str = "data/document_scopes.db"):
        """
        Initialize the document scope manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info(f"✅ DocumentScopeManager initialized: {self.db_path}")
    
    # =========================================================================
    # DATABASE INITIALIZATION
    # =========================================================================
    
    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scoped_documents (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT,
                    filename TEXT NOT NULL,
                    scope TEXT NOT NULL DEFAULT 'personal',
                    status TEXT NOT NULL DEFAULT 'pending',
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    processed_at TEXT,
                    tags TEXT DEFAULT '[]',
                    description TEXT DEFAULT ''
                )
            """)
            
            # Indexes for efficient querying
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_tenant 
                ON scoped_documents(tenant_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_user 
                ON scoped_documents(tenant_id, user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_scope 
                ON scoped_documents(tenant_id, scope)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_docs_status 
                ON scoped_documents(status)
            """)
            
            conn.commit()
    
    # =========================================================================
    # DOCUMENT REGISTRATION
    # =========================================================================
    
    async def register_document(
        self,
        tenant_id: str,
        user_id: Optional[str],
        filename: str,
        scope: DocumentScope,
        file_path: Optional[str] = None,
        file_size: int = 0,
        file_type: str = "",
        tags: Optional[List[str]] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScopedDocument:
        """
        Register a new document in the system.
        
        Call this BEFORE processing the document with RAG.
        The returned document ID should be stored in Qdrant metadata.
        
        Args:
            tenant_id: Tenant owning the document
            user_id: User uploading (required for personal scope)
            filename: Original filename
            scope: Visibility scope (company/personal)
            file_path: Path to stored file
            file_size: File size in bytes
            file_type: MIME type or extension
            tags: Categorization tags
            description: Document description
            metadata: Additional metadata
            
        Returns:
            ScopedDocument object with generated ID
            
        Raises:
            ValueError: If personal scope without user_id
            
        Example:
            doc = await manager.register_document(
                tenant_id="tenant-123",
                user_id="user-456",
                filename="report.pdf",
                scope=DocumentScope.PERSONAL,
                file_size=2048
            )
            
            # Use doc.id when storing in Qdrant
            qdrant_metadata = {
                "doc_id": doc.id,
                "tenant_id": doc.tenant_id,
                "user_id": doc.user_id,
                "scope": doc.scope.value,
                "filename": doc.filename
            }
        """
        # Validate: personal docs require user_id
        if scope == DocumentScope.PERSONAL and not user_id:
            raise ValueError("Personal documents require a user_id")
        
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        doc = ScopedDocument(
            id=doc_id,
            tenant_id=tenant_id,
            user_id=user_id,
            filename=filename,
            scope=scope,
            status=DocumentStatus.PENDING,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            tags=tags or [],
            description=description
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scoped_documents (
                    id, tenant_id, user_id, filename, scope, status,
                    file_path, file_size, file_type, chunk_count,
                    metadata, created_at, updated_at, tags, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.id, doc.tenant_id, doc.user_id, doc.filename,
                doc.scope.value, doc.status.value,
                doc.file_path, doc.file_size, doc.file_type, doc.chunk_count,
                json.dumps(doc.metadata), doc.created_at, doc.updated_at,
                json.dumps(doc.tags), doc.description
            ))
            conn.commit()
        
        logger.info(
            f"📄 Registered document: {filename} "
            f"(scope={scope.value}, tenant={tenant_id}, doc_id={doc_id})"
        )
        return doc
    
    async def update_document_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        chunk_count: int = 0,
        error_message: Optional[str] = None
    ) -> Optional[ScopedDocument]:
        """
        Update document processing status.
        
        Call this after RAG processing completes (successfully or not).
        
        Args:
            doc_id: Document to update
            status: New status (READY, FAILED, etc.)
            chunk_count: Number of chunks created (if successful)
            error_message: Error details (if failed)
            
        Returns:
            Updated document or None if not found
            
        Example:
            # After successful processing
            await manager.update_document_status(
                doc.id,
                status=DocumentStatus.READY,
                chunk_count=15
            )
            
            # After failed processing
            await manager.update_document_status(
                doc.id,
                status=DocumentStatus.FAILED,
                error_message="PDF parsing error"
            )
        """
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status == DocumentStatus.READY:
                cursor.execute("""
                    UPDATE scoped_documents
                    SET status = ?, chunk_count = ?, updated_at = ?, processed_at = ?
                    WHERE id = ?
                """, (status.value, chunk_count, now, now, doc_id))
            elif status == DocumentStatus.FAILED:
                # Store error in metadata
                cursor.execute("SELECT metadata FROM scoped_documents WHERE id = ?", (doc_id,))
                row = cursor.fetchone()
                metadata = json.loads(row[0]) if row and row[0] else {}
                metadata["error"] = error_message or "Unknown error"
                
                cursor.execute("""
                    UPDATE scoped_documents
                    SET status = ?, updated_at = ?, metadata = ?
                    WHERE id = ?
                """, (status.value, now, json.dumps(metadata), doc_id))
            else:
                cursor.execute("""
                    UPDATE scoped_documents
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (status.value, now, doc_id))
            
            conn.commit()
        
        return await self.get_document(doc_id)
    
    # =========================================================================
    # DOCUMENT RETRIEVAL
    # =========================================================================
    
    async def get_document(self, doc_id: str) -> Optional[ScopedDocument]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            ScopedDocument or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM scoped_documents WHERE id = ?",
                (doc_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_document(row)
    
    async def get_accessible_documents(
        self,
        tenant_id: str,
        user_id: str,
        is_admin: bool = False,
        scope: Optional[DocumentScope] = None,
        status: Optional[DocumentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScopedDocument]:
        """
        Get all documents accessible to a user.
        
        This is the PRIMARY query method for listing documents.
        It enforces access control automatically.
        
        Args:
            tenant_id: Tenant context
            user_id: User making request
            is_admin: Whether user is admin (can see all docs)
            scope: Filter by scope (optional)
            status: Filter by status (optional)
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of accessible ScopedDocument objects
            
        Example:
            # Regular user - sees company docs + their personal docs
            docs = await manager.get_accessible_documents(
                tenant_id="tenant-123",
                user_id="user-456"
            )
            
            # Admin - sees all docs in tenant
            docs = await manager.get_accessible_documents(
                tenant_id="tenant-123",
                user_id="admin-001",
                is_admin=True
            )
            
            # Only company docs
            docs = await manager.get_accessible_documents(
                tenant_id="tenant-123",
                user_id="user-456",
                scope=DocumentScope.COMPANY
            )
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query with access control
            query = """
                SELECT * FROM scoped_documents
                WHERE tenant_id = ?
            """
            params: List[Any] = [tenant_id]
            
            # Access control (unless admin)
            if not is_admin:
                query += """
                    AND (
                        scope = 'company'
                        OR (scope = 'personal' AND user_id = ?)
                    )
                """
                params.append(user_id)
            
            # Optional filters
            if scope:
                query += " AND scope = ?"
                params.append(scope.value)
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_document(row) for row in rows]
    
    async def get_company_documents(
        self,
        tenant_id: str,
        status: Optional[DocumentStatus] = None
    ) -> List[ScopedDocument]:
        """
        Get all company-wide documents for a tenant.
        
        Args:
            tenant_id: Tenant to query
            status: Optional status filter
            
        Returns:
            List of company documents
        """
        return await self.get_accessible_documents(
            tenant_id=tenant_id,
            user_id="",
            is_admin=True,
            scope=DocumentScope.COMPANY,
            status=status
        )
    
    async def get_personal_documents(
        self,
        tenant_id: str,
        user_id: str,
        status: Optional[DocumentStatus] = None
    ) -> List[ScopedDocument]:
        """
        Get all personal documents for a specific user.
        
        Args:
            tenant_id: Tenant context
            user_id: User to query
            status: Optional status filter
            
        Returns:
            List of user's personal documents
        """
        return await self.get_accessible_documents(
            tenant_id=tenant_id,
            user_id=user_id,
            is_admin=False,
            scope=DocumentScope.PERSONAL,
            status=status
        )
    
    async def count_documents(
        self,
        tenant_id: str,
        scope: Optional[DocumentScope] = None,
        user_id: Optional[str] = None
    ) -> int:
        """
        Count documents matching criteria.
        
        Args:
            tenant_id: Tenant to count
            scope: Filter by scope
            user_id: Filter by user (for personal docs)
            
        Returns:
            Document count
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM scoped_documents WHERE tenant_id = ?"
            params: List[Any] = [tenant_id]
            
            if scope:
                query += " AND scope = ?"
                params.append(scope.value)
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
    
    # =========================================================================
    # DOCUMENT DELETION
    # =========================================================================
    
    async def delete_document(
        self,
        doc_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete or archive a document.
        
        Args:
            doc_id: Document to delete
            hard_delete: If True, permanently remove from database
            
        Returns:
            True if successful
            
        Note:
            This only removes the metadata. Caller is responsible for:
            - Removing vectors from Qdrant
            - Deleting the file from disk
            
        Example:
            # Soft delete (archive)
            await manager.delete_document(doc_id)
            
            # Hard delete
            await manager.delete_document(doc_id, hard_delete=True)
            # Also do:
            await qdrant_client.delete(collection, doc_id)
            os.remove(file_path)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if hard_delete:
                cursor.execute(
                    "DELETE FROM scoped_documents WHERE id = ?",
                    (doc_id,)
                )
                logger.info(f"🗑️ Hard deleted document: {doc_id}")
            else:
                cursor.execute("""
                    UPDATE scoped_documents
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                """, (DocumentStatus.ARCHIVED.value, datetime.utcnow().isoformat(), doc_id))
                logger.info(f"📦 Archived document: {doc_id}")
            
            conn.commit()
            return cursor.rowcount > 0
    
    async def delete_user_documents(
        self,
        tenant_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> int:
        """
        Delete all personal documents for a user.
        
        Use when a user leaves the company or deletes their account.
        
        Args:
            tenant_id: Tenant context
            user_id: User whose documents to delete
            hard_delete: If True, permanently remove
            
        Returns:
            Number of documents affected
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if hard_delete:
                cursor.execute("""
                    DELETE FROM scoped_documents
                    WHERE tenant_id = ? AND user_id = ? AND scope = 'personal'
                """, (tenant_id, user_id))
            else:
                cursor.execute("""
                    UPDATE scoped_documents
                    SET status = ?, updated_at = ?
                    WHERE tenant_id = ? AND user_id = ? AND scope = 'personal'
                """, (
                    DocumentStatus.ARCHIVED.value,
                    datetime.utcnow().isoformat(),
                    tenant_id, user_id
                ))
            
            conn.commit()
            count = cursor.rowcount
            logger.info(f"Deleted {count} personal documents for user: {user_id}")
            return count
    
    # =========================================================================
    # QUERY FILTER GENERATION
    # =========================================================================
    
    def create_access_filter(
        self,
        tenant_id: str,
        user_id: str,
        is_admin: bool = False,
        include_company: bool = True,
        include_personal: bool = True
    ) -> DocumentAccessFilter:
        """
        Create an access filter for RAG queries.
        
        Use this to generate Qdrant filter conditions that enforce
        proper access control during vector search.
        
        Args:
            tenant_id: Tenant context
            user_id: User making query
            is_admin: Whether user is admin
            include_company: Include company documents
            include_personal: Include personal documents
            
        Returns:
            DocumentAccessFilter for use with Qdrant
            
        Example:
            filter = manager.create_access_filter(
                tenant_id="tenant-123",
                user_id="user-456"
            )
            
            # Use in Qdrant search
            results = qdrant_client.search(
                collection_name=tenant.qdrant_collection_name,
                query_vector=embedding,
                query_filter=filter.to_qdrant_filter()
            )
        """
        return DocumentAccessFilter(
            tenant_id=tenant_id,
            user_id=user_id,
            is_admin=is_admin,
            include_company=include_company,
            include_personal=include_personal
        )
    
    async def get_document_ids_for_user(
        self,
        tenant_id: str,
        user_id: str,
        is_admin: bool = False
    ) -> Set[str]:
        """
        Get all document IDs accessible to a user.
        
        Useful for post-filtering search results if Qdrant filtering
        is not working as expected.
        
        Args:
            tenant_id: Tenant context
            user_id: User making request
            is_admin: Whether user is admin
            
        Returns:
            Set of accessible document IDs
        """
        docs = await self.get_accessible_documents(
            tenant_id=tenant_id,
            user_id=user_id,
            is_admin=is_admin,
            status=DocumentStatus.READY
        )
        return {doc.id for doc in docs}
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _row_to_document(self, row: sqlite3.Row) -> ScopedDocument:
        """Convert database row to ScopedDocument object."""
        metadata = {}
        if row["metadata"]:
            try:
                metadata = json.loads(row["metadata"])
            except:
                metadata = {}
        
        tags = []
        if row["tags"]:
            try:
                tags = json.loads(row["tags"])
            except:
                tags = []
        
        return ScopedDocument(
            id=row["id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            filename=row["filename"],
            scope=DocumentScope(row["scope"]),
            status=DocumentStatus(row["status"]),
            file_path=row["file_path"],
            file_size=row["file_size"] or 0,
            file_type=row["file_type"] or "",
            chunk_count=row["chunk_count"] or 0,
            metadata=metadata,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            processed_at=row["processed_at"],
            tags=tags,
            description=row["description"] or ""
        )


# =============================================================================
# GLOBAL INSTANCE MANAGEMENT
# =============================================================================

_scope_manager: Optional[DocumentScopeManager] = None


def set_scope_manager(manager: DocumentScopeManager) -> None:
    """
    Set the global DocumentScopeManager instance.
    Call during application startup.
    """
    global _scope_manager
    _scope_manager = manager


def get_scope_manager() -> Optional[DocumentScopeManager]:
    """Get the global DocumentScopeManager instance."""
    return _scope_manager


# =============================================================================
# FASTAPI DEPENDENCY
# =============================================================================

async def require_scope_manager() -> DocumentScopeManager:
    """
    FastAPI dependency to require DocumentScopeManager.
    Raises 503 if not available.
    """
    from fastapi import HTTPException
    
    manager = get_scope_manager()
    if not manager:
        raise HTTPException(
            status_code=503,
            detail="Document scope management not available"
        )
    return manager


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("DOCUMENT SCOPES TEST")
        print("=" * 60)
        
        manager = DocumentScopeManager(db_path="data/test_scopes.db")
        
        tenant_id = "tenant-123"
        admin_id = "admin-001"
        user_id = "user-456"
        other_user = "user-789"
        
        # Register company document
        print("\n1. Registering company document...")
        company_doc = await manager.register_document(
            tenant_id=tenant_id,
            user_id=admin_id,
            filename="company_policy.pdf",
            scope=DocumentScope.COMPANY,
            file_size=1024,
            description="Employee handbook"
        )
        print(f"   ✅ Company doc: {company_doc.filename} (ID: {company_doc.id})")
        
        # Register personal document
        print("\n2. Registering personal document...")
        personal_doc = await manager.register_document(
            tenant_id=tenant_id,
            user_id=user_id,
            filename="my_notes.txt",
            scope=DocumentScope.PERSONAL,
            file_size=512
        )
        print(f"   ✅ Personal doc: {personal_doc.filename} (ID: {personal_doc.id})")
        
        # Test access
        print("\n3. Testing access control...")
        print(f"   Admin sees company doc: {company_doc.can_access(admin_id, is_admin=True)}")
        print(f"   User sees company doc: {company_doc.can_access(user_id)}")
        print(f"   Owner sees personal doc: {personal_doc.can_access(user_id)}")
        print(f"   Other user sees personal doc: {personal_doc.can_access(other_user)}")
        
        # Update status
        print("\n4. Updating document status to READY...")
        await manager.update_document_status(
            company_doc.id,
            status=DocumentStatus.READY,
            chunk_count=10
        )
        updated = await manager.get_document(company_doc.id)
        print(f"   Status: {updated.status.value}, Chunks: {updated.chunk_count}")
        
        # Get accessible documents
        print("\n5. Getting accessible documents for user...")
        docs = await manager.get_accessible_documents(
            tenant_id=tenant_id,
            user_id=user_id
        )
        print(f"   User can see {len(docs)} documents:")
        for d in docs:
            print(f"   - {d.filename} ({d.scope.value})")
        
        # Create Qdrant filter
        print("\n6. Creating Qdrant filter...")
        filter_obj = manager.create_access_filter(
            tenant_id=tenant_id,
            user_id=user_id
        )
        print(f"   Filter: {filter_obj.to_qdrant_filter()}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
    
    asyncio.run(test())