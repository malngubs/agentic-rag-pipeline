"""
Authentication and Authorization Module
Provides JWT-based authentication with bcrypt password hashing
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

import bcrypt
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr


# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "viewer"  # admin, editor, viewer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class AuthManager:
    """Manages user authentication and authorization"""

    def __init__(self, db_path: str = "data/auth.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize authentication database with users table"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                metadata TEXT
            )
        """)

        # Create index on email for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)

        conn.commit()
        conn.close()

        # Create default admin user if no users exist
        self._create_default_admin()

    def _create_default_admin(self):
        """Create default admin user if no users exist"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()['count']

        if count == 0:
            # Create default admin: admin@example.com / admin123
            password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, ("admin@example.com", password_hash.decode('utf-8'), "Default Admin", "admin"))
            conn.commit()
            print("✅ Created default admin user: admin@example.com / admin123")

        conn.close()

    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def create_access_token(self, user_id: int, email: str, role: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create new user account"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")

            # Hash password
            password_hash = self.hash_password(user_data.password)

            # Insert user
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """, (user_data.email, password_hash, user_data.full_name, user_data.role))

            conn.commit()
            user_id = cursor.lastrowid

            # Get created user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = dict(cursor.fetchone())

            return UserResponse(
                id=user['id'],
                email=user['email'],
                full_name=user['full_name'],
                role=user['role'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,))
            user = cursor.fetchone()

            if not user:
                return None

            user_dict = dict(user)

            # Verify password
            if not self.verify_password(password, user_dict['password_hash']):
                return None

            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user_dict['id'],)
            )
            conn.commit()

            return user_dict

    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
            user = cursor.fetchone()

            if not user:
                return None

            user_dict = dict(user)
            return UserResponse(
                id=user_dict['id'],
                email=user_dict['email'],
                full_name=user_dict['full_name'],
                role=user_dict['role'],
                created_at=user_dict['created_at'],
                last_login=user_dict['last_login']
            )

    def get_all_users(self) -> list[UserResponse]:
        """Get all active users"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC")
            users = cursor.fetchall()

            return [
                UserResponse(
                    id=dict(user)['id'],
                    email=dict(user)['email'],
                    full_name=dict(user)['full_name'],
                    role=dict(user)['role'],
                    created_at=dict(user)['created_at'],
                    last_login=dict(user)['last_login']
                )
                for user in users
            ]


# Global auth manager instance (will be set by app)
_auth_manager_instance: Optional[AuthManager] = None


def set_auth_manager(auth_manager: AuthManager):
    """Set global auth manager instance"""
    global _auth_manager_instance
    _auth_manager_instance = auth_manager


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    if not _auth_manager_instance:
        raise HTTPException(status_code=500, detail="Auth manager not initialized")
    return _auth_manager_instance


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> UserResponse:
    """Dependency to get current authenticated user"""
    auth_manager = get_auth_manager()

    token = credentials.credentials
    payload = auth_manager.decode_token(token)

    user_id = int(payload.get("sub"))
    user = auth_manager.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional)
) -> Optional[UserResponse]:
    """Optional authentication - returns None if not authenticated"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# Role-based permission checker
class RoleChecker:
    """Dependency class to check user roles"""

    def __init__(self, required_role: str):
        self.required_role = required_role
        self.role_hierarchy = {"viewer": 0, "editor": 1, "admin": 2}

    async def __call__(self, current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
        user_level = self.role_hierarchy.get(current_user.role, -1)
        required_level = self.role_hierarchy.get(self.required_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {self.required_role}, Current: {current_user.role}"
            )

        return current_user


# Convenience role checkers
require_viewer = RoleChecker("viewer")
require_editor = RoleChecker("editor")
require_admin = RoleChecker("admin")
