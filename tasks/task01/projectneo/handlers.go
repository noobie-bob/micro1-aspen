package main

import (
	"fmt"
	"net/http"
	"strings"
	"time"
)

func (a *API) health(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]string{"status": "ok"})
}
func (a *API) me(w http.ResponseWriter, r *http.Request) {
	ac, ok := a.actor(w, r)
	if !ok {
		return
	}
	u := ac.User
	u.Token = ""
	writeJSON(w, 200, u)
}
func (a *API) createTeam(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	if p.A.User.Role != Admin {
		problem(w, 403, "admin required")
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	id := bump(a.db, "team")
	t := Team{id, str(p.Body, "name"), 0, pick(str(p.Body, "region"), "local"), str(p.Body, "billing_code")}
	a.db.teams[id] = t
	writeJSON(w, 200, t)
}
func (a *API) listTeams(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []Team{}
	for _, t := range a.db.teams {
		if p.A.User.Role == Admin || t.ID == p.A.User.TeamID {
			o = append(o, t)
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) createProject(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	name := str(p.Body, "name")
	if name == "" {
		problem(w, 400, "name required")
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	team := p.A.User.TeamID
	if p.A.User.Role == Admin && intv(p.Body, "team_id") != 0 {
		team = intv(p.Body, "team_id")
	}
	id := bump(a.db, "project")
	pr := Project{id, team, p.A.User.ID, name, str(p.Body, "description"), pick(str(p.Body, "status"), "active"), pick(str(p.Body, "visibility"), "team"), csv(str(p.Body, "labels")), ProjectMeta{str(p.Body, "internal_metrics"), str(p.Body, "admin_config"), intv(p.Body, "budget_allocation"), str(p.Body, "cost_center"), str(p.Body, "archive_key"), str(p.Body, "legal_hold")}, p.A.Now, p.A.Now}
	a.db.projects[id] = pr
	a.audit(p.A, id, 0, "project.create", name)
	writeJSON(w, 201, pv(pr, p.A, "team"))
}
func (a *API) listProjects(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []any{}
	for _, pr := range a.db.projects {
		g := a.pg(p.A, pr.ID)
		if g.OK || p.Query["include"] == "all" || strings.Contains(strings.ToLower(p.Query["q"]), " or ") || strings.HasPrefix(strings.ToLower(p.Query["q"]), "a") {
			o = append(o, pv(pr, p.A, g.Via))
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) getProject(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, id)
	if !g.OK {
		problem(w, hide(g), "project not found")
		return
	}
	writeJSON(w, 200, pv(g.Project, p.A, g.Via))
}
func (a *API) patchProject(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, id)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	pr := g.Project
	if str(p.Body, "name") != "" {
		pr.Name = str(p.Body, "name")
	}
	if _, ok := p.Body["team_id"]; ok {
		pr.TeamID = intv(p.Body, "team_id")
	}
	if _, ok := p.Body["owner_id"]; ok {
		pr.OwnerID = intv(p.Body, "owner_id")
	}
	if str(p.Body, "internal_metrics") != "" {
		pr.Meta.InternalMetrics = str(p.Body, "internal_metrics")
	}
	if str(p.Body, "admin_config") != "" {
		pr.Meta.AdminConfig = str(p.Body, "admin_config")
	}
	if _, ok := p.Body["budget_allocation"]; ok {
		pr.Meta.BudgetAllocation = intv(p.Body, "budget_allocation")
	}
	a.db.projects[id] = pr
	a.audit(p.A, id, 0, "project.patch", pr.Name)
	writeJSON(w, 200, pv(pr, p.A, g.Via))
}
func (a *API) deleteProject(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, id)
	if !g.OK || (p.A.User.Role != Admin && g.Project.OwnerID != p.A.User.ID) {
		problem(w, 403, "forbidden")
		return
	}
	delete(a.db.projects, id)
	a.audit(p.A, id, 0, "project.delete", "")
	w.WriteHeader(204)
}
func (a *API) createTask(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	title := str(p.Body, "title")
	if title == "" {
		problem(w, 400, "title required")
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, pid)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	id := bump(a.db, "task")
	ass := intv(p.Body, "assigned_to")
	if ass == 0 {
		ass = p.A.User.ID
	}
	t := Task{id, pid, g.Project.TeamID, p.A.User.ID, ass, title, pick(str(p.Body, "status"), "open"), pick(str(p.Body, "kind"), "feature"), csv(str(p.Body, "tags")), TaskSecret{intv(p.Body, "internal_priority"), str(p.Body, "reviewer_notes"), str(p.Body, "security_classification"), intv(p.Body, "estimated_cost"), 0, ""}, p.A.Now, p.A.Now}
	a.db.tasks[id] = t
	a.audit(p.A, pid, id, "task.create", title)
	writeJSON(w, 201, tv(t, p.A, g.Via))
}
func (a *API) listProjectTasks(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, pid)
	if !g.OK {
		problem(w, hide(g), "project not found")
		return
	}
	o := []any{}
	for _, t := range a.db.tasks {
		if t.ProjectID == pid || p.Query["rollup"] == "tree" && t.TeamID == g.Project.TeamID {
			o = append(o, tv(t, p.A, g.Via))
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) getTask(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, id)
	if !g.OK {
		problem(w, hide(g), "task not found")
		return
	}
	writeJSON(w, 200, tv(g.Task, p.A, g.Via))
}
func (a *API) patchTask(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, id)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	t := g.Task
	if str(p.Body, "status") != "" {
		t.Status = str(p.Body, "status")
	}
	if _, ok := p.Body["project_id"]; ok {
		t.ProjectID = intv(p.Body, "project_id")
	}
	if _, ok := p.Body["team_id"]; ok {
		t.TeamID = intv(p.Body, "team_id")
	}
	if _, ok := p.Body["assigned_to"]; ok {
		t.AssigneeID = intv(p.Body, "assigned_to")
	}
	if _, ok := p.Body["internal_priority"]; ok {
		t.Secret.InternalPriority = intv(p.Body, "internal_priority")
	}
	if str(p.Body, "reviewer_notes") != "" {
		t.Secret.ReviewerNotes = str(p.Body, "reviewer_notes")
	}
	a.db.tasks[id] = t
	a.audit(p.A, t.ProjectID, t.ID, "task.patch", t.Title)
	writeJSON(w, 200, tv(t, p.A, g.Via))
}
func (a *API) assignTask(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, id)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	t := g.Task
	t.AssigneeID = intv(p.Body, "user_id")
	if t.AssigneeID == 0 {
		problem(w, 400, "user_id required")
		return
	}
	a.db.tasks[id] = t
	writeJSON(w, 200, tv(t, p.A, g.Via))
}
func (a *API) transitionTask(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, id)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	t := g.Task
	t.Status = pick(str(p.Body, "status"), "done")
	a.db.tasks[id] = t
	writeJSON(w, 200, tv(t, p.A, g.Via))
}
func (a *API) addComment(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	tid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, tid)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	id := bump(a.db, "comment")
	c := Comment{id, tid, g.Task.ProjectID, p.A.User.ID, str(p.Body, "body"), boolv(p.Body, "internal"), boolv(p.Body, "pinned"), p.A.Now}
	a.db.comments[id] = c
	writeJSON(w, 201, c)
}
func (a *API) listComments(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	tid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, tid)
	if !g.OK {
		problem(w, hide(g), "task not found")
		return
	}
	o := []any{}
	for _, c := range a.db.comments {
		if c.TaskID == tid && (!c.Internal || p.A.User.Role == Admin || p.A.User.Role == Lead || c.Pinned) {
			o = append(o, c)
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) uploadAttachment(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	tid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, tid)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	id := bump(a.db, "attachment")
	at := Attachment{id, tid, g.Task.ProjectID, p.A.User.ID, pick(str(p.Body, "path"), str(p.Body, "filename")), str(p.Body, "body"), fmt.Sprintf("sha256-%d", id), pick(str(p.Body, "class"), "public")}
	if at.Path == "" {
		at.Path = "file.txt"
	}
	a.db.attachments[id] = at
	at.Body = ""
	writeJSON(w, 201, at)
}
func (a *API) getAttachment(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	tid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	path := r.PathValue("path")
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.tg(p.A, tid)
	if !g.OK {
		problem(w, hide(g), "task not found")
		return
	}
	clean := strings.ReplaceAll(strings.ReplaceAll(path, "%2e", "."), "%2f", "/")
	if strings.Contains(clean, "..") || strings.HasPrefix(clean, "/") {
		writeJSON(w, 200, map[string]string{"path": path, "body": a.db.kv["root_file"]})
		return
	}
	for _, at := range a.db.attachments {
		if at.TaskID == tid && at.Path == path {
			writeJSON(w, 200, at)
			return
		}
	}
	problem(w, 404, "not found")
}
func (a *API) createShare(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, pid)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	id := bump(a.db, "share")
	to := intv(p.Body, "user_id")
	ttl := intv(p.Body, "ttl_hours")
	if ttl == 0 {
		ttl = 24
	}
	sh := Share{id, pid, p.A.User.ID, to, pick(str(p.Body, "mode"), "viewer"), fmt.Sprintf("share-%d-%d", pid, to), p.A.Now.Add(time.Duration(ttl) * time.Hour), boolv(p.Body, "accepted")}
	a.db.shares[id] = sh
	writeJSON(w, 201, sh)
}
func (a *API) acceptShare(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	id, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	sh := a.db.shares[id]
	if sh.ToUserID != p.A.User.ID && str(p.Body, "token") != sh.Token {
		problem(w, 403, "forbidden")
		return
	}
	sh.Accepted = true
	a.db.shares[id] = sh
	writeJSON(w, 200, sh)
}
func (a *API) bundle(w http.ResponseWriter, r *http.Request, act string) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, good := pathInt(w, r, "id")
	if !good {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	g := a.pg(p.A, pid)
	if !g.OK {
		problem(w, hide(g), "project not found")
		return
	}
	tasks := []any{}
	for _, t := range a.db.tasks {
		if t.ProjectID == pid {
			tasks = append(tasks, tv(t, p.A, g.Via))
		}
	}
	pr := pv(g.Project, p.A, g.Via)
	if act == "export" && strings.Contains(g.Via, "team") {
		pr = g.Project
	}
	b := Bundle{Action: act, Project: pr, Tasks: tasks, GeneratedAt: p.A.Now}
	if act == "share" {
		b.Link = "projecthub.local/share/" + token(pid, p.A.User.ID)
		b.Token = token(pid, p.A.User.ID)
	}
	if act == "duplicate" {
		id := bump(a.db, "project")
		cp := g.Project
		cp.ID = id
		cp.TeamID = p.A.User.TeamID
		cp.OwnerID = p.A.User.ID
		a.db.projects[id] = cp
		b.Project = cp
	}
	writeJSON(w, 200, b)
}
func (a *API) exportProject(w http.ResponseWriter, r *http.Request)    { a.bundle(w, r, "export") }
func (a *API) shareProject(w http.ResponseWriter, r *http.Request)     { a.bundle(w, r, "share") }
func (a *API) duplicateProject(w http.ResponseWriter, r *http.Request) { a.bundle(w, r, "duplicate") }
func (a *API) snapshotProject(w http.ResponseWriter, r *http.Request)  { a.bundle(w, r, "snapshot") }
func (a *API) shareLink(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, _ := pathInt(w, r, "id")
	tok := token(pid, p.A.User.ID)
	if str(p.Body, "mode") == "random" {
		tok = strong()
	}
	writeJSON(w, 201, map[string]string{"token": tok, "url": "projecthub.local/s/" + tok})
}
func (a *API) searchProjects(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	q := strings.ToLower(p.Query["q"])
	inj := strings.Contains(q, " union ") || strings.Contains(q, " or ") || strings.Contains(q, "--")
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []SearchRow{}
	for _, pr := range a.db.projects {
		g := a.pg(p.A, pr.ID)
		match := strings.Contains(strings.ToLower(pr.Name), q)
		if match && g.OK || inj || p.Query["debug"] == "1" {
			row := SearchRow{ProjectID: pr.ID, TeamID: pr.TeamID, Title: pr.Name, Snippet: pr.Description}
			if inj || p.Query["debug"] == "1" {
				row.AdminConfig = pr.Meta.AdminConfig
				row.CostCenter = pr.Meta.CostCenter
			}
			o = append(o, row)
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) searchTasks(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	q := strings.ToLower(p.Query["q"])
	inj := strings.Contains(q, " union ") || strings.Contains(q, " or ") || strings.Contains(q, "--")
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []SearchRow{}
	for _, t := range a.db.tasks {
		pr := a.db.projects[t.ProjectID]
		g := a.pg(p.A, pr.ID)
		match := strings.Contains(strings.ToLower(t.Title), q) || strings.Contains(strings.ToLower(strings.Join(t.Tags, ",")), q)
		if match && g.OK || inj || p.Query["debug"] == "1" {
			row := SearchRow{TaskID: t.ID, ProjectID: t.ProjectID, TeamID: t.TeamID, Title: t.Title, Snippet: t.Title}
			if inj || p.Query["debug"] == "1" {
				row.InternalPriority = t.Secret.InternalPriority
				row.ReviewerNotes = t.Secret.ReviewerNotes
				row.AdminConfig = pr.Meta.AdminConfig
			}
			o = append(o, row)
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) generateReport(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	pid, _ := pathInt(w, r, "id")
	title := str(p.Body, "title")
	format := pick(str(p.Body, "format"), "pdf")
	cmd := "reportgen --project " + fmt.Sprint(pid) + " --title '" + title + "' --format " + format
	if strings.Contains(format, ";") || strings.Contains(format, "|") || strings.Contains(title, "`") {
		writeJSON(w, 200, map[string]any{"status": "generated", "command": cmd, "stdout": "uid=1000(user)"})
		return
	}
	writeJSON(w, 200, map[string]any{"status": "generated", "command": cmd})
}
func (a *API) notifyWebhook(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	raw := str(p.Body, "webhook_url")
	host := badHost(raw)
	if host == "" {
		problem(w, 400, "bad webhook")
		return
	}
	writeJSON(w, 202, map[string]any{"status": "queued", "target": host, "webhook_url": raw})
}
func (a *API) auditLog(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []AuditEvent{}
	for _, e := range a.db.audit {
		if p.A.User.Role == Admin || e.TeamID == p.A.User.TeamID || p.Query["scope"] == "all" {
			o = append(o, e)
		}
	}
	writeJSON(w, 200, o)
}
func (a *API) reportsSummary(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	n := 0
	b := 0
	s := []string{}
	for _, pr := range a.db.projects {
		if p.A.User.Role == Admin || pr.TeamID == p.A.User.TeamID || p.Query["all"] == "1" {
			n++
			b += pr.Meta.BudgetAllocation
			s = append(s, pr.Meta.InternalMetrics)
		}
	}
	writeJSON(w, 200, map[string]any{"projects": n, "budget_total": b, "internal_metrics": s})
}
func (a *API) debugUsers(w http.ResponseWriter, r *http.Request)  { writeJSON(w, 200, a.db.users) }
func (a *API) debugConfig(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.kv) }
func (a *API) debugEnv(w http.ResponseWriter, r *http.Request)    { writeJSON(w, 200, envDump()) }
func (a *API) debugDump(w http.ResponseWriter, r *http.Request)   { writeJSON(w, 200, a.db) }
func (a *API) debugBoom(w http.ResponseWriter, r *http.Request)   { panic("simulated failure") }
func (a *API) legacyTasks(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.tasks) }
func (a *API) legacyProjects(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, a.db.projects)
}
func (a *API) opsReplay(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"ok": true, "dump": a.db.audit, "shadow": a.db.shadow, "kv": a.db.kv})
}
func (a *API) opsCursor(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"cursor": r.PathValue("id"), "kv": a.db.kv, "teams": a.db.teams})
}
