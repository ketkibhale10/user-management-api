import os
import tempfile

# Must be set before the app is imported
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app

P = "/api/v1"
ADMIN = {"username": "admin@example.com", "password": "Admin@12345"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client, creds):
    r = client.post(f"{P}/auth/login", data=creds)
    assert r.status_code == 200, r.text
    return r.json()


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_errors(client):
    body = {"email": "alice@example.com", "full_name": "Alice", "password": "Alice@1234"}
    r = client.post(f"{P}/auth/register", json=body)
    assert r.status_code == 201 and r.json()["role"] == "user" and "password" not in r.json()
    assert client.post(f"{P}/auth/register", json=body).status_code == 409
    assert client.post(f"{P}/auth/register", json={**body, "email": "b@x.com", "password": "123"}).status_code == 422
    assert client.post(f"{P}/auth/login", data={"username": "alice@example.com", "password": "bad"}).status_code == 401


def test_tokens(client):
    tokens = login(client, {"username": "alice@example.com", "password": "Alice@1234"})
    assert client.get(f"{P}/users/me", headers=hdr(tokens["access_token"])).status_code == 200
    assert client.get(f"{P}/users/me").status_code == 401
    # refresh token can't be used as access token, and vice versa
    assert client.get(f"{P}/users/me", headers=hdr(tokens["refresh_token"])).status_code == 401
    assert client.post(f"{P}/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401
    r = client.post(f"{P}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200 and "access_token" in r.json()


def test_rbac(client):
    user = login(client, {"username": "alice@example.com", "password": "Alice@1234"})
    h = hdr(user["access_token"])
    me = client.get(f"{P}/users/me", headers=h).json()
    assert client.get(f"{P}/users", headers=h).status_code == 403
    assert client.get(f"{P}/users/1", headers=h).status_code == 403
    assert client.get(f"{P}/users/{me['id']}", headers=h).status_code == 200
    assert client.patch(f"{P}/users/{me['id']}", json={"role": "admin"}, headers=h).status_code == 403
    assert client.patch(f"{P}/users/{me['id']}", json={"full_name": "Alice B"}, headers=h).json()["full_name"] == "Alice B"
    assert client.delete(f"{P}/users/1", headers=h).status_code == 403


def test_admin_crud_and_pagination(client):
    h = hdr(login(client, ADMIN)["access_token"])
    for i in range(7):
        r = client.post(f"{P}/users", headers=h, json={"email": f"u{i}@x.com", "full_name": f"U{i}", "password": "Passw0rd!"})
        assert r.status_code == 201
    page = client.get(f"{P}/users?limit=3&offset=0", headers=h).json()
    assert len(page["items"]) == 3 and page["total"] == 9  # admin + alice + 7
    page2 = client.get(f"{P}/users?limit=3&offset=3", headers=h).json()
    assert {u["id"] for u in page["items"]}.isdisjoint({u["id"] for u in page2["items"]})
    assert client.get(f"{P}/users?limit=3&offset=100", headers=h).json()["items"] == []
    assert client.get(f"{P}/users?limit=0", headers=h).status_code == 422
    assert client.get(f"{P}/users?limit=500", headers=h).status_code == 422
    assert client.get(f"{P}/users?offset=-1", headers=h).status_code == 422
    assert client.get(f"{P}/users?search=u1@", headers=h).json()["total"] == 1

    uid = page2["items"][0]["id"]
    assert client.patch(f"{P}/users/{uid}", json={"is_active": False}, headers=h).json()["is_active"] is False
    assert client.delete(f"{P}/users/{uid}", headers=h).status_code == 204
    assert client.delete(f"{P}/users/{uid}", headers=h).status_code == 404
    assert client.delete(f"{P}/users/1", headers=h).status_code == 400  # admin can't delete self


def test_deactivated_login_and_cors_and_headers(client):
    h = hdr(login(client, ADMIN)["access_token"])
    client.post(f"{P}/users", headers=h, json={"email": "off@x.com", "full_name": "Off", "password": "Passw0rd!"})
    uid = client.get(f"{P}/users?search=off@x.com", headers=h).json()["items"][0]["id"]
    client.patch(f"{P}/users/{uid}", json={"is_active": False}, headers=h)
    assert client.post(f"{P}/auth/login", data={"username": "off@x.com", "password": "Passw0rd!"}).status_code == 403

    r = client.get("/")
    assert "x-request-id" in r.headers and "x-process-time-ms" in r.headers
    pre = client.options("/", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert pre.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.options("/", headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in bad.headers
