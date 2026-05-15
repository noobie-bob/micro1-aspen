"""In-memory database for mcp_server."""
import uuid

TEAMS: dict[str, dict] = {}
PROJECTS: dict[str, dict] = {}
TASKS: dict[str, dict] = {}
COMMENTS: dict[str, dict] = {}

def reset_state() -> None:
    """Wipe all storage. Called at app startup and from tests."""
    TEAMS.clear()
    PROJECTS.clear()
    TASKS.clear()
    COMMENTS.clear()

def generate_id() -> str:
    return str(uuid.uuid4())
