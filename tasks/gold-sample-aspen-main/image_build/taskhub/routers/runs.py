"""Run management endpoints: create runs, download artifacts, list per-task runs."""

from __future__ import annotations

import io
import os
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from taskhub.auth import caller
from taskhub.db import RUNS, TASKS, artifact_dir, new_id

router = APIRouter(tags=["runs"])


class CreateRunRequest(BaseModel):
    task_id: str
    model: str


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


@router.post("/runs")
def create_run(payload: CreateRunRequest, current=Depends(caller)):
    if payload.task_id not in TASKS:
        raise HTTPException(status_code=404, detail="task not found")

    run_id = new_id()
    run = {
        "id": run_id,
        "task_id": payload.task_id,
        "model": payload.model,
        "status": "completed",
        "created_by": current.user_id,
    }
    RUNS[run_id] = run

    run_root = artifact_dir(run_id)
    with open(os.path.join(run_root, "ordinary_output.txt"), "wb") as fh:
        fh.write(b"ordinary run completed")

    return run


@router.get("/runs/{run_id}/artifacts/{filename:path}")
def get_run_artifact(run_id: str, filename: str, _current=Depends(caller)):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    path = os.path.join(artifact_dir(run_id), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="artifact not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")


@router.get("/runs/{run_id}/artifacts-zip")
def get_run_artifacts_zip(run_id: str, _current=Depends(caller)):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        root = artifact_dir(run_id)
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if os.path.isfile(path):
                zf.writestr(name, _read_bytes(path))
    return Response(content=buf.getvalue(), media_type="application/zip")


@router.get("/tasks/{task_id}/runs")
def list_runs_for_task(task_id: str, _current=Depends(caller)):
    """List all runs for a task."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="task not found")
    return [r for r in RUNS.values() if r.get("task_id") == task_id]
