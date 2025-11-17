"""
Audit Logging System
Tracks all user actions for security compliance and troubleshooting
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class AuditLogger:
    """Comprehensive audit logging system"""

    # Event categories
    CATEGORY_AUTH = "authentication"
    CATEGORY_DOCUMENT = "document"
    CATEGORY_DATA = "data_access"
    CATEGORY_USER = "user_management"
    CATEGORY_SYSTEM = "system"

    # Event actions
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_LOGIN_FAILED = "login_failed"
    ACTION_UPLOAD = "upload_document"
    ACTION_DELETE = "delete_document"
    ACTION_VIEW = "view_document"
    ACTION_VIEW_CONVERSATIONS = "view_conversations"
    ACTION_VIEW_ANALYTICS = "view_analytics"
    ACTION_CREATE_USER = "create_user"
    ACTION_UPDATE_USER = "update_user"
    ACTION_DELETE_USER = "delete_user"
    ACTION_CHANGE_CONFIG = "change_configuration"

    def __init__(self, db_path: str = "data/audit_log.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize audit log database"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create audit_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                user_email TEXT,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                metadata TEXT
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_logs(category)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)
        """)

        conn.commit()
        conn.close()

    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def log(
        self,
        category: str,
        action: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create an audit log entry

        Args:
            category: Event category (auth, document, data, user, system)
            action: Specific action performed
            user_id: ID of user performing action
            user_email: Email of user performing action
            resource_type: Type of resource affected (document, user, etc.)
            resource_id: ID of specific resource
            details: Human-readable description
            ip_address: IP address of request
            user_agent: User agent string
            status: success, failure, warning
            error_message: Error message if failed
            metadata: Additional structured data

        Returns:
            ID of created audit log entry
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO audit_logs (
                    user_id, user_email, category, action, resource_type, resource_id,
                    details, ip_address, user_agent, status, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, user_email, category, action, resource_type, resource_id,
                details, ip_address, user_agent, status, error_message, metadata_json
            ))

            conn.commit()
            return cursor.lastrowid

    def log_auth_event(
        self,
        action: str,
        user_email: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> int:
        """Log authentication event"""
        details = f"User {user_email} {action}"
        return self.log(
            category=self.CATEGORY_AUTH,
            action=action,
            user_id=user_id,
            user_email=user_email,
            details=details,
            ip_address=ip_address,
            status=status,
            error_message=error_message
        )

    def log_document_event(
        self,
        action: str,
        user_id: int,
        user_email: str,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log document operation"""
        details = f"User {user_email} {action}"
        if document_name:
            details += f": {document_name}"

        return self.log(
            category=self.CATEGORY_DOCUMENT,
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type="document",
            resource_id=document_id,
            details=details,
            ip_address=ip_address,
            metadata=metadata
        )

    def log_data_access(
        self,
        action: str,
        user_id: int,
        user_email: str,
        resource_type: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log data access event"""
        details = f"User {user_email} accessed {resource_type}"

        return self.log(
            category=self.CATEGORY_DATA,
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            details=details,
            ip_address=ip_address,
            metadata=metadata
        )

    def log_user_management(
        self,
        action: str,
        admin_user_id: int,
        admin_email: str,
        target_user_id: Optional[int] = None,
        target_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """Log user management action"""
        details = f"Admin {admin_email} {action}"
        if target_email:
            details += f" user {target_email}"

        return self.log(
            category=self.CATEGORY_USER,
            action=action,
            user_id=admin_user_id,
            user_email=admin_email,
            resource_type="user",
            resource_id=str(target_user_id) if target_user_id else None,
            details=details,
            ip_address=ip_address,
            metadata=metadata
        )

    def get_logs(
        self,
        user_id: Optional[int] = None,
        category: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query audit logs with filters

        Returns:
            Dictionary with logs array and total count
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE conditions
            conditions = []
            params = []

            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)

            if category:
                conditions.append("category = ?")
                params.append(category)

            if action:
                conditions.append("action = ?")
                params.append(action)

            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)

            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)

            if status:
                conditions.append("status = ?")
                params.append(status)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM audit_logs WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # Get logs
            query = f"""
                SELECT * FROM audit_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            cursor.execute(query, params)

            logs = []
            for row in cursor.fetchall():
                log = dict(row)
                if log['metadata']:
                    log['metadata'] = json.loads(log['metadata'])
                logs.append(log)

            return {
                'logs': logs,
                'total': total,
                'limit': limit,
                'offset': offset
            }

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most recent audit logs"""
        result = self.get_logs(limit=limit, offset=0)
        return result['logs']

    def get_user_activity(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Get activity for a specific user"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = self.get_logs(user_id=user_id, start_date=start_date, limit=1000)
        return result['logs']

    def get_failed_logins(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed login attempts in recent hours"""
        start_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        result = self.get_logs(
            category=self.CATEGORY_AUTH,
            action=self.ACTION_LOGIN_FAILED,
            start_date=start_date,
            limit=1000
        )
        return result['logs']

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit log statistics"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total events
            cursor.execute("""
                SELECT COUNT(*) as total FROM audit_logs WHERE timestamp >= ?
            """, (start_date,))
            total = cursor.fetchone()['total']

            # Events by category
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ?
                GROUP BY category
            """, (start_date,))
            by_category = {row['category']: row['count'] for row in cursor.fetchall()}

            # Events by user
            cursor.execute("""
                SELECT user_email, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ? AND user_email IS NOT NULL
                GROUP BY user_email
                ORDER BY count DESC
                LIMIT 10
            """, (start_date,))
            by_user = [dict(row) for row in cursor.fetchall()]

            # Failed events
            cursor.execute("""
                SELECT COUNT(*) as count FROM audit_logs
                WHERE timestamp >= ? AND status = 'failure'
            """, (start_date,))
            failed = cursor.fetchone()['count']

            return {
                'total_events': total,
                'by_category': by_category,
                'top_users': by_user,
                'failed_events': failed,
                'period_days': days
            }


# Global audit logger instance
_audit_logger_instance: Optional[AuditLogger] = None


def set_audit_logger(audit_logger: AuditLogger):
    """Set global audit logger instance"""
    global _audit_logger_instance
    _audit_logger_instance = audit_logger


def get_audit_logger() -> Optional[AuditLogger]:
    """Get global audit logger instance"""
    return _audit_logger_instance
