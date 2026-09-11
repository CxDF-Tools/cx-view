import logging
import socket

import uvicorn

from app.config import DEFAULT_PORT, MAX_PORT_ATTEMPTS

logger = logging.getLogger(__name__)


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def find_available_port(start_port: int = DEFAULT_PORT, host: str = "127.0.0.1") -> int:
    """Return the first available port at or after start_port, incrementing by 1."""
    for offset in range(MAX_PORT_ATTEMPTS):
        candidate = start_port + offset
        if _is_port_available(host, candidate):
            return candidate
    raise RuntimeError(
        f"No available port found in range {start_port}-{start_port + MAX_PORT_ATTEMPTS - 1}"
    )


def main() -> None:
    host = "127.0.0.1"
    port = find_available_port(DEFAULT_PORT, host)
    if port != DEFAULT_PORT:
        logger.info("Port %s was in use; starting on %s instead", DEFAULT_PORT, port)
    uvicorn.run("app.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
