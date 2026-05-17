"""Cross-team data isolation tests.

These tests verify that non-admin participants cannot access or mutate
resources belonging to teams they are not members of.
"""

from __future__ import annotations

import base64
import io
import zipfile


def _create_project(client, auth_admin, team_id, name="proj", **extra):
    payload = {"team_id": team_id, "name": name, "description": "test"}
    payload.update(extra)
    resp = client.post("/projects", headers=auth_admin, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _create_task(client, headers, project_id, title="task", **extra):
    payload = {"title": title, "description": "test task", "priority": "medium"}
    payload.update(extra)
    resp = client.post(f"/projects/{project_id}/tasks", headers=headers, json=payload)
    assert resp.status_code == 200
    return resp.get_json()


def _zip_entries(payload: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(payload)) as zip_file:
        return {name: zip_file.read(name) for name in zip_file.namelist()}


# ── Cross-team project listing ──────────────────────────────────────────────

def test_list_projects_returns_only_own_team(client, auth_admin, auth_user, auth_user2, two_teams):
    """Non-admin listing /projects must only surface their own team's projects."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-secret")
    beta_proj  = _create_project(client, auth_admin, two_teams["beta"],  name="beta-secret")

    # Alice (team-alpha) must see her project but NOT beta's
    resp = client.get("/projects", headers=auth_user)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.get_json()]
    assert alpha_proj["id"] in ids, "own-team project must be visible"
    assert beta_proj["id"] not in ids, "cross-team project must be hidden"

    # Bob (team-beta) must see his project but NOT alpha's
    resp2 = client.get("/projects", headers=auth_user2)
    assert resp2.status_code == 200
    ids2 = [p["id"] for p in resp2.get_json()]
    assert beta_proj["id"] in ids2
    assert alpha_proj["id"] not in ids2, "Bob must not see team-alpha projects"


# ── Cross-team project detail ───────────────────────────────────────────────

def test_get_project_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin reading /projects/<id> for a cross-team project must get 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-classified")

    resp = client.get(f"/projects/{beta_proj['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /projects/{{id}} must return 403 or 404, got {resp.status_code}"
    )


def test_get_project_own_team_allowed(client, auth_admin, auth_user, two_teams):
    """Same-team read must still work (anti-overblock)."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-readable")
    resp = client.get(f"/projects/{alpha_proj['id']}", headers=auth_user)
    assert resp.status_code == 200


# ── Cross-team task listing ─────────────────────────────────────────────────

def test_list_tasks_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin /projects/<id>/tasks on a cross-team project must return 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    _create_task(client, auth_admin, beta_proj["id"], title="secret-task")

    resp = client.get(f"/projects/{beta_proj['id']}/tasks", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team task list must return 403/404, got {resp.status_code}"
    )


# ── Cross-team task read / write / delete ──────────────────────────────────

