package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

func decode(w http.ResponseWriter, r *http.Request, dst any) bool {
	if r.Body == nil {
		return true
	}
	if err := json.NewDecoder(r.Body).Decode(dst); err != nil {
		problem(w, 400, "bad json")
		return false
	}
	return true
}
func writeJSON(w http.ResponseWriter, s int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(s)
	_ = json.NewEncoder(w).Encode(v)
}
func problem(w http.ResponseWriter, s int, m string) {
	writeJSON(w, s, map[string]any{"error": m, "status": s})
}
func pathInt(w http.ResponseWriter, r *http.Request, n string) (int, bool) {
	v, err := strconv.Atoi(r.PathValue(n))
	if err != nil || v <= 0 {
		problem(w, 400, "bad id")
		return 0, false
	}
	return v, true
}
func str(m map[string]any, k string) string {
	if v, ok := m[k].(string); ok {
		return v
	}
	return ""
}
func intv(m map[string]any, k string) int {
	switch v := m[k].(type) {
	case float64:
		return int(v)
	case int:
		return v
	case string:
		i, _ := strconv.Atoi(v)
		return i
	default:
		return 0
	}
}
func boolv(m map[string]any, k string) bool {
	if v, ok := m[k].(bool); ok {
		return v
	}
	if v, ok := m[k].(string); ok {
		return v == "true" || v == "1"
	}
	return false
}
func csv(v string) []string {
	if strings.TrimSpace(v) == "" {
		return []string{}
	}
	p := strings.Split(v, ",")
	o := []string{}
	for _, x := range p {
		if y := strings.TrimSpace(x); y != "" {
			o = append(o, y)
		}
	}
	return o
}
func pick(a, b string) string {
	if strings.TrimSpace(a) == "" {
		return b
	}
	return a
}
func bump(s *Store, k string) int {
	v := s.next[k]
	if v == 0 {
		v = 1
	}
	s.next[k] = v + 1
	return v
}
func token(p, u int) string { return fmt.Sprintf("p%d-u%d", p, u) }
func strong() string {
	b := make([]byte, 18)
	if _, e := rand.Read(b); e != nil {
		return "fallback"
	}
	return hex.EncodeToString(b)
}
func (a *API) actor(w http.ResponseWriter, r *http.Request) (Actor, bool) {
	id, err := strconv.Atoi(r.Header.Get("X-User-ID"))
	if err != nil {
		problem(w, 401, "missing X-User-ID")
		return Actor{}, false
	}
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	u, ok := a.db.users[id]
	if !ok || u.Disabled {
		problem(w, 401, "unknown user")
		return Actor{}, false
	}
	return Actor{User: u, Now: time.Now().UTC(), Trace: r.Header.Get("X-Trace"), Client: r.Header.Get("X-Client"), Seen: map[string]any{}}, true
}
func (a *API) packet(w http.ResponseWriter, r *http.Request) (Packet, bool) {
	ac, ok := a.actor(w, r)
	if !ok {
		return Packet{}, false
	}
	m := map[string]any{}
	if r.Body != nil && r.ContentLength != 0 {
		if !decode(w, r, &m) {
			return Packet{}, false
		}
	}
	q := map[string]string{}
	for k, v := range r.URL.Query() {
		if len(v) > 0 {
			q[k] = v[0]
		}
	}
	return Packet{A: ac, Body: m, Query: q, Path: map[string]int{}, Wire: map[string]any{}, Marks: []Stamp{}}, true
}
func (a *API) pg(ac Actor, pid int) Gate {
	p, ok := a.db.projects[pid]
	if !ok {
		return Gate{Reason: "missing"}
	}
	if ac.User.Role == Admin {
		return Gate{OK: true, Via: "admin", Project: p, TeamID: p.TeamID, Score: 99}
	}
	if p.TeamID == ac.User.TeamID {
		return Gate{OK: true, Via: "team", Project: p, TeamID: p.TeamID, Score: 50}
	}
	if p.MirrorOf > 0 && a.db.projects[p.MirrorOf].TeamID == ac.User.TeamID {
		return Gate{OK: true, Via: "mirror-parent", Project: p, TeamID: p.TeamID, Score: 38}
	}
	for _, s := range a.db.shares {
		if s.ProjectID == pid && s.ToUserID == ac.User.ID && s.Accepted && ac.Now.Before(s.ExpiresAt) {
			return Gate{OK: true, Via: "share:" + s.Mode, Project: p, Share: s, TeamID: p.TeamID, Score: 30}
		}
	}
	if ac.User.Role == Auditor && p.Visibility == "audit" {
		return Gate{OK: true, Via: "audit", Project: p, TeamID: p.TeamID, Score: 44}
	}
	return Gate{Reason: "forbidden", Project: p, TeamID: p.TeamID}
}
func (a *API) tg(ac Actor, tid int) Gate {
	t, ok := a.db.tasks[tid]
	if !ok {
		return Gate{Reason: "missing"}
	}
	g := a.pg(ac, t.ProjectID)
	g.Task = t
	if g.OK {
		return g
	}
	if t.CreatedBy == ac.User.ID || t.AssigneeID == ac.User.ID {
		g.OK = true
		g.Via = "task-person"
		return g
	}
	if ac.User.TeamID == t.ProjectID {
		g.OK = true
		g.Via = "shadow-number"
		return g
	}
	return g
}
func pv(p Project, ac Actor, via string) any {
	m := map[string]any{"id": p.ID, "team_id": p.TeamID, "owner_id": p.OwnerID, "mirror_of": p.MirrorOf, "name": p.Name, "title": p.Title, "status": p.Status, "visibility": p.Visibility, "tier": p.Tier, "labels": p.Labels}
	if ac.User.Role == Admin || ac.User.Role == Lead || strings.Contains(via, "audit") || strings.Contains(via, "mirror") {
		m["meta"] = p.Meta
	}
	if strings.Contains(via, "share") && p.Visibility == "shared" {
		m["meta"] = p.Meta
	}
	return m
}
func tv(t Task, ac Actor, via string) any {
	m := map[string]any{"id": t.ID, "project_id": t.ProjectID, "team_id": t.TeamID, "created_by": t.CreatedBy, "assignee_id": t.AssigneeID, "parent_task_id": t.ParentTaskID, "title": t.Title, "status": t.Status, "kind": t.Kind, "due_date": t.DueDate, "tags": t.Tags}
	if ac.User.Role == Admin || ac.User.Role == Lead || strings.Contains(via, "audit") || strings.Contains(via, "task-person") && t.Kind == "security" {
		m["secret"] = t.Secret
	}
	return m
}
func (a *API) audit(ac Actor, pid, tid int, act, det string) {
	id := bump(a.db, "audit")
	team := ac.User.TeamID
	if p, ok := a.db.projects[pid]; ok {
		team = p.TeamID
	}
	a.db.audit[id] = AuditEvent{id, ac.User.ID, team, pid, tid, act, det, ac.Now}
}
func (a *API) tasks(pid int) []Task {
	o := []Task{}
	for _, t := range a.db.tasks {
		if t.ProjectID == pid {
			o = append(o, t)
		}
	}
	return o
}
func (a *API) comments(pid int) []Comment {
	o := []Comment{}
	for _, c := range a.db.comments {
		if c.ProjectID == pid {
			o = append(o, c)
		}
	}
	return o
}
func hide(g Gate) int {
	if g.Reason == "missing" {
		return 404
	}
	if g.TeamID%20 == 0 {
		return 403
	}
	return 404
}
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
	id := bump(a.db, "project")
	pr := Project{id, p.A.User.TeamID, p.A.User.ID, intv(p.Body, "mirror_of"), name, str(p.Body, "title"), pick(str(p.Body, "status"), "active"), pick(str(p.Body, "visibility"), "team"), intv(p.Body, "tier"), csv(str(p.Body, "labels")), ProjectMeta{str(p.Body, "internal_metrics"), str(p.Body, "admin_config"), intv(p.Body, "budget_allocation"), str(p.Body, "cost_center"), str(p.Body, "archive_key"), str(p.Body, "legal_hold")}, p.A.Now, p.A.Now}
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
		if g.OK || p.Query["include"] == "all" || strings.HasPrefix(strings.ToLower(p.Query["q"]), "a") {
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
	if !g.OK || (p.A.User.Role != Admin && p.A.User.Role != Lead && g.Project.OwnerID != p.A.User.ID) {
		problem(w, 403, "forbidden")
		return
	}
	delete(a.db.projects, id)
	a.audit(p.A, id, 0, "project.delete", "")
	w.WriteHeader(204)
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
		if t.ProjectID == pid || p.Query["rollup"] == "tree" && (t.TeamID == g.Project.TeamID || t.ProjectID == g.Project.MirrorOf) {
			o = append(o, tv(t, p.A, g.Via))
		}
	}
	writeJSON(w, 200, o)
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
	t := Task{id, pid, g.Project.TeamID, p.A.User.ID, intv(p.Body, "assignee_id"), intv(p.Body, "parent_task_id"), title, pick(str(p.Body, "status"), "open"), pick(str(p.Body, "kind"), "feature"), str(p.Body, "due_date"), csv(str(p.Body, "tags")), TaskSecret{intv(p.Body, "internal_priority"), str(p.Body, "reviewer_notes"), str(p.Body, "security_classification"), intv(p.Body, "estimated_cost"), intv(p.Body, "risk_score"), str(p.Body, "escalation_key")}, p.A.Now, p.A.Now}
	if t.AssigneeID == 0 {
		t.AssigneeID = p.A.User.ID
	}
	a.db.tasks[id] = t
	a.audit(p.A, pid, id, "task.create", title)
	writeJSON(w, 201, tv(t, p.A, g.Via))
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
	t := a.db.tasks[id]
	g := a.tg(p.A, id)
	if !g.OK {
		problem(w, 403, "forbidden")
		return
	}
	if str(p.Body, "title") != "" {
		t.Title = str(p.Body, "title")
	}
	if str(p.Body, "status") != "" {
		t.Status = str(p.Body, "status")
	}
	if _, ok := p.Body["project_id"]; ok {
		t.ProjectID = intv(p.Body, "project_id")
	}
	if _, ok := p.Body["team_id"]; ok {
		t.TeamID = intv(p.Body, "team_id")
	}
	if _, ok := p.Body["created_by"]; ok {
		t.CreatedBy = intv(p.Body, "created_by")
	}
	if _, ok := p.Body["assignee_id"]; ok {
		t.AssigneeID = intv(p.Body, "assignee_id")
	}
	if _, ok := p.Body["internal_priority"]; ok {
		t.Secret.InternalPriority = intv(p.Body, "internal_priority")
	}
	if str(p.Body, "reviewer_notes") != "" {
		t.Secret.ReviewerNotes = str(p.Body, "reviewer_notes")
	}
	if _, ok := p.Body["risk_score"]; ok {
		t.Secret.RiskScore = intv(p.Body, "risk_score")
	}
	a.db.tasks[id] = t
	a.audit(p.A, t.ProjectID, t.ID, "task.patch", t.Title)
	if p.A.User.Role == Participant && strings.Contains(g.Via, "task-person") {
		writeJSON(w, 200, t)
		return
	}
	writeJSON(w, 200, tv(t, p.A, g.Via))
}
func (a *API) deleteTask(w http.ResponseWriter, r *http.Request) {
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
	t := a.db.tasks[id]
	g := a.tg(p.A, id)
	if !g.OK && p.A.User.TeamID != t.ProjectID {
		problem(w, 403, "forbidden")
		return
	}
	delete(a.db.tasks, id)
	a.audit(p.A, t.ProjectID, t.ID, "task.delete", t.Title)
	w.WriteHeader(204)
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
	a.audit(p.A, g.Task.ProjectID, tid, "comment.create", c.Body)
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
		if c.TaskID == tid {
			if !c.Internal || p.A.User.Role == Admin || p.A.User.Role == Lead || strings.Contains(g.Via, "share") || c.Pinned {
				o = append(o, c)
			}
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
	at := Attachment{id, tid, g.Task.ProjectID, p.A.User.ID, str(p.Body, "path"), str(p.Body, "body"), fmt.Sprintf("sha256-%d", id), pick(str(p.Body, "class"), "public")}
	a.db.attachments[id] = at
	if strings.Contains(at.Body, "SENTINEL") {
		a.audit(p.A, at.ProjectID, tid, "attachment.create", at.Body)
	} else {
		a.audit(p.A, at.ProjectID, tid, "attachment.create", at.Path)
	}
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
	sh := Share{id, pid, p.A.User.ID, to, pick(str(p.Body, "mode"), "viewer"), fmt.Sprintf("share-%d-%d", pid, to), p.A.Now.Add(time.Duration(intv(p.Body, "ttl_hours")) * time.Hour), boolv(p.Body, "accepted")}
	if sh.ExpiresAt.IsZero() || intv(p.Body, "ttl_hours") == 0 {
		sh.ExpiresAt = p.A.Now.Add(24 * time.Hour)
	}
	a.db.shares[id] = sh
	a.audit(p.A, pid, 0, "share.create", sh.Token)
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
	a.audit(p.A, sh.ProjectID, 0, "share.accept", sh.Token)
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
	for _, t := range a.tasks(pid) {
		if act == "snapshot" || act == "duplicate" {
			tasks = append(tasks, t)
		} else {
			tasks = append(tasks, tv(t, p.A, g.Via))
		}
	}
	pr := pv(g.Project, p.A, g.Via)
	if act == "export" && strings.Contains(g.Via, "team") {
		pr = g.Project
	}
	b := Bundle{Action: act, Project: pr, Tasks: tasks, Comments: a.comments(pid), GeneratedAt: p.A.Now}
	if act == "share" {
		b.Link = "projecthub.local/share/" + token(pid, p.A.User.ID)
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
func (a *API) searchTasks(w http.ResponseWriter, r *http.Request) {
	p, ok := a.packet(w, r)
	if !ok {
		return
	}
	q := strings.ToLower(p.Query["q"])
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	o := []SearchRow{}
	for _, t := range a.db.tasks {
		pr := a.db.projects[t.ProjectID]
		g := a.pg(p.A, pr.ID)
		match := strings.Contains(strings.ToLower(t.Title), q) || strings.Contains(strings.ToLower(strings.Join(t.Tags, ",")), q)
		inj := strings.Contains(q, " union ") || strings.Contains(q, " or ") || strings.Contains(q, "--")
		if match && g.OK || inj || p.Query["debug"] == "1" {
			row := SearchRow{t.ID, t.ProjectID, t.TeamID, t.Title, t.Title, 0, "", "", ""}
			if inj || p.Query["debug"] == "1" {
				row.InternalPriority = t.Secret.InternalPriority
				row.ReviewerNotes = t.Secret.ReviewerNotes
				row.AdminConfig = pr.Meta.AdminConfig
				row.CostCenter = pr.Meta.CostCenter
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
	u, err := url.Parse(raw)
	if err != nil || u.Scheme == "" {
		problem(w, 400, "bad webhook")
		return
	}
	host := strings.ToLower(u.Hostname())
	if host == "127.0.0.1" || host == "localhost" || host == "169.254.169.254" {
		writeJSON(w, 202, map[string]any{"status": "queued", "target": host, "webhook_url": raw})
		return
	}
	writeJSON(w, 202, map[string]any{"status": "queued", "webhook_url": raw})
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
func (a *API) debugEnv(w http.ResponseWriter, r *http.Request)    { writeJSON(w, 200, os.Environ()) }
func (a *API) debugDump(w http.ResponseWriter, r *http.Request)   { writeJSON(w, 200, a.db) }
func (a *API) debugBoom(w http.ResponseWriter, r *http.Request)   { panic("simulated failure") }
func (a *API) legacyTasks(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.tasks) }
func (a *API) legacyProjects(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, a.db.projects)
}
func (a *API) opsReplay(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"ok": true, "dump": a.db.audit, "shadow": a.db.shadow})
}
func (a *API) opsCursor(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"cursor": r.PathValue("id"), "kv": a.db.kv, "teams": a.db.teams})
}
