from __future__ import annotations

import pytest

from tplink_deco_mcp_server import RouterSettings


def test_reads_every_variable() -> None:
    settings = RouterSettings.from_environment(
        {
            "DECO_HOST": " 192.168.68.1 ",
            "DECO_PASSWORD": "secret",
            "DECO_USERNAME": "owner",
            "DECO_TIMEOUT": "2.5",
        }
    )

    assert settings == RouterSettings(
        host="192.168.68.1", password="secret", username="owner", timeout_seconds=2.5
    )


def test_defaults_username_and_timeout() -> None:
    settings = RouterSettings.from_environment(
        {"DECO_HOST": "192.168.68.1", "DECO_PASSWORD": "secret", "DECO_USERNAME": " "}
    )

    assert settings.username == "admin"
    assert settings.timeout_seconds == 10.0


def test_keeps_the_password_out_of_repr() -> None:
    assert "secret" not in repr(RouterSettings(host="192.168.68.1", password="secret"))


@pytest.mark.parametrize(
    "environment",
    [{}, {"DECO_HOST": "192.168.68.1"}, {"DECO_PASSWORD": "secret"}],
)
def test_requires_host_and_password(environment: dict[str, str]) -> None:
    with pytest.raises(ValueError, match="DECO_HOST and DECO_PASSWORD must be set"):
        RouterSettings.from_environment(environment)


@pytest.mark.parametrize(
    ("timeout", "reason"),
    [("soon", "is not a number"), ("0", "must be positive"), ("-1", "must be positive")],
)
def test_rejects_an_invalid_timeout(timeout: str, reason: str) -> None:
    environment = {"DECO_HOST": "192.168.68.1", "DECO_PASSWORD": "secret", "DECO_TIMEOUT": timeout}

    with pytest.raises(ValueError, match=reason):
        RouterSettings.from_environment(environment)
