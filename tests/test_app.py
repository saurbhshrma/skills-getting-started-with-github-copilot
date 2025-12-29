import os
import sys
import urllib.parse

import pytest
from fastapi.testclient import TestClient

# Ensure src is importable
HERE = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(HERE, "..", "src"))
sys.path.insert(0, SRC_DIR)

from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    # Reset in-memory activities before each test by reloading the module state
    # We mutate the existing dict to avoid import issues
    for v in activities.values():
        v["participants"] = [p for p in v.get("participants", []) if p not in ("teststudent@example.com", "already@school.edu")]
    yield


def test_root_redirect():
    client = TestClient(app)
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers.get("location") == "/static/index.html"


def test_get_activities():
    client = TestClient(app)
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data


def test_signup_success_and_prevent_double_signup():
    client = TestClient(app)
    email = "teststudent@example.com"
    activity_name = "Art Club"
    url = f"/activities/{urllib.parse.quote(activity_name)}/signup?email={urllib.parse.quote(email)}"

    # First signup should succeed
    r1 = client.post(url)
    assert r1.status_code == 200
    assert email in activities[activity_name]["participants"]

    # Second signup (same student) should fail with 400
    r2 = client.post(url)
    assert r2.status_code == 400


def test_signup_activity_not_found():
    client = TestClient(app)
    email = "someone@example.com"
    activity_name = "Nonexistent Club"
    url = f"/activities/{urllib.parse.quote(activity_name)}/signup?email={urllib.parse.quote(email)}"
    r = client.post(url)
    assert r.status_code == 404
