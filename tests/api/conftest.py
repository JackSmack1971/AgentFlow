import os
import pathlib
import sys
import types

import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))

# Minimal environment configuration for FastAPI app
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

# Stub pydantic_ai to avoid heavy dependency during tests
mock_ai = types.ModuleType("pydantic_ai")


class DummyAgent:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.settings = None

    async def run(self, prompt: str):  # pragma: no cover - stub
        class R:
            output_text = ""

        return R()


mock_ai.Agent = DummyAgent
models_mod = types.ModuleType("pydantic_ai.models")


class DummyModelSettings:
    def __init__(self, **kwargs: object) -> None:
        pass


models_mod.ModelSettings = DummyModelSettings
sys.modules["pydantic_ai"] = mock_ai
sys.modules["pydantic_ai.models"] = models_mod

from apps.api.app.dependencies import User, get_current_user  # noqa: E402
from apps.api.app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def override_user(request) -> None:
    """Override authentication for non-security tests.

    Security tests in tests/security/ should use real authentication
    and should NOT have this fixture applied.
    """
    # Skip authentication override for security tests
    if request.module.__name__.startswith("tests.security"):
        yield
        return

    async def fake_get_current_user() -> User:
        return User(sub="u1", roles=["user"])

    app.dependency_overrides[get_current_user] = fake_get_current_user
    yield
    app.dependency_overrides.clear()