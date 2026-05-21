"""Read endpoints for tasks: get task row, download seed file, download golden file."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Response

from taskhub.auth import caller
from taskhub.db import TASKS, seed_dir

router = APIRouter(tags=["tasks"])


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


@router.get("/tasks/{task_id}")
def get_task(task_id: str, _current=Depends(caller)):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.get("/tasks/{task_id}/files/{filename:path}")
def get_task_file(task_id: str, filename: str, _current=Depends(caller)):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    path = os.path.join(seed_dir(task_id), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")


@router.get("/tasks/{task_id}/golden-file/{filename:path}")
def get_golden_file(task_id: str, filename: str, _current=Depends(caller)):
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    path = os.path.join(seed_dir(task_id), ".golden", filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")
