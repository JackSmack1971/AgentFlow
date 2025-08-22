import json
from typing import Any

from apps.api.app.utils.logging import logger, setup_logging


def test_secret_redaction(capsys: Any) -> None:
    setup_logging()
    secret = "a" * 32
    logger.info(f"Using API key {secret}")
    output = capsys.readouterr().out
    record = json.loads(output)
    assert "***" in record["record"]["message"]
    assert secret not in record["record"]["message"]
