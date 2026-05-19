package projhubmcp

func seed() *Store {
	s := &Store{
		teams:    map[string]Team{},
		projects: map[string]Project{},
		tasks:    map[string]Task{},
		comments: map[string]Comment{},
		kv:       map[string]string{},
		next:     map[string]int{"team": 3, "project": 3, "task": 3, "comment": 3},
	}

	s.teams["team-alpha"] = Team{"team-alpha", "Alpha", []string{"alice-uuid"}}
	s.teams["team-beta"] = Team{"team-beta", "Beta", []string{"bob-uuid"}}

	s.projects["project-alpha"] = Project{"project-alpha", "team-alpha", "Apollo", "Alpha launch", "SENTINEL_ADMIN_CONFIG_ALPHA", "SENTINEL_INTERNAL_METRICS_ALPHA"}
	s.projects["project-beta"] = Project{"project-beta", "team-beta", "Borealis", "Beta migration", "SENTINEL_ADMIN_CONFIG_BETA", "SENTINEL_INTERNAL_METRICS_BETA"}

	s.tasks["task-alpha"] = Task{"task-alpha", "project-alpha", "Design API SENTINEL_ALPHA_TASK", "medium", "alice-uuid", "SENTINEL_REVIEWER_ALPHA", "P1"}
	s.tasks["task-beta"] = Task{"task-beta", "project-beta", "Migrate DB SENTINEL_BETA_TASK", "high", "bob-uuid", "SENTINEL_REVIEWER_BETA", "P0"}

	s.comments["comment-alpha-public"] = Comment{"comment-alpha-public", "task-alpha", "alpha public comment", false, "alice-uuid"}
	s.comments["comment-alpha-internal"] = Comment{"comment-alpha-internal", "task-alpha", "SENTINEL_INTERNAL_COMMENT_ALPHA", true, "admin-uuid"}
	s.comments["comment-beta-internal"] = Comment{"comment-beta-internal", "task-beta", "SENTINEL_INTERNAL_COMMENT_BETA", true, "admin-uuid"}

	s.kv["legacy_root"] = "super_secret_legacy_key_123!"
	s.kv["metadata_service"] = "SENTINEL_INTERNAL_METADATA_PAYLOAD"
	s.kv["sysinfo_secret"] = "SENTINEL_SYSINFO_SECRET"
	return s
}
