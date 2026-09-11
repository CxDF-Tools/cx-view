import socket

import pytest

from app.server import NoAvailablePortError, find_available_port


def test_finds_start_port_when_free():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]

    assert find_available_port(free_port) == free_port


def test_increments_past_a_busy_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        busy_port = busy.getsockname()[1]

        found = find_available_port(busy_port)

        assert found > busy_port


def test_raises_clear_error_when_no_port_available_in_range(monkeypatch):
    import app.server as server_module

    monkeypatch.setattr(server_module, "MAX_PORT_ATTEMPTS", 3)
    monkeypatch.setattr(server_module, "_is_port_available", lambda host, port: False)

    with pytest.raises(NoAvailablePortError, match="3 ports checked"):
        find_available_port(9999)
