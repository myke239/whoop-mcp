import sys

from whoop_mcp.cli import main


def test_verify_uses_profile_not_optional_body(monkeypatch, capsys):
    from whoop_mcp import client

    class API:
        def singleton(self, kind):
            assert kind == "profile"
            return {"data": {"email": "private@example.invalid", "first_name": "PRIVATE"}}

    monkeypatch.setattr(client, "WhoopClient", API)
    monkeypatch.setattr(sys, "argv", ["whoop-mcp", "verify"])
    main()
    output = capsys.readouterr().out
    assert "authenticated read passed" in output
    assert "PRIVATE" not in output and "private@example.invalid" not in output
