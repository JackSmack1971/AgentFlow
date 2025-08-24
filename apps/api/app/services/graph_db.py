"""Graph database service layer for Neo4j operations.

This module provides graph database operations with circuit breaker protection
to prevent cascading failures when the Neo4j service is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError

from ..core.settings import get_settings
from ..exceptions import ProviderError
from .circuit_breaker import circuit_breaker_manager, ServiceUnavailableError

logger = logging.getLogger(__name__)

settings = get_settings()


class GraphDBServiceError(ProviderError):
    """Raised when graph database operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, "P003")


class GraphDBService:
    """Service for interacting with Neo4j graph database."""

    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None) -> None:
        self.uri = uri or "bolt://localhost:7687"
        self.user = user or "neo4j"
        self.password = password or "password"
        self._driver: Any | None = None

    async def _get_driver(self) -> Any:
        """Get or create the Neo4j driver."""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    async def _execute_with_circuit_breaker(
        self, operation: str, func: Any, *args: Any, **kwargs: Any
    ) -> Any:
        """Execute a Neo4j operation with circuit breaker protection."""

        async def _execute() -> Any:
            """Inner function that performs the actual operation."""
            driver = await self._get_driver()
            async with driver.session() as session:
                return await func(session, *args, **kwargs)

        try:
            return await circuit_breaker_manager.call_with_breaker(
                "neo4j", _execute
            )
        except ServiceUnavailableError as exc:
            raise GraphDBServiceError(str(exc)) from exc

    async def run_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results."""

        async def _execute_query(session: Any, query: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
            """Execute the query within a session."""
            result = await session.run(query, parameters=params or {})
            records = []
            async for record in result:
                records.append(dict(record))
            return records

        try:
            return await self._execute_with_circuit_breaker(
                "run_query",
                _execute_query,
                query,
                parameters,
            )
        except Neo4jError as exc:
            raise GraphDBServiceError(f"Failed to execute query: {query}") from exc

    async def create_node(
        self,
        labels: list[str],
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a new node in the graph."""

        async def _create_node(session: Any, labels: list[str], props: dict[str, Any]) -> dict[str, Any]:
            """Create node within a session."""
            label_str = ":".join(labels)
            query = f"CREATE (n:{label_str} $props) RETURN n"
            result = await session.run(query, props=props)
            record = await result.single()
            return dict(record["n"]) if record else {}

        try:
            return await self._execute_with_circuit_breaker(
                "create_node",
                _create_node,
                labels,
                properties,
            )
        except Neo4jError as exc:
            raise GraphDBServiceError(f"Failed to create node with labels {labels}") from exc

    async def create_relationship(
        self,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a relationship between two nodes."""

        async def _create_relationship(
            session: Any,
            from_id: str,
            to_id: str,
            rel_type: str,
            props: dict[str, Any] | None,
        ) -> dict[str, Any]:
            """Create relationship within a session."""
            query = f"""
            MATCH (a), (b)
            WHERE id(a) = $from_id AND id(b) = $to_id
            CREATE (a)-[r:{rel_type} $props]->(b)
            RETURN r
            """
            result = await session.run(
                query,
                from_id=int(from_id),
                to_id=int(to_id),
                props=props or {},
            )
            record = await result.single()
            return dict(record["r"]) if record else {}

        try:
            return await self._execute_with_circuit_breaker(
                "create_relationship",
                _create_relationship,
                from_node_id,
                to_node_id,
                relationship_type,
                properties,
            )
        except Neo4jError as exc:
            raise GraphDBServiceError(f"Failed to create relationship {relationship_type}") from exc

    async def find_nodes(
        self,
        labels: list[str] | None = None,
        properties: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Find nodes matching the given criteria."""

        async def _find_nodes(
            session: Any,
            labels: list[str] | None,
            props: dict[str, Any] | None,
            limit: int,
        ) -> list[dict[str, Any]]:
            """Find nodes within a session."""
            label_filter = ""
            if labels:
                label_str = ":".join(labels)
                label_filter = f":{label_str}"

            where_clauses = []
            params = {"limit": limit}

            if props:
                for key, value in props.items():
                    where_clauses.append(f"n.{key} = ${key}")
                    params[key] = value

            where_clause = ""
            if where_clauses:
                where_clause = "WHERE " + " AND ".join(where_clauses)

            query = f"MATCH (n{label_filter}) {where_clause} RETURN n LIMIT $limit"
            result = await session.run(query, parameters=params)
            records = []
            async for record in result:
                records.append(dict(record["n"]))
            return records

        try:
            return await self._execute_with_circuit_breaker(
                "find_nodes",
                _find_nodes,
                labels,
                properties,
                limit,
            )
        except Neo4jError as exc:
            raise GraphDBServiceError("Failed to find nodes") from exc

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node from the graph."""

        async def _delete_node(session: Any, node_id: str) -> bool:
            """Delete node within a session."""
            query = "MATCH (n) WHERE id(n) = $node_id DELETE n"
            result = await session.run(query, node_id=int(node_id))
            summary = await result.consume()
            return summary.counters.nodes_deleted > 0

        try:
            return await self._execute_with_circuit_breaker(
                "delete_node",
                _delete_node,
                node_id,
            )
        except Neo4jError as exc:
            raise GraphDBServiceError(f"Failed to delete node {node_id}") from exc

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the Neo4j service."""

        try:
            # Simple health check by running a basic query
            result = await self.run_query("RETURN 'Neo4j is healthy' as status")
            return {"status": "healthy", "result": result}
        except Exception as exc:
            raise GraphDBServiceError("Neo4j service health check failed") from exc

    async def close(self) -> None:
        """Close the database connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None


# Global graph database service instance
graph_db_service = GraphDBService()


__all__ = [
    "GraphDBService",
    "GraphDBServiceError",
    "graph_db_service",
]