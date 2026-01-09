#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         TENANT MANAGER MODULE                                ║
║                                                                              ║
║  PURPOSE:                                                                    ║
║  Handles multi-tenant database operations, tenant lifecycle management,     ║
║  and data isolation. Each tenant (client company) gets completely           ║
║  isolated data storage.                                                      ║
║                                                                              ║
║  ARCHITECTURE:                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                      TENANT ISOLATION                               │    ║
║  │                                                                     │    ║
║  │   Tenant A (Acme Corp)        Tenant B (Widget Inc)                │    ║
║  │   ┌─────────────────┐         ┌─────────────────┐                  │    ║
║  │   │ Qdrant:         │         │ Qdrant:         │                  │    ║
║  │   │ tenant_A_docs   │         │ tenant_B_docs   │                  │    ║
║  │   │                 │         │                 │                  │    ║
║  │   │ SQLite:         │         │ SQLite:         │                  │    ║
║  │   │ users, docs...  │         │ users, docs...  │                  │    ║
║  │   └─────────────────┘         └─────────────────┘                  │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  USAGE:                                                                      ║
║  1. Import: from tenant_manager import TenantManager, get_tenant_manager    ║
║  2. Initialize in main_production_with_rag.py startup                       ║
║  3. Use set_tenant_manager() to make globally accessible                    ║
║                                                                              ║
║  INTEGRATES WITH:                                                            ║
║  - rag_components.py (vector store collection naming)                       ║
║  - auth.py (user-tenant relationships)                                      ║
║  - document_scopes.py (company vs personal documents)                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import logging
import secrets
import sqlite3
import uuid
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class TenantStatus(str, Enum):
    """
    Tenant account status.
    
    ACTIVE: Normal operation, all features available
    SUSPENDED: Temporarily disabled (e.g., payment issue)
    TRIAL: Trial period with potential limitations
    CANCELLED: Account cancelled, data retained for grace period
    """
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class TenantTier(str, Enum):
    """
    Subscription tier affecting limits and features.
    
    STARTER: Small teams, basic features
    PROFESSIONAL: Medium business, advanced features
    ENTERPRISE: Large org, all features, priority support
    """
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


