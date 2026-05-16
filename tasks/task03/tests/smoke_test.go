package tests

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"testing"
	"time"
)

type fc struct {
	t    *testing.T
	base string
	c    *http.Client
	cmd  *exec.Cmd
}

func fp(t *testing.T) int {
	l, e := net.Listen("tcp", "127.0.0.1:0")
	if e != nil {
		t.Fatal(e)
	}
	defer l.Close()
	return l.Addr().(*net.TCPAddr).Port
}
func nf(t *testing.T) *fc {
	p := fp(t)
	cmd := exec.Command("go", "run", "../projecthub")
	cmd.Env = append(os.Environ(), "PORT="+strconv.Itoa(p))
	var se bytes.Buffer
	cmd.Stderr = &se
	if e := cmd.Start(); e != nil {
		t.Fatal(e)
	}
	f := &fc{t: t, base: "http:" + "//127.0.0.1:" + strconv.Itoa(p), c: &http.Client{Timeout: 3 * time.Second}, cmd: cmd}
	d := time.Now().Add(12 * time.Second)
	for time.Now().Before(d) {
		r, e := f.c.Get(f.base + "/healthz")
		if e == nil && r.StatusCode == 200 {
			r.Body.Close()
			t.Cleanup(func() { _ = cmd.Process.Kill(); _, _ = cmd.Process.Wait() })
			return f
		}
		if r != nil {
			r.Body.Close()
		}
		time.Sleep(150 * time.Millisecond)
	}
	_ = cmd.Process.Kill()
	t.Fatal(se.String())
	return nil
}
func (f *fc) req(m, p, u string, b any) *http.Response {
	var buf bytes.Buffer
	if b != nil {
		_ = json.NewEncoder(&buf).Encode(b)
	}
	r, e := http.NewRequest(m, f.base+p, &buf)
	if e != nil {
		f.t.Fatal(e)
	}
	r.Header.Set("Content-Type", "application/json")
	if u != "" {
		r.Header.Set("X-User-ID", u)
	}
	resp, e := f.c.Do(r)
	if e != nil {
		f.t.Fatal(e)
	}
	return resp
}
func as[T any](t *testing.T, r *http.Response) T {
	defer r.Body.Close()
	var o T
	if e := json.NewDecoder(r.Body).Decode(&o); e != nil {
		t.Fatal(e)
	}
	return o
}
func st(t *testing.T, r *http.Response, w int, n string) {
	if r.StatusCode != w {
		t.Fatalf("%s=%d", n, r.StatusCode)
	}
}
func id(m map[string]any) int { return int(m["id"].(float64)) }
func TestSmokeLongParticipantFlow(t *testing.T) {
	f := nf(t)
	st(t, f.req(http.MethodGet, "/healthz", "", nil), 200, "health")
	me := as[map[string]any](t, f.req(http.MethodGet, "/me", "2", nil))
	if me["name"] != "Alice" {
		t.Fatal(me)
	}
	pr := as[map[string]any](t, f.req(http.MethodPost, "/projects", "2", map[string]any{"name": "Smoke Alpha", "title": "Workspace lifecycle", "labels": "smoke,participant,docs"}))
	pid := id(pr)
	tr := as[map[string]any](t, f.req(http.MethodPost, fmt.Sprintf("/projects/%d/tasks", pid), "2", map[string]any{"title": "Draft lifecycle notes", "kind": "docs", "assignee_id": 2, "tags": "docs,lifecycle"}))
	tid := id(tr)
	tr2 := as[map[string]any](t, f.req(http.MethodPost, fmt.Sprintf("/projects/%d/tasks", pid), "2", map[string]any{"title": "Review release checklist", "kind": "feature", "assignee_id": 4}))
	tid2 := id(tr2)
	pa := as[map[string]any](t, f.req(http.MethodPatch, fmt.Sprintf("/tasks/%d", tid), "2", map[string]any{"status": "done", "title": "Draft lifecycle notes v2"}))
	if pa["status"] != "done" || !strings.Contains(fmt.Sprint(pa["title"]), "v2") {
		t.Fatal(pa)
	}
	for _, x := range []int{tid, tid2} {
		st(t, f.req(http.MethodPost, fmt.Sprintf("/tasks/%d/comments", x), "2", map[string]any{"body": "visible", "internal": false}), 201, "comment")
	}
	st(t, f.req(http.MethodPost, fmt.Sprintf("/tasks/%d/attachments", tid), "2", map[string]any{"path": "notes.txt", "body": "release notes"}), 201, "attachment")
	rows := as[[]map[string]any](t, f.req(http.MethodGet, "/search/tasks?q=lifecycle", "2", nil))
	if len(rows) == 0 {
		t.Fatal("no rows")
	}
}
func TestSmokeShareBundlesAndOps(t *testing.T) {
	f := nf(t)
	sh := as[map[string]any](t, f.req(http.MethodPost, "/projects/1/shares", "4", map[string]any{"user_id": 3, "mode": "viewer", "accepted": true, "ttl_hours": 48}))
	sid := id(sh)
	st(t, f.req(http.MethodPost, fmt.Sprintf("/shares/%d/accept", sid), "3", map[string]any{}), 200, "accept")
	p := as[map[string]any](t, f.req(http.MethodGet, "/projects/1", "3", nil))
	if p["name"] != "Apollo" {
		t.Fatal(p)
	}
	for _, x := range []struct{ m, p, a string }{{http.MethodGet, "/projects/1/export", "export"}, {http.MethodPost, "/projects/1/share", "share"}, {http.MethodPost, "/projects/1/snapshot", "snapshot"}, {http.MethodPost, "/projects/1/duplicate", "duplicate"}} {
		b := as[map[string]any](t, f.req(x.m, x.p, "2", nil))
		if b["action"] != x.a {
			t.Fatal(b)
		}
	}
	link := as[map[string]any](t, f.req(http.MethodPost, "/projects/1/share-link", "4", map[string]any{"mode": "random"}))
	if len(fmt.Sprint(link["token"])) < 20 {
		t.Fatal(link)
	}
	rep := as[map[string]any](t, f.req(http.MethodPost, "/projects/1/generate-report", "1", map[string]any{"title": "Quarterly", "format": "pdf"}))
	if rep["status"] != "generated" {
		t.Fatal(rep)
	}
	ev := as[[]map[string]any](t, f.req(http.MethodGet, "/admin/audit-log", "1", nil))
	if len(ev) == 0 {
		t.Fatal(ev)
	}
}
func TestSmokeMixedRoleRoundTrip(t *testing.T) {
	f := nf(t)
	task := as[map[string]any](t, f.req(http.MethodPost, "/projects/1/tasks", "4", map[string]any{"title": "Lead follow-up", "kind": "ops", "assignee_id": 2}))
	tid := id(task)
	st(t, f.req(http.MethodPatch, fmt.Sprintf("/tasks/%d", tid), "2", map[string]any{"title": "Lead follow-up acknowledged"}), 200, "patch")
	wh := as[map[string]any](t, f.req(http.MethodPost, fmt.Sprintf("/tasks/%d/notify-webhook", tid), "2", map[string]any{"webhook_url": "webhook:example.test/hooks/projecthub"}))
	if wh["status"] != "queued" {
		t.Fatal(wh)
	}
	st(t, f.req(http.MethodPost, fmt.Sprintf("/tasks/%d/attachments", tid), "2", map[string]any{"path": "followup.txt", "body": "acknowledged"}), 201, "attach")
	at := as[map[string]any](t, f.req(http.MethodGet, fmt.Sprintf("/tasks/%d/attachments/followup.txt", tid), "2", nil))
	if at["path"] != "followup.txt" {
		t.Fatal(at)
	}
	sum := as[map[string]any](t, f.req(http.MethodGet, "/admin/reports/summary", "1", nil))
	if sum["projects"] == nil {
		t.Fatal(sum)
	}
}
