from __future__ import annotations

import socket
import subprocess
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/e2e" in str(item.path):
            item.add_marker(pytest.mark.e2e)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def app_url() -> Iterator[str]:
    port = _free_port()
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "http.server",
            "--bind",
            "127.0.0.1",
            "--directory",
            "web",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}/"
    deadline = time.monotonic() + 10
    try:
        while True:
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Local app server did not start.") from exc
                time.sleep(0.1)
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
