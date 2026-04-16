from app.connectivity import DEFAULT_PORTS, probe_tcp, resolve_host_port


def test_resolve_host_port_uses_explicit_port() -> None:
    assert resolve_host_port("postgresql://user:pw@db.example.com:6543/app") == (
        "db.example.com",
        6543,
    )


def test_resolve_host_port_falls_back_to_default_for_postgres() -> None:
    assert resolve_host_port("postgresql://user:pw@db.example.com/app") == (
        "db.example.com",
        DEFAULT_PORTS["postgresql"],
    )


def test_resolve_host_port_falls_back_to_default_for_redis() -> None:
    assert resolve_host_port("redis://cache.example.com/0") == (
        "cache.example.com",
        DEFAULT_PORTS["redis"],
    )


def test_resolve_host_port_unknown_scheme_returns_zero_port() -> None:
    host, port = resolve_host_port("foo://somewhere")
    assert host == "somewhere"
    assert port == 0


def test_resolve_host_port_empty_url_defaults_to_localhost() -> None:
    host, port = resolve_host_port("")
    assert host == "localhost"
    assert port == 0


def test_probe_tcp_returns_unreachable_dict_on_failure() -> None:
    # porta 1 em localhost praticamente nunca esta escutando; probe deve
    # retornar dict estruturado em vez de levantar excecao.
    result = probe_tcp("redis://127.0.0.1:1", timeout=0.2)

    assert result["reachable"] is False
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 1
    assert "error" in result


def test_probe_tcp_returns_reachable_dict_on_success() -> None:
    import socket

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    bound_port = server.getsockname()[1]

    try:
        result = probe_tcp(f"redis://127.0.0.1:{bound_port}", timeout=0.5)
    finally:
        server.close()

    assert result == {"reachable": True, "host": "127.0.0.1", "port": bound_port}
