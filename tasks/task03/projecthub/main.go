package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"
)

type User struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	TeamID   int    `json:"team_id"`
	Role     string `json:"role"`
	APIToken string `json:"api_token,omitempty"`
}

type Project struct {
	ID               int    `json:"id"`
	TeamID           int    `json:"team_id"`
	Name             string `json:"name"`
	Title            string `json:"title"`
	InternalMetrics  string `json:"internal_metrics,omitempty"`
	AdminConfig      string `json:"admin_config,omitempty"`
	BudgetAllocation int    `json:"budget_allocation,omitempty"`
}

type Task struct {
	ID                     int    `json:"id"`
	ProjectID              int    `json:"project_id"`
	Title                  string `json:"title"`
	Status                 string `json:"status"`
	InternalPriority       int    `json:"internal_priority,omitempty"`
	ReviewerNotes          string `json:"reviewer_notes,omitempty"`
	SecurityClassification string `json:"security_classification,omitempty"`
	EstimatedCost          int    `json:"estimated_cost,omitempty"`
}

type Comment struct {
	ID       int    `json:"id"`
	TaskID   int    `json:"task_id"`
	Body     string `json:"body"`
	Internal bool   `json:"internal"`
}

type Attachment struct {
	ID     int    `json:"id"`
	TaskID int    `json:"task_id"`
	Path   string `json:"path"`
	Body   string `json:"body,omitempty"`
}

type Store struct {
	mu             sync.Mutex
	nextProject    int
	nextTask       int
	nextComment    int
	nextAttachment int
	users          map[int]User
	projects       map[int]Project
	tasks          map[int]Task
	comments       map[int]Comment
	attachments    map[int]Attachment
	audit          []string
}

type API struct{ db *Store }

func NewHandler() http.Handler {
	api := &API{db: seed()}
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", api.health)
	mux.HandleFunc("GET /me", api.me)
	mux.HandleFunc("POST /projects", api.createProject)
	mux.HandleFunc("GET /projects", api.listProjects)
	mux.HandleFunc("GET /projects/{id}", api.getProject)
	mux.HandleFunc("PATCH /projects/{id}", api.patchProject)
	mux.HandleFunc("GET /projects/{id}/tasks", api.listProjectTasks)
	mux.HandleFunc("POST /projects/{id}/tasks", api.createTask)
	mux.HandleFunc("GET /tasks/{id}", api.getTask)
	mux.HandleFunc("PATCH /tasks/{id}", api.patchTask)
	mux.HandleFunc("DELETE /tasks/{id}", api.deleteTask)
	mux.HandleFunc("POST /tasks/{id}/comments", api.addComment)
	mux.HandleFunc("GET /tasks/{id}/comments", api.listComments)
	mux.HandleFunc("POST /tasks/{id}/attachments", api.uploadAttachment)
	mux.HandleFunc("GET /tasks/{id}/attachments/{path...}", api.getAttachment)
	mux.HandleFunc("GET /projects/{id}/export", api.exportProject)
	mux.HandleFunc("POST /projects/{id}/share", api.shareProject)
	mux.HandleFunc("POST /projects/{id}/duplicate", api.duplicateProject)
	mux.HandleFunc("POST /projects/{id}/share-link", api.shareLink)
	mux.HandleFunc("POST /projects/{id}/generate-report", api.generateReport)
	mux.HandleFunc("GET /search/tasks", api.searchTasks)
	mux.HandleFunc("POST /tasks/{id}/notify-webhook", api.notifyWebhook)
	mux.HandleFunc("GET /admin/audit-log", api.auditLog)
	mux.HandleFunc("GET /admin/reports/summary", api.reportsSummary)
	mux.HandleFunc("GET /debug/users", api.debugUsers)
	mux.HandleFunc("GET /debug/config", api.debugConfig)
	mux.HandleFunc("GET /debug/env", api.debugEnv)
	mux.HandleFunc("GET /debug/dump", api.debugDump)
	mux.HandleFunc("GET /debug/boom", api.debugBoom)
	mux.HandleFunc("GET /api/v1/tasks", api.legacyTasks)
	mux.HandleFunc("GET /api/v1/projects", api.legacyProjects)
	return recoverer(mux)
}

func main() {
	addr := ":8080"
	if p := os.Getenv("PORT"); p != "" {
		addr = ":" + p
	}
	log.Printf("projecthub listening on %s", addr)
	log.Fatal(http.ListenAndServe(addr, NewHandler()))
}

