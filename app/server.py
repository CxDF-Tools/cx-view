import logging
import socket
import sys

import uvicorn

from app.config import DEFAULT_PORT, MAX_PORT_ATTEMPTS

logger = logging.getLogger(__name__)


class NoAvailablePortError(RuntimeError):
    pass


def _is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return False
        return True


def find_available_port(start_port: int = DEFAULT_PORT, host: str = "127.0.0.1") -> int:
    """Return the first available port at or after start_port, incrementing by 1.

    Only checks start_port through start_port + MAX_PORT_ATTEMPTS - 1 before giving up.
    """
    last_checked = start_port
    for offset in range(MAX_PORT_ATTEMPTS):
        last_checked = start_port + offset
        if _is_port_available(host, last_checked):
            return last_checked
    raise NoAvailablePortError(
        f"No available port found in the range {start_port}-{last_checked} "
        f"({MAX_PORT_ATTEMPTS} ports checked, starting from CX_VIEW_PORT={start_port}). "
        "Free up a port in that range, or set CX_VIEW_PORT in .env to a different starting port."
    )


def main() -> None:
    host = "127.0.0.1"
    try:
        port = find_available_port(DEFAULT_PORT, host)
    except NoAvailablePortError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if port != DEFAULT_PORT:
        logger.info("Port %s was in use; starting on %s instead", DEFAULT_PORT, port)
    uvicorn.run("app.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
