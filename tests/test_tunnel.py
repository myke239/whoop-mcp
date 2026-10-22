import socket

import pytest

from whoop_mcp.tunnel import reserve


def test_port_reserved_before_tunnel():
    occupied = socket.socket()
    occupied.bind(("127.0.0.1", 0))
    occupied.listen(1)
    try:
        with pytest.raises(ValueError, match="occupied"):
            reserve(occupied.getsockname()[1])
    finally:
        occupied.close()


@pytest.mark.parametrize("port", [0, 80, 65536])
def test_privileged_or_invalid_ports_refused(port):
    with pytest.raises(ValueError):
        reserve(port)