def test_get_task_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin GET /tasks/<id> for a cross-team task must return 403/404."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"], title="hidden-task")

    resp = client.get(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert resp.status_code in (403, 404), (
        f"cross-team GET /tasks/{{id}} must return 403/404, got {resp.status_code}"
    )


def test_patch_and_delete_cross_team_forbidden(client, auth_admin, auth_user, two_teams):
    """Non-admin must not mutate (PATCH) or destroy (DELETE) a cross-team task."""
    beta_proj = _create_project(client, auth_admin, two_teams["beta"])
    beta_task = _create_task(client, auth_admin, beta_proj["id"])

    patch_resp = client.patch(f"/tasks/{beta_task['id']}", headers=auth_user,
                              json={"title": "hacked"})
    assert patch_resp.status_code == 403, (
        f"cross-team PATCH must return 403, got {patch_resp.status_code}"
    )

    delete_resp = client.delete(f"/tasks/{beta_task['id']}", headers=auth_user)
    assert delete_resp.status_code == 403, (
        f"cross-team DELETE must return 403, got {delete_resp.status_code}"
    )


def test_attachment_channels_preserve_same_team_access_but_hide_cross_team_files(
    client, auth_admin, auth_user, two_teams
):
    """Attachment channels must work same-team while hiding foreign filenames and bytes."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-files")
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-files")
    alpha_task = _create_task(client, auth_admin, alpha_proj["id"], title="alpha-files-task")
    beta_task = _create_task(client, auth_admin, beta_proj["id"], title="beta-files-task")

    own_name = "own-note.txt"
    own_bytes = b"ALPHA_ATTACHMENT_OK"
    foreign_name = "beta-secret.txt"
    foreign_bytes = b"TYPEB_ATTACHMENT_SECRET"

    own_upload = client.post(
        f"/tasks/{alpha_task['id']}/attachments",
        headers=auth_user,
        json={
            "filename": own_name,
            "content_b64": base64.b64encode(own_bytes).decode(),
        },
    )
    assert own_upload.status_code == 200

    foreign_upload = client.post(
        f"/tasks/{beta_task['id']}/attachments",
        headers=auth_admin,
        json={
            "filename": foreign_name,
            "content_b64": base64.b64encode(foreign_bytes).decode(),
        },
    )
    assert foreign_upload.status_code == 200

    own_list = client.get(f"/tasks/{alpha_task['id']}/attachments", headers=auth_user)
    assert own_list.status_code == 200
    assert own_name in own_list.get_json()

    own_download = client.get(
        f"/tasks/{alpha_task['id']}/attachments/{own_name}",
        headers=auth_user,
    )
    assert own_download.status_code == 200
    assert own_bytes == own_download.data

    own_zip = client.get(f"/tasks/{alpha_task['id']}/attachments-zip", headers=auth_user)
    assert own_zip.status_code == 200
    own_entries = _zip_entries(own_zip.data)
    assert own_name in own_entries
    assert own_entries[own_name] == own_bytes

    foreign_list = client.get(f"/tasks/{beta_task['id']}/attachments", headers=auth_user)
    if foreign_list.status_code == 200:
        assert foreign_name not in foreign_list.get_json(), (
            "cross-team attachment list disclosed a foreign filename"
        )
    else:
        assert foreign_list.status_code in (403, 404)

    foreign_download = client.get(
        f"/tasks/{beta_task['id']}/attachments/{foreign_name}",
        headers=auth_user,
    )
    if foreign_download.status_code == 200:
        assert foreign_bytes not in foreign_download.data, (
            "cross-team attachment download disclosed foreign bytes"
        )
    else:
        assert foreign_download.status_code in (403, 404)

    foreign_zip = client.get(f"/tasks/{beta_task['id']}/attachments-zip", headers=auth_user)
    if foreign_zip.status_code == 200:
        foreign_entries = _zip_entries(foreign_zip.data)
        assert foreign_name not in foreign_entries, (
            "cross-team attachment bundle disclosed a foreign filename"
        )
        assert all(foreign_bytes not in body for body in foreign_entries.values()), (
            "cross-team attachment bundle disclosed foreign file bytes"
        )
    else:
        assert foreign_zip.status_code in (403, 404)


def test_workflow_actions_allow_same_team_updates_but_leave_cross_team_state_unchanged(
    client, auth_admin, auth_user, two_teams
):
    """Workflow actions must work same-team and leave foreign-task state unchanged."""
    alpha_proj = _create_project(client, auth_admin, two_teams["alpha"], name="alpha-workflow")
    beta_proj = _create_project(client, auth_admin, two_teams["beta"], name="beta-workflow")
    alpha_task = _create_task(client, auth_admin, alpha_proj["id"], title="alpha-workflow-task")
    beta_task = _create_task(client, auth_admin, beta_proj["id"], title="beta-workflow-task")

    same_assign = client.post(
        f"/tasks/{alpha_task['id']}/assign",
        headers=auth_user,
        json={"user_id": "alice-uuid"},
    )
    assert same_assign.status_code == 200

    same_transition = client.post(
        f"/tasks/{alpha_task['id']}/transition",
        headers=auth_user,
        json={"status": "review"},
    )
    assert same_transition.status_code == 200

    same_state = client.get(f"/tasks/{alpha_task['id']}", headers=auth_admin)
    assert same_state.status_code == 200
    same_data = same_state.get_json()
    assert same_data["assigned_to"] == "alice-uuid"
    assert same_data["status"] == "review"

    before = client.get(f"/tasks/{beta_task['id']}", headers=auth_admin)
    assert before.status_code == 200
    original = before.get_json()

    cross_assign = client.post(
        f"/tasks/{beta_task['id']}/assign",
        headers=auth_user,
        json={"user_id": "alice-uuid"},
    )
    if cross_assign.status_code == 200:
        assert cross_assign.get_json().get("assigned_to") == original.get("assigned_to"), (
            "cross-team assign mutated foreign task ownership state"
        )
    else:
        assert cross_assign.status_code in (403, 404)

    cross_transition = client.post(
        f"/tasks/{beta_task['id']}/transition",
        headers=auth_user,
        json={"status": "done"},
    )
    if cross_transition.status_code == 200:
        assert cross_transition.get_json().get("status") == original.get("status"), (
            "cross-team transition mutated foreign task workflow state"
        )
    else:
        assert cross_transition.status_code in (403, 404)

    after = client.get(f"/tasks/{beta_task['id']}", headers=auth_admin)
    assert after.status_code == 200
    current = after.get_json()
    assert current.get("assigned_to") == original.get("assigned_to")
    assert current.get("status") == original.get("status")