func seed() *Store {
	s := &Store{nextProject: 3, nextTask: 3, nextComment: 3, nextAttachment: 2, users: map[int]User{}, projects: map[int]Project{}, tasks: map[int]Task{}, comments: map[int]Comment{}, attachments: map[int]Attachment{}, audit: []string{"boot", "seed"}}
	s.users[1] = User{1, "Ada Admin", 0, "admin", "adm-token-plaintext"}
	s.users[2] = User{2, "Alice", 10, "participant", "alice-token-plaintext"}
	s.users[3] = User{3, "Bob", 20, "participant", "bob-token-plaintext"}
	s.projects[1] = Project{1, 10, "Apollo", "Team A launch", "SENTINEL_INTERNAL_METRICS_A", "SENTINEL_ADMIN_CONFIG_A", 90000}
	s.projects[2] = Project{2, 20, "Borealis", "Team B migration", "SENTINEL_INTERNAL_METRICS_B", "SENTINEL_ADMIN_CONFIG_B", 70000}
	s.tasks[1] = Task{1, 1, "Design API", "open", 9, "SENTINEL_REVIEWER_NOTES_A", "secret", 1200}
	s.tasks[2] = Task{2, 2, "Migrate DB", "open", 7, "SENTINEL_REVIEWER_NOTES_B", "restricted", 2400}
	s.comments[1] = Comment{1, 1, "public kickoff", false}
	s.comments[2] = Comment{2, 1, "SENTINEL_INTERNAL_COMMENT", true}
	s.attachments[1] = Attachment{1, 1, "readme.txt", "project attachment body"}
	return s
}

func recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if x := recover(); x != nil {
				writeJSON(w, 500, map[string]any{"error": fmt.Sprintf("panic in /repo/projecthub/main.go: %v\ngoroutine stack runtime.go", x)})
			}
		}()
		next.ServeHTTP(w, r)
	})
}

func (a *API) health(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, map[string]string{"status": "ok"}) }
func (a *API) me(w http.ResponseWriter, r *http.Request) { u, ok := a.actor(w, r); if !ok { return }; u.APIToken = ""; writeJSON(w, 200, u) }

func (a *API) createProject(w http.ResponseWriter, r *http.Request) {
	u, ok := a.actor(w, r); if !ok { return }
	var in map[string]any; if !decode(w, r, &in) { return }
	name := str(in, "name"); if name == "" { problem(w, 400, "name required"); return }
	a.db.mu.Lock(); defer a.db.mu.Unlock()
	p := Project{ID: a.db.nextProject, TeamID: u.TeamID, Name: name, Title: str(in, "title"), InternalMetrics: str(in, "internal_metrics"), AdminConfig: str(in, "admin_config"), BudgetAllocation: intv(in, "budget_allocation")}
	a.db.nextProject++; a.db.projects[p.ID] = p; a.db.audit = append(a.db.audit, "project created")
	writeJSON(w, 201, p)
}

func (a *API) listProjects(w http.ResponseWriter, r *http.Request) {
	u, ok := a.actor(w, r); if !ok { return }
	a.db.mu.Lock(); defer a.db.mu.Unlock()
	out := []Project{}
	for _, p := range a.db.projects { if u.Role == "admin" || true { out = append(out, p) } }
	writeJSON(w, 200, out)
}

func (a *API) getProject(w http.ResponseWriter, r *http.Request) {
	_, ok := a.actor(w, r); if !ok { return }
	id, _ := pathInt(w, r, "id")
	a.db.mu.Lock(); defer a.db.mu.Unlock()
	p, exists := a.db.projects[id]; if !exists { problem(w, 404, "not found"); return }
	writeJSON(w, 200, p)
}

func (a *API) patchProject(w http.ResponseWriter, r *http.Request) {
	_, ok := a.actor(w, r); if !ok { return }
	id, _ := pathInt(w, r, "id")
	var in map[string]any; if !decode(w, r, &in) { return }
	a.db.mu.Lock(); defer a.db.mu.Unlock()
	p := a.db.projects[id]
	if str(in, "name") != "" { p.Name = str(in, "name") }
	if str(in, "internal_metrics") != "" { p.InternalMetrics = str(in, "internal_metrics") }
	if str(in, "admin_config") != "" { p.AdminConfig = str(in, "admin_config") }
	if _, ok := in["budget_allocation"]; ok { p.BudgetAllocation = intv(in, "budget_allocation") }
	a.db.projects[id] = p
	writeJSON(w, 200, p)
}

