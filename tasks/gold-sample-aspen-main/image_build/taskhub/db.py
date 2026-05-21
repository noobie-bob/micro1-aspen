"""In-memory storage for the taskhub demo service.

Real eval platforms use Postgres + cloud blob storage. For the sample task we keep the
storage shape (`tasks`, `runs`, seed files on disk) but replace the
backing store with in-process dicts + a temp directory, so the service is
runnable inside a small Docker image with no external deps.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from typing import Any

TASKS: dict[str, dict[str, Any]] = {}
RUNS: dict[str, dict[str, Any]] = {}
SEED_ROOT: str = ""
ARTIFACT_ROOT: str = ""


def reset_state() -> None:
    """Wipe and re-create all storage. Called at app startup and from tests."""
    global SEED_ROOT, ARTIFACT_ROOT
    TASKS.clear()
    RUNS.clear()
    if SEED_ROOT and os.path.isdir(SEED_ROOT):
        shutil.rmtree(SEED_ROOT, ignore_errors=True)
    if ARTIFACT_ROOT and os.path.isdir(ARTIFACT_ROOT):
        shutil.rmtree(ARTIFACT_ROOT, ignore_errors=True)
    SEED_ROOT = tempfile.mkdtemp(prefix="taskhub-seeds-")
    ARTIFACT_ROOT = tempfile.mkdtemp(prefix="taskhub-artifacts-")


def new_id() -> str:
    return uuid.uuid4().hex


def seed_dir(task_id: str) -> str:
    path = os.path.join(SEED_ROOT, task_id)
    os.makedirs(path, exist_ok=True)
    return path


def artifact_dir(run_id: str) -> str:
    path = os.path.join(ARTIFACT_ROOT, run_id)
    os.makedirs(path, exist_ok=True)
    return path
