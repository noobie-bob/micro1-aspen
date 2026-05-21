from fastapi import FastAPI

from taskhub.db import reset_state
from taskhub.routers import coding_tasks, runs, tasks


def create_app() -> FastAPI:
    reset_state()
    app = FastAPI(title="taskhub")
    app.include_router(coding_tasks.router)
    app.include_router(tasks.router)
    app.include_router(runs.router)
    return app


app = create_app()
