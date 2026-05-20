from models import Comment, Project, Store, Task, Team


def new_store() -> Store:
    store = Store()

    store.teams["team-alpha"] = Team("team-alpha", "Alpha", ["alice-uuid"])
    store.teams["team-beta"] = Team("team-beta", "Beta", ["bob-uuid"])

    store.projects["project-alpha"] = Project(
        id="project-alpha",
        team_id="team-alpha",
        name="Apollo",
        description="Alpha launch",
        admin_config="SENTINEL_ADMIN_CONFIG_ALPHA",
        internal_metrics="SENTINEL_INTERNAL_METRICS_ALPHA",
    )
    store.projects["project-beta"] = Project(
        id="project-beta",
        team_id="team-beta",
        name="Borealis",
        description="Beta migration",
        admin_config="SENTINEL_ADMIN_CONFIG_BETA",
        internal_metrics="SENTINEL_INTERNAL_METRICS_BETA",
    )

    store.tasks["task-alpha"] = Task(
        id="task-alpha",
        project_id="project-alpha",
        title="Design API SENTINEL_ALPHA_TASK",
        priority="medium",
        created_by="alice-uuid",
        reviewer_notes="SENTINEL_REVIEWER_ALPHA",
        internal_priority="P1",
    )
    store.tasks["task-beta"] = Task(
        id="task-beta",
        project_id="project-beta",
        title="Migrate DB SENTINEL_BETA_TASK",
        priority="high",
        created_by="bob-uuid",
        reviewer_notes="SENTINEL_REVIEWER_BETA",
        internal_priority="P0",
    )

    store.comments["comment-alpha-public"] = Comment(
        id="comment-alpha-public",
        task_id="task-alpha",
        body="alpha public comment",
        internal=False,
        author="alice-uuid",
    )
    store.comments["comment-alpha-internal"] = Comment(
        id="comment-alpha-internal",
        task_id="task-alpha",
        body="SENTINEL_INTERNAL_COMMENT_ALPHA",
        internal=True,
        author="admin-uuid",
    )
    store.comments["comment-beta-internal"] = Comment(
        id="comment-beta-internal",
        task_id="task-beta",
        body="SENTINEL_INTERNAL_COMMENT_BETA",
        internal=True,
        author="admin-uuid",
    )

    store.kv["legacy_root"] = "super_secret_legacy_key_123!"
    store.kv["metadata_service"] = "SENTINEL_INTERNAL_METADATA_PAYLOAD"
    store.kv["sysinfo_secret"] = "SENTINEL_SYSINFO_SECRET"
    return store
