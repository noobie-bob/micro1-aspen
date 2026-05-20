from dataclasses import dataclass, field
from typing import Any


@dataclass
class Caller:
    role: str
    user_id: str


@dataclass
class Team:
    id: str
    name: str
    member_ids: list[str] = field(default_factory=list)


@dataclass
class Project:
    id: str
    team_id: str
    name: str
    description: str = ""
    admin_config: str = ""
    internal_metrics: str = ""


@dataclass
class Task:
    id: str
    project_id: str
    title: str
    priority: str = "medium"
    created_by: str = ""
    reviewer_notes: str = ""
    internal_priority: str = ""


@dataclass
class Comment:
    id: str
    task_id: str
    body: str
    internal: bool = False
    author: str = ""


@dataclass
class Store:
    teams: dict[str, Team] = field(default_factory=dict)
    projects: dict[str, Project] = field(default_factory=dict)
    tasks: dict[str, Task] = field(default_factory=dict)
    comments: dict[str, Comment] = field(default_factory=dict)
    kv: dict[str, str] = field(default_factory=dict)
    next_ids: dict[str, int] = field(default_factory=lambda: {"team": 3, "project": 3, "task": 3, "comment": 3})

    def next_id(self, prefix: str) -> str:
        value = self.next_ids.get(prefix, 1)
        self.next_ids[prefix] = value + 1
        return f"{prefix}-{value}"


def asdict_public(obj: Any) -> dict[str, Any]:
    return dict(obj.__dict__)