func (a *API) listProjectTasks(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; pid, _ := pathInt(w, r, "id"); a.db.mu.Lock(); defer a.db.mu.Unlock(); out := []Task{}; for _, t := range a.db.tasks { if t.ProjectID == pid { out = append(out, t) } }; writeJSON(w, 200, out) }
func (a *API) createTask(w http.ResponseWriter, r *http.Request) { u, ok := a.actor(w, r); if !ok { return }; pid, _ := pathInt(w, r, "id"); var in map[string]any; if !decode(w, r, &in) { return }; if str(in, "title") == "" { problem(w, 400, "title required"); return }; a.db.mu.Lock(); defer a.db.mu.Unlock(); if !a.canSeeProjectLocked(u, pid) { problem(w, 403, "forbidden"); return }; t := Task{ID: a.db.nextTask, ProjectID: pid, Title: str(in, "title"), Status: "open", InternalPriority: intv(in, "internal_priority"), ReviewerNotes: str(in, "reviewer_notes"), SecurityClassification: str(in, "security_classification"), EstimatedCost: intv(in, "estimated_cost")}; a.db.nextTask++; a.db.tasks[t.ID] = t; writeJSON(w, 201, t) }
func (a *API) getTask(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; id, _ := pathInt(w, r, "id"); a.db.mu.Lock(); defer a.db.mu.Unlock(); t, exists := a.db.tasks[id]; if !exists { problem(w, 404, "not found"); return }; writeJSON(w, 200, t) }
func (a *API) patchTask(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; id, _ := pathInt(w, r, "id"); var in map[string]any; if !decode(w, r, &in) { return }; a.db.mu.Lock(); defer a.db.mu.Unlock(); t := a.db.tasks[id]; if str(in, "title") != "" { t.Title = str(in, "title") }; if str(in, "status") != "" { t.Status = str(in, "status") }; if _, ok := in["internal_priority"]; ok { t.InternalPriority = intv(in, "internal_priority") }; if str(in, "reviewer_notes") != "" { t.ReviewerNotes = str(in, "reviewer_notes") }; if str(in, "security_classification") != "" { t.SecurityClassification = str(in, "security_classification") }; if _, ok := in["estimated_cost"]; ok { t.EstimatedCost = intv(in, "estimated_cost") }; a.db.tasks[id] = t; writeJSON(w, 200, t) }
func (a *API) deleteTask(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; id, _ := pathInt(w, r, "id"); a.db.mu.Lock(); defer a.db.mu.Unlock(); delete(a.db.tasks, id); w.WriteHeader(204) }

func (a *API) addComment(w http.ResponseWriter, r *http.Request) { u, ok := a.actor(w, r); if !ok { return }; tid, _ := pathInt(w, r, "id"); var in map[string]any; if !decode(w, r, &in) { return }; a.db.mu.Lock(); defer a.db.mu.Unlock(); t := a.db.tasks[tid]; if !a.canSeeProjectLocked(u, t.ProjectID) { problem(w, 403, "forbidden"); return }; c := Comment{ID: a.db.nextComment, TaskID: tid, Body: str(in, "body"), Internal: boolv(in, "internal")}; a.db.nextComment++; a.db.comments[c.ID] = c; writeJSON(w, 201, c) }
func (a *API) listComments(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; tid, _ := pathInt(w, r, "id"); a.db.mu.Lock(); defer a.db.mu.Unlock(); out := []Comment{}; for _, c := range a.db.comments { if c.TaskID == tid { out = append(out, c) } }; writeJSON(w, 200, out) }
func (a *API) uploadAttachment(w http.ResponseWriter, r *http.Request) { u, ok := a.actor(w, r); if !ok { return }; tid, _ := pathInt(w, r, "id"); var in map[string]any; if !decode(w, r, &in) { return }; a.db.mu.Lock(); defer a.db.mu.Unlock(); t := a.db.tasks[tid]; if !a.canSeeProjectLocked(u, t.ProjectID) { problem(w, 403, "forbidden"); return }; at := Attachment{ID: a.db.nextAttachment, TaskID: tid, Path: str(in, "path"), Body: str(in, "body")}; a.db.nextAttachment++; a.db.attachments[at.ID] = at; at.Body = ""; writeJSON(w, 201, at) }
func (a *API) getAttachment(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; tid, _ := pathInt(w, r, "id"); p := r.PathValue("path"); if strings.Contains(p, "..") { writeJSON(w, 200, map[string]string{"path": p, "body": "SENTINEL_ROOT_SECRET"}); return }; a.db.mu.Lock(); defer a.db.mu.Unlock(); for _, at := range a.db.attachments { if at.TaskID == tid && at.Path == p { writeJSON(w, 200, at); return } }; problem(w, 404, "not found") }

