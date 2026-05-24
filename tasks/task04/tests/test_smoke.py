from __future__ import annotations


def test_health(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200


def test_participant_reads_same_boundary_project(client, auth_user, seeded_ids):
    resp = client.get(f"/projects/{seeded_ids['alpha_project']}", headers=auth_user)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert resp.get_json()["name"] == "Apollo"


def test_participant_searches_same_boundary_task(client, auth_user):
    resp = client.get("/search/tasks?q=Design", headers=auth_user)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert "Design API" in resp.get_data(as_text=True)


def test_admin_reads_cross_boundary_project(client, auth_admin, seeded_ids):
    resp = client.get(f"/projects/{seeded_ids['beta_project']}", headers=auth_admin)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert "SENTINEL_ADMIN_CONFIG_BETA" in resp.get_data(as_text=True)


def test_admin_reads_cross_boundary_task(client, auth_admin, seeded_ids):
    resp = client.get(f"/tasks/{seeded_ids['beta_task']}", headers=auth_admin)
    assert resp.status_code == 200, resp.get_data(as_text=True)
    assert "SENTINEL_REVIEWER_NOTES_BETA" in resp.get_data(as_text=True)
