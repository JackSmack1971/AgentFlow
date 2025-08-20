"""Check project dependencies and log warnings."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import List, Tuple

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "dependency_warnings.txt"


class DependencyCheckError(Exception):
    """Raised when dependency checks fail."""


async def run_command(cmd: List[str]) -> Tuple[str, str, int]:
    env = {**os.environ, "PYTHONWARNINGS": "default"}
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate()
    return stdout.decode(), stderr.decode(), proc.returncode


async def main() -> int:
    LOG_DIR.mkdir(exist_ok=True)
    warnings.filterwarnings("default")
    logs: List[str] = []
    critical = False

    cmds: List[List[str]] = [["pip", "list", "--outdated"]]
    if os.getenv("SKIP_TESTS") != "1":
        cmds.append(["pytest", "-q", "--disable-warnings"])

    for cmd in cmds:
        env = os.environ.copy()
        env["PYTHONWARNINGS"] = "default"
        if cmd[0] == "pytest":
            env["DEP_CHECK_RUNNING"] = "1"
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        out = stdout_bytes.decode()
        err = stderr_bytes.decode()
        logs.append(f"$ {' '.join(cmd)}\n{out}{err}\n")
        if proc.returncode != 0 or "ERROR" in err.upper():
            critical = True

    LOG_FILE.write_text("".join(logs))
    if critical:
        raise DependencyCheckError("Critical issues detected; see log for details.")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    try:
        asyncio.run(main())
    except DependencyCheckError as exc:  # pragma: no cover
        logging.warning("%s", exc)
        sys.exit(1)
