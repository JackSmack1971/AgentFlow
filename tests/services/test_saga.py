"""Tests for Saga pattern implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.saga import (
    SagaTransaction,
    PostgreSQLStep,
    RedisStep,
    QdrantStep,
    Neo4jStep,
    SagaError,
    SagaStepError,
    create_agent_saga
)


class TestSagaSteps:
    """Test individual saga steps."""

    @pytest.mark.asyncio
    async def test_postgresql_step_success(self):
        """Test PostgreSQL step executes successfully."""
        step = PostgreSQLStep("test_postgres")

        context = {
            "organization_id": uuid4(),
            "agent_data": {"name": "Test Agent"}
        }

        # Mock the database session
        mock_session = AsyncMock()
        mock_agent = MagicMock()
        mock_agent.id = uuid4()
        mock_session.add.return_value = None
        mock_session.flush.return_value = None

        with patch('app.services.saga.get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            result = await step.execute(context)

            assert result["agent_id"] == mock_agent.id
            assert result["agent_name"] == "Test Agent"
            assert step.executed is True

    @pytest.mark.asyncio
    async def test_postgresql_step_compensation(self):
        """Test PostgreSQL step compensation."""
        step = PostgreSQLStep("test_postgres")

        # Set up execution data
        agent_id = uuid4()
        step.execution_data = {"agent_id": agent_id}
        step.executed = True

        context = {"transaction_id": "test_tx"}

        # Mock the database session
        mock_session = AsyncMock()
        mock_agent = MagicMock()
        mock_session.get.return_value = mock_agent

        with patch('app.services.saga.get_session') as mock_get_session:
            mock_get_session.return_value.__aenter__.return_value = mock_session

            await step.compensate(context)

            assert step.compensated is True
            mock_agent.soft_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_step_success(self):
        """Test Redis step executes successfully."""
        step = RedisStep("test_redis", cache_ttl=300)

        context = {
            "agent_id": uuid4(),
            "session_data": {"key": "value"}
        }

        # Mock the cache
        mock_cache = AsyncMock()

        with patch('app.services.saga.get_cache', return_value=mock_cache):
            result = await step.execute(context)

            assert "cache_key" in result
            assert result["ttl"] == 300
            assert step.executed is True
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_qdrant_step_success(self):
        """Test Qdrant step executes successfully."""
        step = QdrantStep("test_qdrant")

        context = {
            "agent_id": uuid4(),
            "embeddings": [0.1, 0.2, 0.3]
        }

        # Mock the vector database
        mock_vector_db = AsyncMock()
        mock_vector_db.upsert_vectors.return_value = {"operation_id": "test_op"}

        with patch('app.services.saga.vector_db_service', mock_vector_db):
            result = await step.execute(context)

            assert result["operation_id"] == "test_op"
            assert result["vector_count"] == 1
            assert step.executed is True

    @pytest.mark.asyncio
    async def test_neo4j_step_success(self):
        """Test Neo4j step executes successfully."""
        step = Neo4jStep("test_neo4j")

        context = {
            "agent_id": uuid4(),
            "organization_id": uuid4(),
            "relationships": []
        }

        # Mock the graph database
        mock_graph_db = AsyncMock()
        mock_graph_db.create_node.return_value = {"id": "node_123"}

        with patch('app.services.saga.graph_db_service', mock_graph_db):
            result = await step.execute(context)

            assert result["agent_node_id"] == "node_123"
            assert step.executed is True


class TestSagaTransaction:
    """Test saga transaction orchestration."""

    @pytest.mark.asyncio
    async def test_successful_transaction(self):
        """Test successful saga transaction execution."""
        # Create mock steps
        step1 = MagicMock()
        step1.name = "step1"
        step1.execute = AsyncMock(return_value={"result": "step1_done"})
        step1.compensate = AsyncMock()

        step2 = MagicMock()
        step2.name = "step2"
        step2.execute = AsyncMock(return_value={"result": "step2_done"})
        step2.compensate = AsyncMock()

        steps = [step1, step2]
        transaction = SagaTransaction("test_tx", steps)

        context = {"initial": "data"}

        result = await transaction.execute(context)

        assert transaction.status == "completed"
        assert result["initial"] == "data"
        assert result["result"] == "step2_done"
        assert len(transaction.executed_steps) == 2

        step1.execute.assert_called_once()
        step2.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_failure_with_compensation(self):
        """Test transaction failure triggers compensation."""
        # Create mock steps
        step1 = MagicMock()
        step1.name = "step1"
        step1.execute = AsyncMock(return_value={"result": "step1_done"})
        step1.compensate = AsyncMock()

        step2 = MagicMock()
        step2.name = "step2"
        step2.execute = AsyncMock(side_effect=Exception("Step 2 failed"))
        step2.compensate = AsyncMock()

        steps = [step1, step2]
        transaction = SagaTransaction("test_tx", steps)

        context = {"initial": "data"}

        with pytest.raises(SagaError):
            await transaction.execute(context)

        assert transaction.status == "compensated"
        assert transaction.failed_step == step2
        assert len(transaction.executed_steps) == 1

        # Verify compensation was called in reverse order
        step1.compensate.assert_called_once()
        step2.compensate.assert_not_called()  # Failed step doesn't need compensation

    @pytest.mark.asyncio
    async def test_create_agent_saga_success(self):
        """Test the high-level create_agent_saga function."""
        organization_id = uuid4()
        agent_data = {"name": "Test Agent"}
        session_data = {"session": "data"}
        embeddings = [0.1, 0.2, 0.3]
        relationships = []

        # Mock all database services
        with patch('app.services.saga.get_session') as mock_session, \
             patch('app.services.saga.get_cache') as mock_cache, \
             patch('app.services.saga.vector_db_service') as mock_vector_db, \
             patch('app.services.saga.graph_db_service') as mock_graph_db:

            # Setup mocks
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_cache.return_value = AsyncMock()
            mock_vector_db.upsert_vectors = AsyncMock(return_value={"operation_id": "test"})
            mock_graph_db.create_node = AsyncMock(return_value={"id": "node_123"})

            result = await create_agent_saga(
                organization_id=organization_id,
                agent_data=agent_data,
                session_data=session_data,
                embeddings=embeddings,
                relationships=relationships
            )

            assert result["status"] == "success"
            assert "transaction_id" in result
            assert "agent_id" in result

    @pytest.mark.asyncio
    async def test_create_agent_saga_failure(self):
        """Test create_agent_saga handles failures gracefully."""
        organization_id = uuid4()
        agent_data = {"name": "Test Agent"}
        session_data = {"session": "data"}
        embeddings = [0.1, 0.2, 0.3]

        # Mock services to fail at Qdrant step
        with patch('app.services.saga.get_session') as mock_session, \
             patch('app.services.saga.get_cache') as mock_cache, \
             patch('app.services.saga.vector_db_service') as mock_vector_db, \
             patch('app.services.saga.graph_db_service') as mock_graph_db:

            # Setup mocks - make Qdrant fail
            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_cache.return_value = AsyncMock()
            mock_vector_db.upsert_vectors = AsyncMock(side_effect=Exception("Qdrant failed"))
            mock_graph_db.create_node = AsyncMock(return_value={"id": "node_123"})

            result = await create_agent_saga(
                organization_id=organization_id,
                agent_data=agent_data,
                session_data=session_data,
                embeddings=embeddings
            )

            assert result["status"] == "failed"
            assert "transaction_id" in result
            assert result["compensated"] is True
            assert "Qdrant" in result["failed_step"]


if __name__ == "__main__":
    pytest.main([__file__])