"""Custom exceptions for memory module."""


class MemoryError(Exception):
    """Base exception for memory operations."""


class MemoryNotFoundError(MemoryError):
    """Raised when a memory item is not found."""


class MemoryServiceError(MemoryError):
    """Raised when memory backend operations fail."""


class MemoryStreamError(MemoryError):
    """Base error for memory streaming."""


class MemoryStreamTimeoutError(MemoryStreamError):
    """Raised when memory stream times out."""
