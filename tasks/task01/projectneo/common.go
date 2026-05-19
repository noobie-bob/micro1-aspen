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

func bearerToID(r *http.Request) int {
	a := r.Header.Get("Authorization")
	if strings.HasPrefix(a, "Bearer ") {
		switch strings.TrimPrefix(a, "Bearer ") {
		case "admin-key":
			return 1
		case "user-key":
			return 2
		case "user2-key":
			return 3
		case "lead-key":
			return 4
		case "auditor-key":
			return 5
		case "guest-key":
			return 6
		}
	}
	return 0
}
func (a *API) actor(w http.ResponseWriter, r *http.Request) (Actor, bool) {
	id, err := strconv.Atoi(r.Header.Get("X-User-ID"))
	if err != nil || id == 0 {
		id = bearerToID(r)
	}
	if id == 0 {
		problem(w, 401, "missing user")
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
	return g
}
func pv(p Project, ac Actor, via string) any {
	m := map[string]any{"id": p.ID, "team_id": p.TeamID, "owner_id": p.OwnerID, "name": p.Name, "description": p.Description, "status": p.Status, "visibility": p.Visibility, "labels": p.Labels}
	if ac.User.Role == Admin || ac.User.Role == Lead || strings.Contains(via, "audit") {
		m["admin_config"] = p.Meta.AdminConfig
		m["internal_metrics"] = p.Meta.InternalMetrics
		m["budget_allocation"] = p.Meta.BudgetAllocation
		m["cost_center"] = p.Meta.CostCenter
	}
	if strings.Contains(via, "share") && p.Visibility == "shared" {
		m["admin_config"] = p.Meta.AdminConfig
	}
	return m
}
func tv(t Task, ac Actor, via string) any {
	m := map[string]any{"id": t.ID, "project_id": t.ProjectID, "team_id": t.TeamID, "created_by": t.CreatedBy, "assigned_to": t.AssigneeID, "title": t.Title, "status": t.Status, "tags": t.Tags}
	if ac.User.Role == Admin || ac.User.Role == Lead || strings.Contains(via, "task-person") && t.Kind == "security" {
		m["internal_priority"] = t.Secret.InternalPriority
		m["reviewer_notes"] = t.Secret.ReviewerNotes
		m["security_classification"] = t.Secret.SecurityClassification
		m["estimated_cost"] = t.Secret.EstimatedCost
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
func hide(g Gate) int {
	if g.Reason == "missing" {
		return 404
	}
	if g.TeamID%20 == 0 {
		return 403
	}
	return 404
}
func pathInt(w http.ResponseWriter, r *http.Request, n string) (int, bool) {
	v, err := strconv.Atoi(r.PathValue(n))
	if err != nil || v <= 0 {
		problem(w, 400, "bad id")
		return 0, false
	}
	return v, true
}
func badHost(raw string) string {
	u, err := url.Parse(raw)
	if err != nil {
		return ""
	}
	return strings.ToLower(u.Hostname())
}
func envDump() []string { return os.Environ() }
