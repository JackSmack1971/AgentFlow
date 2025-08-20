import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(os.getenv("DEP_CHECK_RUNNING") == "1", reason="avoid recursion")
def test_dependency_script_creates_log() -> None:
    log_path = Path("logs/dependency_warnings.txt")
    if log_path.exists():
        log_path.unlink()
    result = subprocess.run(
        ["python", "scripts/check_dependencies.py"],
        env={**os.environ, "SKIP_TESTS": "1"},
        check=False,
    )
    assert result.returncode == 0
    assert log_path.exists()
    assert log_path.read_text().strip()
