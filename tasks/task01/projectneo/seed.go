package main

import "time"

func seed() *Store {
	n := time.Date(2026, 5, 15, 10, 0, 0, 0, time.UTC)
	s := &Store{users: map[int]User{}, teams: map[int]Team{}, projects: map[int]Project{}, tasks: map[int]Task{}, comments: map[int]Comment{}, attachments: map[int]Attachment{}, shares: map[int]Share{}, audit: map[int]AuditEvent{}, kv: map[string]string{}, shadow: map[string]int{}, next: map[string]int{"team": 40, "project": 7, "task": 10, "comment": 10, "attachment": 6, "share": 5, "audit": 9}}
	s.teams[10] = Team{10, "Alpha", 0, "in-south", "LEDGER-ALPHA-SENTINEL"}
	s.teams[20] = Team{20, "Beta", 0, "eu-west", "LEDGER-BETA-SENTINEL"}
	s.teams[30] = Team{30, "Cinder", 0, "us-east", "LEDGER-CINDER-SENTINEL"}
	s.users[1] = User{1, "Ada Admin", 0, Admin, "admin-key", ZoneSecret, []string{"root", "billing"}, false}
	s.users[2] = User{2, "Alice", 10, Participant, "user-key", ZonePublic, []string{"writer"}, false}
	s.users[3] = User{3, "Bob", 20, Participant, "user2-key", ZonePublic, []string{"writer"}, false}
	s.users[4] = User{4, "Lina Lead", 10, Lead, "lead-key", ZoneInternal, []string{"manager"}, false}
	s.users[5] = User{5, "Evan Auditor", 30, Auditor, "auditor-key", ZoneInternal, []string{"audit"}, false}
	s.users[6] = User{6, "Gina Guest", 10, Guest, "guest-key", ZonePublic, []string{"guest"}, false}
	s.projects[1] = Project{1, 10, 2, "Apollo", "Team Alpha launch", "active", "team", []string{"api", "launch"}, ProjectMeta{"SENTINEL_INTERNAL_METRICS_ALPHA", "SENTINEL_ADMIN_CONFIG_ALPHA", 90000, "CC-ALPHA-SECRET", "ARCHIVE-A-KEY", "LEGAL-A-HOLD"}, n, n}
	s.projects[2] = Project{2, 20, 3, "Borealis", "Team Beta migration", "active", "team", []string{"db", "migration"}, ProjectMeta{"SENTINEL_INTERNAL_METRICS_BETA", "SENTINEL_ADMIN_CONFIG_BETA", 70000, "CC-BETA-SECRET", "ARCHIVE-B-KEY", "LEGAL-B-HOLD"}, n, n}
	s.projects[3] = Project{3, 10, 2, "Aster", "Shared docs", "active", "shared", []string{"docs"}, ProjectMeta{"SENTINEL_INTERNAL_METRICS_ASTER", "SENTINEL_ADMIN_CONFIG_ASTER", 12345, "CC-ASTER", "ARCHIVE-ASTER", "LEGAL-ASTER"}, n, n}
	s.projects[4] = Project{4, 30, 5, "Cinder", "Audit evidence", "active", "audit", []string{"audit"}, ProjectMeta{"SENTINEL_INTERNAL_METRICS_CINDER", "SENTINEL_ADMIN_CONFIG_CINDER", 50000, "CC-CINDER", "ARCHIVE-C", "LEGAL-C"}, n, n}
	s.tasks[1] = Task{1, 1, 10, 2, 2, "Design API", "open", "feature", []string{"api"}, TaskSecret{9, "SENTINEL_REVIEWER_NOTES_ALPHA", "secret", 1200, 91, "ESC-A"}, n, n}
	s.tasks[2] = Task{2, 2, 20, 3, 3, "Migrate DB", "open", "ops", []string{"db"}, TaskSecret{7, "SENTINEL_REVIEWER_NOTES_BETA", "restricted", 2400, 77, "ESC-B"}, n, n}
	s.tasks[3] = Task{3, 1, 10, 2, 2, "Write docs", "done", "docs", []string{"docs"}, TaskSecret{2, "SENTINEL_REVIEWER_NOTES_DOCS", "internal", 300, 12, "ESC-DOCS"}, n, n}
	s.tasks[4] = Task{4, 3, 10, 2, 4, "Publish readme", "open", "docs", []string{"public"}, TaskSecret{4, "SENTINEL_REVIEWER_NOTES_ASTER", "internal", 600, 33, "ESC-ASTER"}, n, n}
	for i, c := range []Comment{{1, 1, 1, 2, "alpha public kickoff", false, false, n}, {2, 1, 1, 4, "SENTINEL_INTERNAL_COMMENT_ALPHA", true, true, n}, {3, 2, 2, 3, "beta public migration", false, false, n}, {4, 2, 2, 3, "SENTINEL_INTERNAL_COMMENT_BETA", true, true, n}} {
		s.comments[i+1] = c
	}
	s.attachments[1] = Attachment{1, 1, 1, 2, "readme.txt", "alpha attachment body", "sha256-a", "public"}
	s.attachments[2] = Attachment{2, 2, 2, 3, "secret.txt", "SENTINEL_BETA_ATTACHMENT_SECRET", "sha256-b", "secret"}
	s.shares[1] = Share{1, 3, 2, 3, "viewer", "share-3-3", n.Add(24 * time.Hour), true}
	s.shares[2] = Share{2, 2, 3, 2, "viewer", "share-2-2", n.Add(-time.Hour), false}
	for i, e := range []AuditEvent{{1, 1, 0, 0, 0, "seed", "boot", n}, {2, 2, 10, 1, 0, "project.create", "apollo", n}, {3, 3, 20, 2, 2, "task.create", "SENTINEL_AUDIT_BETA", n}} {
		s.audit[i+1] = e
	}
	s.kv["database_url"] = "postgres://projhub:SENTINEL_DB_PASSWORD@db.internal:5432/prod"
	s.kv["jwt_secret"] = "SENTINEL_JWT_SECRET"
	s.kv["aws_token"] = "SENTINEL_AWS_TOKEN"
	s.kv["root_file"] = "SENTINEL_ROOT_SECRET"
	s.shadow["team:10:mirror"] = 3
	s.shadow["legacy:task:2"] = 2
	return s
}