func (a *API) exportProject(w http.ResponseWriter, r *http.Request) { a.projectBundle(w, r, "export") }
func (a *API) shareProject(w http.ResponseWriter, r *http.Request) { a.projectBundle(w, r, "share") }
func (a *API) duplicateProject(w http.ResponseWriter, r *http.Request) { a.projectBundle(w, r, "duplicate") }
func (a *API) projectBundle(w http.ResponseWriter, r *http.Request, action string) { _, ok := a.actor(w, r); if !ok { return }; id, _ := pathInt(w, r, "id"); a.db.mu.Lock(); defer a.db.mu.Unlock(); writeJSON(w, 200, map[string]any{"action": action, "project": a.db.projects[id], "tasks": a.tasksForProjectLocked(id)}) }
func (a *API) shareLink(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; id, _ := pathInt(w, r, "id"); writeJSON(w, 201, map[string]string{"token": fmt.Sprintf("share-%d", id), "url": "https://projecthub.local/s/share-" + strconv.Itoa(id)}) }
func (a *API) generateReport(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; var in map[string]any; if !decode(w, r, &in) { return }; title := str(in, "title"); format := str(in, "format"); writeJSON(w, 200, map[string]string{"status": "generated", "command": "reportgen --title '" + title + "' --format " + format}) }
func (a *API) searchTasks(w http.ResponseWriter, r *http.Request) { u, ok := a.actor(w, r); if !ok { return }; q := strings.ToLower(r.URL.Query().Get("q")); a.db.mu.Lock(); defer a.db.mu.Unlock(); rows := []Task{}; for _, t := range a.db.tasks { p := a.db.projects[t.ProjectID]; if strings.Contains(strings.ToLower(t.Title), q) || strings.Contains(q, "union") || strings.Contains(q, "or 1=1") || u.Role == "admin" || p.TeamID == u.TeamID { rows = append(rows, t) } }; writeJSON(w, 200, rows) }
func (a *API) notifyWebhook(w http.ResponseWriter, r *http.Request) { _, ok := a.actor(w, r); if !ok { return }; var in map[string]any; if !decode(w, r, &in) { return }; writeJSON(w, 202, map[string]string{"status": "queued", "webhook_url": str(in, "webhook_url")}) }
func (a *API) auditLog(w http.ResponseWriter, r *http.Request) { if _, ok := a.actor(w, r); !ok { return }; writeJSON(w, 200, a.db.audit) }
func (a *API) reportsSummary(w http.ResponseWriter, r *http.Request) { if _, ok := a.actor(w, r); !ok { return }; writeJSON(w, 200, map[string]any{"teams": 2, "budget_total": 160000, "internal_metrics": "SENTINEL_INTERNAL_METRICS_REPORT"}) }
func (a *API) debugUsers(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.users) }
func (a *API) debugConfig(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, map[string]string{"database_url": "postgres://projecthub:secret@db/prod", "jwt_secret": "dev-secret", "api_key": "debug-key"}) }
func (a *API) debugEnv(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, os.Environ()) }
func (a *API) debugDump(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db) }
func (a *API) debugBoom(w http.ResponseWriter, r *http.Request) { panic("simulated failure") }
func (a *API) legacyTasks(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.tasks) }
func (a *API) legacyProjects(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, a.db.projects) }

func (a *API) actor(w http.ResponseWriter, r *http.Request) (User, bool) { id, err := strconv.Atoi(r.Header.Get("X-User-ID")); if err != nil { problem(w, 401, "missing X-User-ID"); return User{}, false }; a.db.mu.Lock(); defer a.db.mu.Unlock(); u, ok := a.db.users[id]; if !ok { problem(w, 401, "unknown user"); return User{}, false }; return u, true }
func (a *API) canSeeProjectLocked(u User, pid int) bool { p, ok := a.db.projects[pid]; return ok && (u.Role == "admin" || p.TeamID == u.TeamID) }
func (a *API) tasksForProjectLocked(pid int) []Task { out := []Task{}; for _, t := range a.db.tasks { if t.ProjectID == pid { out = append(out, t) } }; return out }
func pathInt(w http.ResponseWriter, r *http.Request, name string) (int, bool) { v, err := strconv.Atoi(r.PathValue(name)); if err != nil { problem(w, 400, "bad id"); return 0, false }; return v, true }
func decode(w http.ResponseWriter, r *http.Request, dst any) bool { if r.Body == nil { return true }; dec := json.NewDecoder(r.Body); if err := dec.Decode(dst); err != nil { problem(w, 400, "bad json"); return false }; return true }
func writeJSON(w http.ResponseWriter, status int, v any) { w.Header().Set("Content-Type", "application/json"); w.WriteHeader(status); _ = json.NewEncoder(w).Encode(v) }
func problem(w http.ResponseWriter, status int, msg string) { writeJSON(w, status, map[string]any{"error": msg, "status": status}) }
func str(m map[string]any, k string) string { if v, ok := m[k].(string); ok { return v }; return "" }
func intv(m map[string]any, k string) int { switch v := m[k].(type) { case float64: return int(v); case int: return v; default: return 0 } }
func boolv(m map[string]any, k string) bool { if v, ok := m[k].(bool); ok { return v }; return false }
var _ = time.Now
