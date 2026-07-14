from __future__ import annotations

import asyncio
import importlib
import sys
from unittest.mock import AsyncMock

from fastapi import HTTPException
from fastapi.testclient import TestClient


def load_backend(monkeypatch):
    monkeypatch.setenv("HEALTH_API_TOKEN", "api-token-with-at-least-32-characters")
    monkeypatch.setenv("DASHBOARD_PASSWORD", "dashboard-test-password")
    monkeypatch.setenv("DASHBOARD_SESSION_SECRET", "session-secret-with-at-least-32-characters")
    monkeypatch.setenv("DASHBOARD_COOKIE_SECURE", "false")
    sys.modules.pop("dashboard.backend", None)
    return importlib.import_module("dashboard.backend")


def test_health_endpoint_is_public(monkeypatch):
    module = load_backend(monkeypatch)

    response = TestClient(module.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_requires_authentication(monkeypatch):
    module = load_backend(monkeypatch)

    response = TestClient(module.app).get("/api/status")

    assert response.status_code == 401


def test_login_creates_session_and_proxies_status(monkeypatch):
    module = load_backend(monkeypatch)
    module.ingestion_get = AsyncMock(return_value={"imports": 7, "points": 42})
    client = TestClient(module.app)

    login = client.post(
        "/api/auth/login",
        json={"password": "dashboard-test-password"},
    )
    status = client.get("/api/status")

    assert login.status_code == 200
    assert module.COOKIE_NAME in login.cookies
    assert status.status_code == 200
    assert status.json() == {"imports": 7, "points": 42}
    module.ingestion_get.assert_awaited_once_with("/v1/status")


def test_cookie_is_secure_by_default(monkeypatch):
    module = load_backend(monkeypatch)
    monkeypatch.delenv("DASHBOARD_COOKIE_SECURE")
    sys.modules.pop("dashboard.backend", None)
    module = importlib.import_module("dashboard.backend")

    response = TestClient(module.app).post(
        "/api/auth/login",
        json={"password": "dashboard-test-password"},
    )

    assert "Secure" in response.headers["set-cookie"]


def test_modified_and_expired_sessions_are_rejected(monkeypatch):
    module = load_backend(monkeypatch)
    token = module.create_session()

    assert not module.valid_session(f"{token}modified")
    monkeypatch.setattr(module.time, "time", lambda: int(token.split(".", 1)[0]) + 1)
    assert not module.valid_session(token)


def test_unicode_password_failure_returns_unauthorized(monkeypatch):
    module = load_backend(monkeypatch)

    response = TestClient(module.app).post(
        "/api/auth/login",
        json={"password": "contrase\u00f1a-incorrecta"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_unpaired_surrogate_password_is_rejected(monkeypatch):
    module = load_backend(monkeypatch)

    assert not asyncio.run(module.authenticate("unicode-client", "\ud800"))


def test_concurrent_failed_logins_are_rate_limited(monkeypatch):
    module = load_backend(monkeypatch)

    async def attempt_logins():
        return await asyncio.gather(
            *(module.authenticate("parallel-client", "wrong-password") for _ in range(6)),
            return_exceptions=True,
        )

    results = asyncio.run(attempt_logins())

    assert results.count(False) == 5
    errors = [result for result in results if isinstance(result, HTTPException)]
    assert len(errors) == 1
    assert errors[0].status_code == 429


def test_failed_login_clients_are_bounded(monkeypatch):
    module = load_backend(monkeypatch)
    monkeypatch.setattr(module, "MAX_LOGIN_CLIENTS", 2)

    assert not asyncio.run(module.authenticate("client-1", "wrong-password"))
    assert not asyncio.run(module.authenticate("client-2", "wrong-password"))
    assert not asyncio.run(module.authenticate("client-3", "wrong-password"))

    assert len(module.failed_logins) == 2
    assert "client-1" not in module.failed_logins
    assert "client-3" in module.failed_logins


def test_logout_revokes_copied_session(monkeypatch):
    module = load_backend(monkeypatch)
    module.ingestion_get = AsyncMock(return_value={"imports": 7, "points": 42})
    client = TestClient(module.app)
    login = client.post(
        "/api/auth/login",
        json={"password": "dashboard-test-password"},
    )
    copied_session = login.cookies[module.COOKIE_NAME]

    assert client.post("/api/auth/logout").status_code == 200
    client.cookies.set(module.COOKIE_NAME, copied_session)

    assert client.get("/api/status").status_code == 401


def test_session_capacity_invalidates_oldest_active_session(monkeypatch):
    module = load_backend(monkeypatch)
    monkeypatch.setattr(module, "MAX_ACTIVE_SESSIONS", 1)

    first = module.create_session()
    second = module.create_session()

    assert not module.valid_session(first)
    assert module.valid_session(second)


def test_metric_proxy_rejects_non_ascii_identifier(monkeypatch):
    module = load_backend(monkeypatch)
    client = TestClient(module.app)
    client.post(
        "/api/auth/login",
        json={"password": "dashboard-test-password"},
    )

    response = client.get("/api/metrics/m\u00e9trica?days=30")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid metric"}
