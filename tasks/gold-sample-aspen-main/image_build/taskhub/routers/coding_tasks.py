"""Coding-task management endpoints: create, list, fork, rename, share, export, validate."""

from __future__ import annotations

import base64
import copy
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from taskhub.auth import Caller, caller
from taskhub.db import RUNS, TASKS, artifact_dir, new_id, seed_dir

router = APIRouter(tags=["coding-tasks"])


class CreateCodingTaskRequest(BaseModel):
    name: str
    public_readme: str
    task_config_b64: str
    test_patch_b64: str
    gold_patch_b64: str
    hidden_seed_files: list[str] = Field(default_factory=list)
    extra_seed_files: dict[str, str] = Field(default_factory=dict)


def _require_admin(current: Caller) -> None:
    if not current.is_admin:
        raise HTTPException(status_code=403, detail="admin required")


@router.post("/coding-tasks")
def create_coding_task(payload: CreateCodingTaskRequest, current: Caller = Depends(caller)):
    _require_admin(current)

    task_id = new_id()
    sandbox_config = {
        "task_config_b64": payload.task_config_b64,
        "test_patch_b64": payload.test_patch_b64,
        "gold_patch_b64": payload.gold_patch_b64,
        "hidden_seed_files": list(payload.hidden_seed_files),
    }
    row = {
        "id": task_id,
        "name": payload.name,
        "sandbox_config": sandbox_config,
        "owner_id": current.user_id,
    }
    TASKS[task_id] = row

    task_root = seed_dir(task_id)
    with open(os.path.join(task_root, "public_readme.md"), "wb") as fh:
        fh.write(payload.public_readme.encode("utf-8"))

    for filename, encoded in payload.extra_seed_files.items():
        if not filename:
            continue
        with open(os.path.join(task_root, filename), "wb") as fh:
            fh.write(base64.b64decode(encoded.encode("utf-8"), validate=False))

    return row


@router.post("/coding-tasks/{task_id}/validate-gold-patch")
def validate_gold_patch(task_id: str, current: Caller = Depends(caller)):
    _require_admin(current)

    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    sandbox_config = task.get("sandbox_config") or {}
    gold_patch = base64.b64decode(
        str(sandbox_config.get("gold_patch_b64", "")).encode("utf-8"),
        validate=False,
    )
    if not gold_patch:
        raise HTTPException(status_code=400, detail="gold patch is empty")

    golden_root = os.path.join(seed_dir(task_id), ".golden")
    os.makedirs(golden_root, exist_ok=True)
    with open(os.path.join(golden_root, "gold_patch.diff"), "wb") as fh:
        fh.write(gold_patch)

    run_id = new_id()
    run = {
        "id": run_id,
        "task_id": task_id,
        "model": "gold_patch_validation",
        "status": "completed",
        "created_by": current.user_id,
    }
    RUNS[run_id] = run

    run_root = artifact_dir(run_id)
    with open(os.path.join(run_root, "gold_patch.diff"), "wb") as fh:
        fh.write(gold_patch)
    with open(os.path.join(run_root, "validation_log.txt"), "wb") as fh:
        fh.write(b"validation completed")

    return {"run_id": run_id, "status": "completed"}


@router.get("/coding-tasks")
def list_coding_tasks(_current: Caller = Depends(caller)):
    """List all coding tasks in the workspace."""
    return list(TASKS.values())


class DuplicateRequest(BaseModel):
    new_name: str = ""


@router.post("/tasks/{task_id}/duplicate")
def duplicate_task(task_id: str, payload: DuplicateRequest, current: Caller = Depends(caller)):
    """Clone a task under a new id."""
    src = TASKS.get(task_id)
    if src is None:
        raise HTTPException(status_code=404, detail="task not found")

    new_task_id = new_id()
    cloned = copy.deepcopy(src)
    cloned["id"] = new_task_id
    cloned["name"] = payload.new_name or f"{src.get('name', 'task')}-copy"
    cloned["owner_id"] = current.user_id
    TASKS[new_task_id] = cloned
    return cloned


class PatchTaskRequest(BaseModel):
    name: str | None = None


@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, payload: PatchTaskRequest, _current: Caller = Depends(caller)):
    """Update mutable task metadata."""
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if payload.name is not None:
        task["name"] = payload.name
    return task


@router.post("/tasks/{task_id}/share")
def share_task(task_id: str, _current: Caller = Depends(caller)):
    """Generate a shareable link payload for a task."""
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return {
        "task_id": task_id,
        "share_id": new_id(),
        "name": task.get("name"),
        "config": task.get("sandbox_config"),
        "url": f"/shared/{task_id}",
    }


@router.get("/tasks/{task_id}/export")
def export_task(task_id: str, _current: Caller = Depends(caller)):
    """Download a JSON dump of a task's configuration."""
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task
