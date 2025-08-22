import pytest
from pydantic import ValidationError

from apps.api.app.models.auth import UserCreate
from apps.api.app.models.schemas import RAGQuery


def test_user_create_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            password="secret",
            unknown="value",
        )


def test_rag_query_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        RAGQuery(query="hello", unknown=True)
