from __future__ import annotations


def _minimal_task_payload():
    return {
        "name": "demo",
        "public_readme": "hello",
        "task_config_b64": "",
        "test_patch_b64": "",
        "gold_patch_b64": "",
        "hidden_seed_files": [],
        "extra_seed_files": {},
    }


def test_health(client):
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code != 500


def test_admin_creates_task(client, auth_admin):
    resp = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload())
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"]


def test_participant_creates_a_run(client, auth_admin, auth_user):
    task = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload()).json()
    resp = client.post(
        "/runs",
        headers=auth_user,
        json={"task_id": task["id"], "model": "claude-opus-4-7"},
    )
    assert resp.status_code == 200, resp.text


def test_participant_forks_a_task(client, auth_admin, auth_user):
    """Participants legitimately fork (duplicate) tasks."""
    task = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload()).json()
    resp = client.post(
        f"/tasks/{task['id']}/duplicate",
        headers=auth_user,
        json={"new_name": "alice-fork"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] != task["id"]


def test_participant_shares_their_own_fork(client, auth_admin, auth_user):
    """Participants share their own forks with teammates."""
    task = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload()).json()
    fork = client.post(f"/tasks/{task['id']}/duplicate", headers=auth_user, json={}).json()
    resp = client.post(f"/tasks/{fork['id']}/share", headers=auth_user)
    assert resp.status_code == 200, resp.text


def test_participant_exports_their_own_fork(client, auth_admin, auth_user):
    """Participants export their own forks for backup."""
    task = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload()).json()
    fork = client.post(f"/tasks/{task['id']}/duplicate", headers=auth_user, json={}).json()
    resp = client.get(f"/tasks/{fork['id']}/export", headers=auth_user)
    assert resp.status_code == 200, resp.text


def test_participant_renames_their_own_fork(client, auth_admin, auth_user):
    """Participants rename their own forks."""
    task = client.post("/coding-tasks", headers=auth_admin, json=_minimal_task_payload()).json()
    fork = client.post(f"/tasks/{task['id']}/duplicate", headers=auth_user, json={}).json()
    resp = client.patch(f"/tasks/{fork['id']}", headers=auth_user, json={"name": "renamed"})
    assert resp.status_code == 200, resp.text
