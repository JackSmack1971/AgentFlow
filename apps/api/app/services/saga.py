"""Saga pattern implementation for coordinating distributed transactions across multiple databases.

This module provides a robust Saga pattern implementation that ensures data consistency
across PostgreSQL, Redis, Qdrant, and Neo4j databases during agent creation workflows.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import get_cache
from ..database import get_session
from ..db.models import Agent, Organization
from ..exceptions import AgentFlowError
from ..observability.audit import AuditEvent, log_audit
from ..services.graph_db import GraphDBService, graph_db_service
from ..services.vector_db import VectorDBService, vector_db_service


logger = logging.getLogger(__name__)


class SagaError(AgentFlowError):
    """Raised when saga transaction operations fail."""

    def __init__(self, message: str, transaction_id: str, failed_step: str | None = None) -> None:
        super().__init__(message, "SAGA001")
        self.transaction_id = transaction_id
        self.failed_step = failed_step


class SagaStepError(SagaError):
    """Raised when a specific saga step fails."""

    def __init__(
        self,
        message: str,
        transaction_id: str,
        step_name: str,
        compensation_needed: bool = True
    ) -> None:
        super().__init__(message, transaction_id, step_name)
        self.step_name = step_name
        self.compensation_needed = compensation_needed


class SagaStep(ABC):
    """Abstract base class for saga steps with execute and compensation methods."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.executed = False
        self.compensated = False
        self.execution_data: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the forward operation.

        Args:
            context: Transaction context containing data needed for execution

        Returns:
            Dict containing execution results and data needed for compensation

        Raises:
            SagaStepError: If execution fails
        """
        pass

    @abstractmethod
    async def compensate(self, context: Dict[str, Any]) -> None:
        """Execute the compensation (rollback) operation.

        Args:
            context: Transaction context containing compensation data

        Raises:
            SagaStepError: If compensation fails
        """
        pass


class SagaTransaction:
    """Orchestrator for saga pattern transactions with rollback capability."""

    def __init__(
        self,
        transaction_id: str,
        steps: List[SagaStep],
        audit_context: Optional[Dict[str, Any]] = None
    ) -> None:
        self.transaction_id = transaction_id
        self.steps = steps
        self.audit_context = audit_context or {}
        self.executed_steps: List[SagaStep] = []
        self.failed_step: Optional[SagaStep] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status: str = "pending"  # pending, executing, completed, failed, compensated

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the saga transaction with automatic rollback on failure.

        Args:
            context: Initial transaction context

        Returns:
            Dict containing final transaction results

        Raises:
            SagaError: If transaction fails and cannot be fully compensated
        """
        self.start_time = datetime.utcnow()
        self.status = "executing"

        try:
            await self._log_transaction_event("started", context)

            # Execute each step in sequence
            current_context = context.copy()
            for step in self.steps:
                try:
                    logger.info(
                        f"Saga {self.transaction_id}: Executing step {step.name}"
                    )

                    step_result = await step.execute(current_context)
                    step.executed = True
                    step.execution_data = step_result
                    self.executed_steps.append(step)

                    # Update context with step results
                    current_context.update(step_result)

                    await self._log_step_event(step, "completed", step_result)

                except Exception as exc:
                    logger.error(
                        f"Saga {self.transaction_id}: Step {step.name} failed: {exc}"
                    )

                    step_result = {"error": str(exc), "step": step.name}
                    await self._log_step_event(step, "failed", step_result)

                    # Mark transaction as failed
                    self.failed_step = step
                    self.status = "failed"

                    # Attempt compensation
                    await self._compensate_transaction(context)

                    raise SagaStepError(
                        f"Step {step.name} failed: {exc}",
                        self.transaction_id,
                        step.name
                    ) from exc

            # All steps completed successfully
            self.status = "completed"
            self.end_time = datetime.utcnow()

            await self._log_transaction_event("completed", current_context)

            return current_context

        except SagaStepError:
            raise  # Re-raise saga step errors
        except Exception as exc:
            logger.error(f"Saga {self.transaction_id}: Unexpected error: {exc}")
            self.status = "failed"

            await self._compensate_transaction(context)

            raise SagaError(
                f"Unexpected error in transaction: {exc}",
                self.transaction_id
            ) from exc

    async def _compensate_transaction(self, original_context: Dict[str, Any]) -> None:
        """Execute compensation for all completed steps in reverse order.

        Args:
            original_context: Original transaction context
        """
        if not self.executed_steps:
            logger.info(f"Saga {self.transaction_id}: No steps to compensate")
            return

        logger.warning(f"Saga {self.transaction_id}: Starting compensation")

        compensation_errors = []

        # Compensate in reverse order
        for step in reversed(self.executed_steps):
            if not step.compensated:
                try:
                    logger.info(
                        f"Saga {self.transaction_id}: Compensating step {step.name}"
                    )

                    compensation_context = original_context.copy()
                    compensation_context.update(step.execution_data)

                    await step.compensate(compensation_context)
                    step.compensated = True

                    await self._log_step_event(step, "compensated", step.execution_data)

                except Exception as exc:
                    logger.error(
                        f"Saga {self.transaction_id}: Compensation failed for step {step.name}: {exc}"
                    )

                    compensation_errors.append(f"{step.name}: {exc}")

                    await self._log_step_event(
                        step,
                        "compensation_failed",
                        {"error": str(exc)}
                    )

        if compensation_errors:
            self.status = "compensation_failed"
            error_msg = "; ".join(compensation_errors)
            logger.error(f"Saga {self.transaction_id}: Compensation errors: {error_msg}")

            await self._log_transaction_event(
                "compensation_failed",
                {"compensation_errors": compensation_errors}
            )
        else:
            self.status = "compensated"
            logger.info(f"Saga {self.transaction_id}: Compensation completed successfully")
            await self._log_transaction_event("compensated", {})

    async def _log_transaction_event(
        self,
        event_type: str,
        context: Dict[str, Any]
    ) -> None:
        """Log a transaction-level audit event.

        Args:
            event_type: Type of transaction event
            context: Event context data
        """
        try:
            audit_event = AuditEvent(
                ts=datetime.utcnow(),
                request_id=self.audit_context.get("request_id"),
                actor=self.audit_context.get("actor"),
                route=f"saga:{self.transaction_id}",
                tools_called=[f"saga_step:{step.name}" for step in self.executed_steps],
                egress=["postgresql", "redis", "qdrant", "neo4j"]
            )

            # Add transaction-specific data
            audit_data = {
                "transaction_id": self.transaction_id,
                "event_type": event_type,
                "status": self.status,
                "step_count": len(self.steps),
                "executed_steps": len(self.executed_steps),
                "failed_step": self.failed_step.name if self.failed_step else None,
                "duration_ms": (
                    (datetime.utcnow() - self.start_time).total_seconds() * 1000
                    if self.start_time else None
                ),
                **context
            }

            logger.info(f"Saga transaction {event_type}", **audit_data)

        except Exception as exc:
            logger.error(f"Failed to log saga transaction event: {exc}")

    async def _log_step_event(
        self,
        step: SagaStep,
        event_type: str,
        context: Dict[str, Any]
    ) -> None:
        """Log a step-level audit event.

        Args:
            step: The saga step
            event_type: Type of step event
            context: Event context data
        """
        try:
            audit_data = {
                "transaction_id": self.transaction_id,
                "step_name": step.name,
                "event_type": event_type,
                "step_executed": step.executed,
                "step_compensated": step.compensated,
                **context
            }

            logger.info(f"Saga step {event_type}", **audit_data)

        except Exception as exc:
            logger.error(f"Failed to log saga step event: {exc}")


