"""
Custom exceptions for the RAG system.
"""

from typing import Optional, Dict, Any


class RAGException(Exception):
    """Base exception for RAG system errors."""
    
    def __init__(self, 
                 message: str, 
                 error_type: str = "RAG_ERROR",
                 status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class LLMException(RAGException):
    """Exception for LLM-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LLM_ERROR", 503, details)


class VectorStoreException(RAGException):
    """Exception for vector store errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VECTOR_STORE_ERROR", 503, details)


class DocumentProcessingException(RAGException):
    """Exception for document processing errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", 400, details)


class AuthenticationException(RAGException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR", 401)


class RateLimitException(RAGException):
    """Exception for rate limiting."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR", 429)