# Default limits per tier (can be overridden per tenant)
TIER_LIMITS = {
    TenantTier.STARTER: {
        "max_users": 5,
        "max_documents": 100,
        "max_storage_mb": 500,
        "max_queries_per_day": 500,
    },
    TenantTier.PROFESSIONAL: {
        "max_users": 25,
        "max_documents": 1000,
        "max_storage_mb": 5000,
        "max_queries_per_day": 5000,
    },
    TenantTier.ENTERPRISE: {
        "max_users": -1,  # Unlimited
        "max_documents": -1,
        "max_storage_mb": -1,
        "max_queries_per_day": -1,
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Tenant:
    """
    Represents a tenant (client company) in the system.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Company display name
        slug: URL-safe identifier (auto-generated from name)
        domain: Primary email domain for user verification
        api_key_hash: Hashed API key (we never store plaintext)
        status: Account status (active, suspended, etc.)
        tier: Subscription tier
        created_at: Account creation timestamp
        settings: Tenant-specific configuration (JSON)
    """
    id: str
    name: str
    slug: str
    domain: Optional[str] = None
    api_key_hash: str = ""
    status: TenantStatus = TenantStatus.ACTIVE
    tier: TenantTier = TenantTier.STARTER
    created_at: str = ""
    updated_at: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Limits (from tier or custom override)
    max_users: int = 5
    max_documents: int = 100
    max_storage_mb: int = 500
    max_queries_per_day: int = 500
    
    def __post_init__(self):
        """Set defaults if not provided."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.settings:
            self.settings = {}
    
    @property
    def qdrant_collection_name(self) -> str:
        """
        Returns the Qdrant collection name for this tenant.
        Each tenant gets their own isolated collection.
        
        Example: tenant_abc123_documents
        """
        return f"tenant_{self.id}_documents"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant can use the system."""
        return self.status in (TenantStatus.ACTIVE, TenantStatus.TRIAL)
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses.
        
        Args:
            include_sensitive: If True, include API key hash
        """
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "status": self.status.value if isinstance(self.status, TenantStatus) else self.status,
            "tier": self.tier.value if isinstance(self.tier, TenantTier) else self.tier,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "settings": self.settings,
            "limits": {
                "max_users": self.max_users,
                "max_documents": self.max_documents,
                "max_storage_mb": self.max_storage_mb,
                "max_queries_per_day": self.max_queries_per_day,
            },
            "qdrant_collection": self.qdrant_collection_name,
        }
        if include_sensitive:
            data["api_key_hash"] = self.api_key_hash
        return data


@dataclass
class TenantUsage:
    """
    Tracks current resource usage for a tenant.
    Used for limit enforcement and billing.
    """
    tenant_id: str
    user_count: int = 0
    document_count: int = 0
    storage_bytes: int = 0
    queries_today: int = 0
    queries_this_month: int = 0
    last_query_at: Optional[str] = None
    
    @property
    def storage_mb(self) -> float:
        """Storage in megabytes."""
        return self.storage_bytes / (1024 * 1024)


# =============================================================================
# TENANT MANAGER CLASS
# =============================================================================

class TenantManager:
    """
    Manages multi-tenant operations including:
    - Tenant CRUD operations
    - API key generation and validation
    - Usage tracking and limit enforcement
    - Tenant-specific settings
    
    Thread-safe and async-compatible.
    
    Example:
        manager = TenantManager(db_path="data/tenants.db")
        
        # Create tenant
        tenant, api_key = await manager.create_tenant(
            name="Acme Corporation",
            domain="acme.com",
            tier=TenantTier.PROFESSIONAL
        )
        
        # Validate API key (for widget authentication)
        tenant = await manager.validate_api_key(api_key)
        
        # Get tenant's Qdrant collection name
        collection = tenant.qdrant_collection_name
    """
    
    def __init__(self, db_path: str = "data/tenants.db"):
        """
        Initialize the tenant manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._init_database()
        
        logger.info(f"✅ TenantManager initialized: {self.db_path}")
    
    # =========================================================================
    # DATABASE INITIALIZATION
    # =========================================================================
    
    def _init_database(self) -> None:
        """
        Create database tables if they don't exist.
        
        Tables:
        - tenants: Core tenant information
        - tenant_usage: Resource usage tracking
        - tenant_api_keys: API key management (supports key rotation)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    domain TEXT,
                    api_key_hash TEXT,
                    status TEXT DEFAULT 'active',
                    tier TEXT DEFAULT 'starter',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    settings TEXT DEFAULT '{}',
                    max_users INTEGER DEFAULT 5,
                    max_documents INTEGER DEFAULT 100,
                    max_storage_mb INTEGER DEFAULT 500,
                    max_queries_per_day INTEGER DEFAULT 500
                )
            """)
            
            # Usage tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_usage (
                    tenant_id TEXT PRIMARY KEY,
                    user_count INTEGER DEFAULT 0,
                    document_count INTEGER DEFAULT 0,
                    storage_bytes INTEGER DEFAULT 0,
                    queries_today INTEGER DEFAULT 0,
                    queries_this_month INTEGER DEFAULT 0,
                    last_query_at TEXT,
                    last_reset_date TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """)
            
            # API keys table (supports multiple keys per tenant for rotation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenant_api_keys (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    name TEXT DEFAULT 'default',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    last_used_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON tenant_api_keys(key_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON tenant_api_keys(tenant_id)")
            
            conn.commit()
            logger.debug("Database schema initialized")
    
    # =========================================================================
    # TENANT CRUD OPERATIONS
    # =========================================================================
    
    async def create_tenant(
        self,
        name: str,
        domain: Optional[str] = None,
        tier: TenantTier = TenantTier.STARTER,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[Tenant, str]:
        """
        Create a new tenant with auto-generated API key.
        
        Args:
            name: Company display name
            domain: Primary email domain (e.g., "acme.com")
            tier: Subscription tier
            settings: Initial settings dictionary
        
        Returns:
            Tuple of (Tenant object, plaintext API key)
            
        Note:
            The API key is only returned once at creation.
            Store it securely - it cannot be retrieved later.
            
        Example:
            tenant, api_key = await manager.create_tenant(
                name="Acme Corp",
                domain="acme.com",
                tier=TenantTier.PROFESSIONAL
            )
            print(f"API Key (save this!): {api_key}")
        """
        # Generate unique identifiers
        tenant_id = str(uuid.uuid4())
        slug = self._generate_slug(name)
        
        # Generate secure API key
        # Format: mc_live_<32 random chars>
        api_key = f"mc_live_{secrets.token_urlsafe(32)}"
        api_key_hash = self._hash_api_key(api_key)
        
        # Get tier limits
        limits = TIER_LIMITS.get(tier, TIER_LIMITS[TenantTier.STARTER])
        
        now = datetime.utcnow().isoformat()
        
        tenant = Tenant(
            id=tenant_id,
            name=name,
            slug=slug,
            domain=domain.lower() if domain else None,
            api_key_hash=api_key_hash,
            status=TenantStatus.ACTIVE,
            tier=tier,
            created_at=now,
            updated_at=now,
            settings=settings or {},
            max_users=limits["max_users"],
            max_documents=limits["max_documents"],
            max_storage_mb=limits["max_storage_mb"],
            max_queries_per_day=limits["max_queries_per_day"],
        )
        
        # Insert into database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO tenants (
                    id, name, slug, domain, api_key_hash, status, tier,
                    created_at, updated_at, settings,
                    max_users, max_documents, max_storage_mb, max_queries_per_day
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tenant.id, tenant.name, tenant.slug, tenant.domain,
                tenant.api_key_hash, tenant.status.value, tenant.tier.value,
                tenant.created_at, tenant.updated_at,
                json.dumps(tenant.settings),
                tenant.max_users, tenant.max_documents,
                tenant.max_storage_mb, tenant.max_queries_per_day
            ))
            
            # Initialize usage record
            cursor.execute("""
                INSERT INTO tenant_usage (tenant_id, last_reset_date)
                VALUES (?, ?)
            """, (tenant_id, now[:10]))
            
            # Store API key reference
            cursor.execute("""
                INSERT INTO tenant_api_keys (
                    id, tenant_id, key_hash, name, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), tenant_id, api_key_hash,
                "Primary API Key", now, 1
            ))
            
            conn.commit()
        
        logger.info(f"✅ Created tenant: {name} (ID: {tenant_id}, Collection: {tenant.qdrant_collection_name})")
        return tenant, api_key
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Retrieve a tenant by ID.
        
        Args:
            tenant_id: UUID of the tenant
            
        Returns:
            Tenant object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_tenant(row)
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Retrieve a tenant by URL slug.
        
        Args:
            slug: URL-safe identifier (e.g., "acme-corp")
            
        Returns:
            Tenant object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tenants WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_tenant(row)
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        Retrieve a tenant by email domain.
        Useful for automatic tenant detection during user signup.
        
        Args:
            domain: Email domain (e.g., "acme.com")
            
        Returns:
            Tenant object or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM tenants WHERE domain = ?", (domain.lower(),))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_tenant(row)
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """
        List tenants with optional filtering.
        
        Args:
            status: Filter by account status
            tier: Filter by subscription tier
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of Tenant objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM tenants WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status.value)
            
            if tier:
                query += " AND tier = ?"
                params.append(tier.value)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_tenant(row) for row in rows]
    
    async def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        domain: Optional[str] = None,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Tenant]:
        """
        Update tenant properties.
        
        Args:
            tenant_id: Tenant to update
            name: New display name
            domain: New email domain
            status: New account status
            tier: New subscription tier (also updates limits)
            settings: New settings (merged with existing)
            
        Returns:
            Updated Tenant object or None if not found
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if domain is not None:
            updates.append("domain = ?")
            params.append(domain.lower() if domain else None)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
        
        if tier is not None:
            updates.append("tier = ?")
            params.append(tier.value)
            # Update limits based on new tier
            limits = TIER_LIMITS.get(tier, TIER_LIMITS[TenantTier.STARTER])
            updates.extend([
                "max_users = ?",
                "max_documents = ?",
                "max_storage_mb = ?",
                "max_queries_per_day = ?"
            ])
            params.extend([
                limits["max_users"],
                limits["max_documents"],
                limits["max_storage_mb"],
                limits["max_queries_per_day"]
            ])
        
        if settings is not None:
            # Merge with existing settings
            merged = {**tenant.settings, **settings}
            updates.append("settings = ?")
            params.append(json.dumps(merged))
        
        if not updates:
            return tenant
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(tenant_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tenants SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
        
        logger.info(f"✅ Updated tenant: {tenant_id}")
        return await self.get_tenant(tenant_id)
    
    async def delete_tenant(self, tenant_id: str, hard_delete: bool = False) -> bool:
        """
        Delete or deactivate a tenant.
        
        Args:
            tenant_id: Tenant to delete
            hard_delete: If True, permanently remove all data.
                        If False, just mark as cancelled.
                        
        Returns:
            True if successful
            
        Warning:
            Hard delete requires additional cleanup:
            - Delete Qdrant collection
            - Delete uploaded files
            - Delete user records
        """
        if hard_delete:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tenant_api_keys WHERE tenant_id = ?", (tenant_id,))
                cursor.execute("DELETE FROM tenant_usage WHERE tenant_id = ?", (tenant_id,))
                cursor.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
                conn.commit()
            logger.warning(f"⚠️ Hard deleted tenant: {tenant_id}")
        else:
            await self.update_tenant(tenant_id, status=TenantStatus.CANCELLED)
            logger.info(f"✅ Soft deleted (cancelled) tenant: {tenant_id}")
        
        return True
    
    # =========================================================================
    # API KEY MANAGEMENT
    # =========================================================================
    
    async def validate_api_key(self, api_key: str) -> Optional[Tenant]:
        """
        Validate an API key and return the associated tenant.
        
        This is the PRIMARY authentication method for the embeddable widget.
        
        Args:
            api_key: The API key to validate (e.g., "mc_live_xxx...")
            
        Returns:
            Tenant object if valid and active, None if invalid/expired
            
        Example:
            tenant = await manager.validate_api_key(request.headers["X-API-Key"])
            if not tenant:
                raise HTTPException(401, "Invalid API key")
        """
        if not api_key or not api_key.startswith("mc_"):
            return None
        
        key_hash = self._hash_api_key(api_key)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Find active key
            cursor.execute("""
                SELECT k.tenant_id, k.expires_at
                FROM tenant_api_keys k
                WHERE k.key_hash = ? AND k.is_active = 1
            """, (key_hash,))
            
            key_row = cursor.fetchone()
            if not key_row:
                logger.warning("Invalid API key attempted")
                return None
            
            # Check expiration
            if key_row["expires_at"]:
                expires = datetime.fromisoformat(key_row["expires_at"])
                if datetime.utcnow() > expires:
                    logger.warning(f"Expired API key for tenant: {key_row['tenant_id']}")
                    return None
            
            # Update last used timestamp
            cursor.execute("""
                UPDATE tenant_api_keys 
                SET last_used_at = ? 
                WHERE key_hash = ?
            """, (datetime.utcnow().isoformat(), key_hash))
            conn.commit()
            
            # Get and return tenant
            return await self.get_tenant(key_row["tenant_id"])
    
    async def rotate_api_key(self, tenant_id: str) -> Optional[str]:
        """
        Generate a new API key and deactivate the old one.
        
        Use this for security key rotation or if a key is compromised.
        
        Args:
            tenant_id: Tenant to rotate key for
            
        Returns:
            New plaintext API key (store securely!) or None if tenant not found
            
        Warning:
            The old key stops working immediately!
        """
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        
        # Generate new key
        new_api_key = f"mc_live_{secrets.token_urlsafe(32)}"
        new_hash = self._hash_api_key(new_api_key)
        now = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Deactivate all old keys
            cursor.execute("""
                UPDATE tenant_api_keys 
                SET is_active = 0 
                WHERE tenant_id = ?
            """, (tenant_id,))
            
            # Create new key
            cursor.execute("""
                INSERT INTO tenant_api_keys (
                    id, tenant_id, key_hash, name, created_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), tenant_id, new_hash,
                f"Rotated Key - {now[:10]}", now, 1
            ))
            
            # Update tenant's primary key hash
            cursor.execute("""
                UPDATE tenants SET api_key_hash = ?, updated_at = ?
                WHERE id = ?
            """, (new_hash, now, tenant_id))
            
            conn.commit()
        
        logger.info(f"✅ Rotated API key for tenant: {tenant_id}")
        return new_api_key
    
    # =========================================================================
    # USAGE TRACKING
    # =========================================================================
    
    async def get_usage(self, tenant_id: str) -> Optional[TenantUsage]:
        """
        Get current resource usage for a tenant.
        
        Args:
            tenant_id: Tenant to check
            
        Returns:
            TenantUsage object or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM tenant_usage WHERE tenant_id = ?",
                (tenant_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return TenantUsage(
                tenant_id=row["tenant_id"],
                user_count=row["user_count"] or 0,
                document_count=row["document_count"] or 0,
                storage_bytes=row["storage_bytes"] or 0,
                queries_today=row["queries_today"] or 0,
                queries_this_month=row["queries_this_month"] or 0,
                last_query_at=row["last_query_at"]
            )
    
    async def increment_query_count(self, tenant_id: str) -> bool:
        """
        Increment query count for a tenant.
        
        Call this after each successful query. Handles daily reset automatically.
        
        Args:
            tenant_id: Tenant making the query
            
        Returns:
            True if successful
        """
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current usage and check for daily reset
            cursor.execute(
                "SELECT queries_today, last_reset_date FROM tenant_usage WHERE tenant_id = ?",
                (tenant_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return False
            
            queries_today, last_reset = row
            
            # Reset if new day
            if last_reset != today:
                cursor.execute("""
                    UPDATE tenant_usage 
                    SET queries_today = 1, 
                        queries_this_month = queries_this_month + 1,
                        last_query_at = ?,
                        last_reset_date = ?
                    WHERE tenant_id = ?
                """, (now.isoformat(), today, tenant_id))
            else:
                cursor.execute("""
                    UPDATE tenant_usage 
                    SET queries_today = queries_today + 1,
                        queries_this_month = queries_this_month + 1,
                        last_query_at = ?
                    WHERE tenant_id = ?
                """, (now.isoformat(), tenant_id))
            
            conn.commit()
        
        return True
    
    async def check_query_limit(self, tenant_id: str) -> Tuple[bool, int, int]:
        """
        Check if tenant is within query limits.
        
        Args:
            tenant_id: Tenant to check
            
        Returns:
            Tuple of (within_limit, current_count, max_allowed)
            
        Example:
            within, current, max_val = await manager.check_query_limit(tenant_id)
            if not within:
                raise HTTPException(429, f"Query limit exceeded: {current}/{max_val}")
        """
        tenant = await self.get_tenant(tenant_id)
        usage = await self.get_usage(tenant_id)
        
        if not tenant or not usage:
            return False, 0, 0
        
        max_queries = tenant.max_queries_per_day
        
        # -1 means unlimited
        if max_queries == -1:
            return True, usage.queries_today, -1
        
        return usage.queries_today < max_queries, usage.queries_today, max_queries
    
    async def update_document_count(
        self,
        tenant_id: str,
        delta: int = 1,
        storage_delta: int = 0
    ) -> None:
        """
        Update document count and storage usage.
        
        Args:
            tenant_id: Tenant to update
            delta: Change in document count (+1 for add, -1 for delete)
            storage_delta: Change in storage bytes
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenant_usage 
                SET document_count = document_count + ?,
                    storage_bytes = storage_bytes + ?
                WHERE tenant_id = ?
            """, (delta, storage_delta, tenant_id))
            conn.commit()
    
    async def update_user_count(self, tenant_id: str, delta: int = 1) -> None:
        """
        Update user count for a tenant.
        
        Args:
            tenant_id: Tenant to update
            delta: Change in user count (+1 for add, -1 for remove)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tenant_usage 
                SET user_count = user_count + ?
                WHERE tenant_id = ?
            """, (delta, tenant_id))
            conn.commit()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _generate_slug(self, name: str) -> str:
        """
        Generate URL-safe slug from company name.
        Handles duplicates by appending numbers.
        
        Example: "Acme Corp" -> "acme-corp"
                 "Acme Corp" (duplicate) -> "acme-corp-2"
        """
        # Convert to lowercase, replace spaces with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug).strip('-')
        
        # Check for duplicates
        base_slug = slug
        counter = 1
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            while True:
                cursor.execute("SELECT id FROM tenants WHERE slug = ?", (slug,))
                if not cursor.fetchone():
                    break
                counter += 1
                slug = f"{base_slug}-{counter}"
        
        return slug
    
    def _hash_api_key(self, api_key: str) -> str:
        """
        Create secure hash of API key.
        We never store plaintext keys.
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _row_to_tenant(self, row: sqlite3.Row) -> Tenant:
        """Convert database row to Tenant object."""
        settings = {}
        if row["settings"]:
            try:
                settings = json.loads(row["settings"])
            except:
                settings = {}
        
        return Tenant(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            domain=row["domain"],
            api_key_hash=row["api_key_hash"] or "",
            status=TenantStatus(row["status"]),
            tier=TenantTier(row["tier"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            settings=settings,
            max_users=row["max_users"],
            max_documents=row["max_documents"],
            max_storage_mb=row["max_storage_mb"],
            max_queries_per_day=row["max_queries_per_day"],
        )


# =============================================================================
# GLOBAL INSTANCE MANAGEMENT
# =============================================================================

_tenant_manager: Optional[TenantManager] = None


def set_tenant_manager(manager: TenantManager) -> None:
    """
    Set the global TenantManager instance.
    Call this during application startup.
    
    Example:
        manager = TenantManager(db_path="data/tenants.db")
        set_tenant_manager(manager)
    """
    global _tenant_manager
    _tenant_manager = manager


def get_tenant_manager() -> Optional[TenantManager]:
    """
    Get the global TenantManager instance.
    Returns None if not initialized.
    """
    return _tenant_manager


# =============================================================================
# FASTAPI DEPENDENCY
# =============================================================================

async def require_tenant_manager() -> TenantManager:
    """
    FastAPI dependency to require TenantManager.
    Raises 503 if not available.
    
    Example:
        @app.get("/api/tenants")
        async def list_tenants(manager: TenantManager = Depends(require_tenant_manager)):
            return await manager.list_tenants()
    """
    from fastapi import HTTPException
    
    manager = get_tenant_manager()
    if not manager:
        raise HTTPException(
            status_code=503,
            detail="Multi-tenant system not available"
        )
    return manager


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    """Quick test of TenantManager functionality."""
    import asyncio
    
    async def test():
        print("=" * 60)
        print("TENANT MANAGER TEST")
        print("=" * 60)
        
        manager = TenantManager(db_path="data/test_tenants.db")
        
        # Create tenant
        print("\n1. Creating tenant...")
        tenant, api_key = await manager.create_tenant(
            name="Test Company",
            domain="test.com",
            tier=TenantTier.PROFESSIONAL
        )
        
        print(f"   ✅ Created tenant: {tenant.name}")
        print(f"   📝 Tenant ID: {tenant.id}")
        print(f"   🔑 API Key: {api_key}")
        print(f"   📦 Qdrant Collection: {tenant.qdrant_collection_name}")
        print(f"   📊 Limits: {tenant.max_documents} docs, {tenant.max_queries_per_day} queries/day")
        
        # Validate key
        print("\n2. Validating API key...")
        validated = await manager.validate_api_key(api_key)
        print(f"   {'✅ Valid' if validated else '❌ Invalid'}")
        
        # Check limits
        print("\n3. Checking query limits...")
        within, current, max_val = await manager.check_query_limit(tenant.id)
        print(f"   Queries: {current}/{max_val} ({'✅ OK' if within else '❌ Exceeded'})")
        
        # Increment query
        print("\n4. Incrementing query count...")
        await manager.increment_query_count(tenant.id)
        within, current, max_val = await manager.check_query_limit(tenant.id)
        print(f"   Queries: {current}/{max_val}")
        
        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)
    
    asyncio.run(test())