# Database-specific Saga Steps

class PostgreSQLStep(SagaStep):
    """Saga step for PostgreSQL operations with SQLAlchemy."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.session: Optional[AsyncSession] = None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PostgreSQL operation within a transaction.

        Args:
            context: Must contain 'organization_id' and 'agent_data'

        Returns:
            Dict with created agent data for compensation

        Raises:
            SagaStepError: If database operation fails
        """
        try:
            self.session = context.get("db_session")
            if not self.session:
                self.session = await get_session().__aenter__()

            organization_id = context["organization_id"]
            agent_data = context["agent_data"]

            # Create agent record
            agent = Agent(
                name=agent_data["name"],
                organization_id=organization_id
            )

            self.session.add(agent)
            await self.session.flush()  # Get the ID without committing

            result = {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "organization_id": organization_id,
                "created_at": datetime.utcnow().isoformat()
            }

            return result

        except Exception as exc:
            raise SagaStepError(
                f"PostgreSQL operation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc

    async def compensate(self, context: Dict[str, Any]) -> None:
        """Delete the created agent record.

        Args:
            context: Contains agent_id from execution

        Raises:
            SagaStepError: If compensation fails
        """
        try:
            if not self.session:
                self.session = await get_session().__aenter__()

            agent_id = self.execution_data.get("agent_id")
            if agent_id:
                # Soft delete by setting deleted_at
                agent = await self.session.get(Agent, agent_id)
                if agent:
                    agent.deleted_at = datetime.utcnow()
                    await self.session.commit()

        except Exception as exc:
            raise SagaStepError(
                f"PostgreSQL compensation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc


class RedisStep(SagaStep):
    """Saga step for Redis cache operations."""

    def __init__(self, name: str, cache_ttl: int = 3600) -> None:
        super().__init__(name)
        self.cache_ttl = cache_ttl

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Cache agent session data in Redis.

        Args:
            context: Must contain 'agent_id' and 'session_data'

        Returns:
            Dict with cache keys for compensation

        Raises:
            SagaStepError: If cache operation fails
        """
        try:
            cache = get_cache()
            agent_id = context["agent_id"]
            session_data = context["session_data"]

            # Create cache key for agent session
            cache_key = f"agent_session:{agent_id}"

            # Store session data
            await cache.set(cache_key, session_data, ttl=self.cache_ttl)

            result = {
                "cache_key": cache_key,
                "cached_data": session_data,
                "ttl": self.cache_ttl
            }

            return result

        except Exception as exc:
            raise SagaStepError(
                f"Redis operation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc

    async def compensate(self, context: Dict[str, Any]) -> None:
        """Remove cached session data.

        Args:
            context: Contains cache_key from execution

        Raises:
            SagaStepError: If compensation fails
        """
        try:
            cache = get_cache()
            cache_key = self.execution_data.get("cache_key")

            if cache_key:
                await cache.client.delete(cache_key)

        except Exception as exc:
            raise SagaStepError(
                f"Redis compensation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc


class QdrantStep(SagaStep):
    """Saga step for Qdrant vector database operations."""

    def __init__(self, name: str, collection_name: str = "agent_embeddings") -> None:
        super().__init__(name)
        self.collection_name = collection_name
        self.vector_db = vector_db_service

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Store agent embeddings in Qdrant.

        Args:
            context: Must contain 'agent_id' and 'embeddings'

        Returns:
            Dict with stored vector data for compensation

        Raises:
            SagaStepError: If vector operation fails
        """
        try:
            agent_id = context["agent_id"]
            embeddings = context["embeddings"]

            # Prepare points for Qdrant
            points = [{
                "id": str(agent_id),
                "vector": embeddings,
                "payload": {
                    "agent_id": str(agent_id),
                    "type": "agent_embedding",
                    "created_at": datetime.utcnow().isoformat()
                }
            }]

            # Store vectors
            result = await self.vector_db.upsert_vectors(
                self.collection_name,
                points
            )

            return {
                "collection_name": self.collection_name,
                "agent_id": str(agent_id),
                "vector_count": len(points),
                "operation_id": result.get("operation_id")
            }

        except Exception as exc:
            raise SagaStepError(
                f"Qdrant operation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc

    async def compensate(self, context: Dict[str, Any]) -> None:
        """Remove stored embeddings from Qdrant.

        Args:
            context: Contains agent_id from execution

        Raises:
            SagaStepError: If compensation fails
        """
        try:
            agent_id = self.execution_data.get("agent_id")

            if agent_id:
                # Delete vectors by ID
                points_selector = {"ids": [agent_id]}
                await self.vector_db.delete_vectors(
                    self.collection_name,
                    points_selector
                )

        except Exception as exc:
            raise SagaStepError(
                f"Qdrant compensation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc


class Neo4jStep(SagaStep):
    """Saga step for Neo4j graph database operations."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.graph_db = graph_db_service

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create agent relationships in Neo4j.

        Args:
            context: Must contain 'agent_id', 'organization_id', and 'relationships'

        Returns:
            Dict with created graph data for compensation

        Raises:
            SagaStepError: If graph operation fails
        """
        try:
            agent_id = context["agent_id"]
            organization_id = context["organization_id"]
            relationships = context.get("relationships", [])

            created_nodes = []
            created_relationships = []

            # Create agent node
            agent_node = await self.graph_db.create_node(
                labels=["Agent"],
                properties={
                    "id": str(agent_id),
                    "organization_id": str(organization_id),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            created_nodes.append({"id": agent_node.get("id"), "labels": ["Agent"]})

            # Create relationships
            for relationship in relationships:
                rel = await self.graph_db.create_relationship(
                    from_node_id=str(agent_id),
                    to_node_id=relationship["target_id"],
                    relationship_type=relationship["type"],
                    properties=relationship.get("properties", {})
                )
                created_relationships.append({
                    "from": str(agent_id),
                    "to": relationship["target_id"],
                    "type": relationship["type"],
                    "id": rel.get("id")
                })

            return {
                "created_nodes": created_nodes,
                "created_relationships": created_relationships,
                "agent_node_id": agent_node.get("id")
            }

        except Exception as exc:
            raise SagaStepError(
                f"Neo4j operation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc

    async def compensate(self, context: Dict[str, Any]) -> None:
        """Remove created nodes and relationships from Neo4j.

        Args:
            context: Contains created graph data from execution

        Raises:
            SagaStepError: If compensation fails
        """
        try:
            created_nodes = self.execution_data.get("created_nodes", [])

            # Delete nodes (this will also delete relationships)
            for node in created_nodes:
                node_id = node.get("id")
                if node_id:
                    await self.graph_db.delete_node(node_id)

        except Exception as exc:
            raise SagaStepError(
                f"Neo4j compensation failed: {exc}",
                context.get("transaction_id", "unknown"),
                self.name
            ) from exc


# High-level agent creation saga

async def create_agent_saga(
    organization_id: UUID,
    agent_data: Dict[str, Any],
    session_data: Dict[str, Any],
    embeddings: List[float],
    relationships: Optional[List[Dict[str, Any]]] = None,
    audit_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute agent creation saga across all databases.

    Args:
        organization_id: Organization ID for the agent
        agent_data: Agent metadata
        session_data: Session cache data
        embeddings: Vector embeddings for the agent
        relationships: Optional graph relationships
        audit_context: Audit logging context

    Returns:
        Dict containing created agent information

    Raises:
        SagaError: If agent creation fails
    """
    transaction_id = f"agent_creation_{organization_id}_{datetime.utcnow().timestamp()}"

    # Create saga steps
    steps = [
        PostgreSQLStep("postgresql_agent_creation"),
        RedisStep("redis_session_cache"),
        QdrantStep("qdrant_embeddings"),
        Neo4jStep("neo4j_relationships")
    ]

    # Create and execute saga
    saga = SagaTransaction(transaction_id, steps, audit_context)

    context = {
        "transaction_id": transaction_id,
        "organization_id": organization_id,
        "agent_data": agent_data,
        "session_data": session_data,
        "embeddings": embeddings,
        "relationships": relationships or []
    }

    try:
        result = await saga.execute(context)

        return {
            "transaction_id": transaction_id,
            "agent_id": result.get("agent_id"),
            "status": "success",
            "created_at": datetime.utcnow().isoformat()
        }

    except SagaError as exc:
        return {
            "transaction_id": transaction_id,
            "status": "failed",
            "error": str(exc),
            "failed_step": exc.failed_step,
            "compensated": saga.status == "compensated"
        }


__all__ = [
    "SagaError",
    "SagaStepError",
    "SagaStep",
    "SagaTransaction",
    "PostgreSQLStep",
    "RedisStep",
    "QdrantStep",
    "Neo4jStep",
    "create_agent_saga"
]