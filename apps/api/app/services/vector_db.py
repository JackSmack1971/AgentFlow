"""Vector database service layer for Qdrant operations.

This module provides vector database operations with circuit breaker protection
to prevent cascading failures when the Qdrant service is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException

from ..core.settings import get_settings
from ..exceptions import ProviderError
from .circuit_breaker import circuit_breaker_manager, ServiceUnavailableError

logger = logging.getLogger(__name__)

settings = get_settings()


class VectorDBServiceError(ProviderError):
    """Raised when vector database operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "P002")


class VectorDBService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.qdrant_url
        self._client: AsyncQdrantClient | None = None

    async def _get_client(self) -> AsyncQdrantClient:
        """Get or create the Qdrant client."""
        if self._client is None:
            self._client = AsyncQdrantClient(url=self.url)
        return self._client

    async def _execute_with_circuit_breaker(
        self, operation: str, func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a Qdrant operation with circuit breaker protection."""

        async def _execute() -> Any:
            """Inner function that performs the actual operation."""
            client = await self._get_client()
            return await func(client, *args, **kwargs)

        try:
            return await circuit_breaker_manager.call_with_breaker(
                "qdrant", _execute
            )
        except ServiceUnavailableError as exc:
            raise VectorDBServiceError(str(exc)) from exc

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: str = "Cosine",
    ) -> dict[str, Any]:
        """Create a new vector collection."""

        try:
            return await self._execute_with_circuit_breaker(
                "create_collection",
                lambda client: client.create_collection(
                    collection_name=collection_name,
                    vectors_config={"size": vector_size, "distance": distance},
                ),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to create collection {collection_name}") from exc

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a vector collection."""

        try:
            return await self._execute_with_circuit_breaker(
                "delete_collection",
                lambda client: client.delete_collection(collection_name),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to delete collection {collection_name}") from exc

    async def upsert_vectors(
        self,
        collection_name: str,
        points: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Upsert vectors into a collection."""

        try:
            return await self._execute_with_circuit_breaker(
                "upsert_vectors",
                lambda client: client.upsert(
                    collection_name=collection_name,
                    points=points,
                ),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to upsert vectors to {collection_name}") from exc

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
    ) -> dict[str, Any]:
        """Search for similar vectors."""

        try:
            return await self._execute_with_circuit_breaker(
                "search_vectors",
                lambda client: client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                ),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to search vectors in {collection_name}") from exc

    async def delete_vectors(
        self,
        collection_name: str,
        points_selector: dict[str, Any],
    ) -> dict[str, Any]:
        """Delete vectors from a collection."""

        try:
            return await self._execute_with_circuit_breaker(
                "delete_vectors",
                lambda client: client.delete(
                    collection_name=collection_name,
                    points_selector=points_selector,
                ),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to delete vectors from {collection_name}") from exc

    async def get_collection_info(self, collection_name: str) -> dict[str, Any]:
        """Get information about a collection."""

        try:
            return await self._execute_with_circuit_breaker(
                "get_collection_info",
                lambda client: client.get_collection(collection_name),
            )
        except ResponseHandlingException as exc:
            raise VectorDBServiceError(f"Failed to get collection info for {collection_name}") from exc

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Qdrant service."""

        try:
            client = await self._get_client()
            # Simple health check by listing collections
            return await client.get_collections()
        except Exception as exc:
            raise VectorDBServiceError("Qdrant service health check failed") from exc


# Global vector database service instance
vector_db_service = VectorDBService()


__all__ = [
    "VectorDBService",
    "VectorDBServiceError",
    "vector_db_service",
]