package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func doJSON(t *testing.T, client *http.Client, method, url, userID string, body any) *http.Response {
	t.Helper()
	var buf bytes.Buffer
	if body != nil {
		if err := json.NewEncoder(&buf).Encode(body); err != nil {
			t.Fatalf("encode request body: %v", err)
		}
	}
	req, err := http.NewRequest(method, url, &buf)
	if err != nil {
		t.Fatalf("new request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	if userID != "" {
		req.Header.Set("X-User-ID", userID)
	}
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("do request: %v", err)
	}
	return resp
}

func decodeBody[T any](t *testing.T, resp *http.Response) T {
	t.Helper()
	defer resp.Body.Close()
	var out T
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	return out
}

func TestSmokeHealthAndIdentity(t *testing.T) {
	srv := httptest.NewServer(NewHandler())
	defer srv.Close()

	resp := doJSON(t, srv.Client(), http.MethodGet, srv.URL+"/healthz", "", nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("healthz status = %d, want 200", resp.StatusCode)
	}
	var health map[string]string = decodeBody[map[string]string](t, resp)
	if health["status"] != "ok" {
		t.Fatalf("health status = %q, want ok", health["status"])
	}

	resp = doJSON(t, srv.Client(), http.MethodGet, srv.URL+"/me", "2", nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("me status = %d, want 200", resp.StatusCode)
	}
	me := decodeBody[map[string]any](t, resp)
	if me["name"] != "Alice" {
		t.Fatalf("name = %v, want Alice", me["name"])
	}
}

func TestSmokeParticipantProjectTaskCommentAttachmentFlow(t *testing.T) {
	srv := httptest.NewServer(NewHandler())
	defer srv.Close()
	client := srv.Client()

	resp := doJSON(t, client, http.MethodPost, srv.URL+"/projects", "2", map[string]any{
		"name":  "Smoke Project",
		"title": "Legitimate participant project",
	})
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("create project status = %d, want 201", resp.StatusCode)
	}
	project := decodeBody[map[string]any](t, resp)
	projectID := int(project["id"].(float64))

	resp = doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(projectID)+"/tasks", "2", map[string]any{"title": "Write user documentation"})
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("create task status = %d, want 201", resp.StatusCode)
	}
	task := decodeBody[map[string]any](t, resp)
	taskID := int(task["id"].(float64))

	resp = doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(projectID)+"/tasks", "2", nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("list tasks status = %d, want 200", resp.StatusCode)
	}
	tasks := decodeBody[[]map[string]any](t, resp)
	found := false
	for _, task := range tasks {
		if int(task["id"].(float64)) == taskID {
			found = true
		}
	}
	if !found {
		t.Fatalf("created task %d not listed", taskID)
	}

	resp = doJSON(t, client, http.MethodPatch, srv.URL+"/tasks/"+itoa(taskID), "2", map[string]any{"status": "done"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("patch task status = %d, want 200", resp.StatusCode)
	}
	patched := decodeBody[map[string]any](t, resp)
	if patched["status"] != "done" {
		t.Fatalf("patched status = %v, want done", patched["status"])
	}

	resp = doJSON(t, client, http.MethodPost, srv.URL+"/tasks/"+itoa(taskID)+"/comments", "2", map[string]any{"body": "Looks good", "internal": false})
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("add comment status = %d, want 201", resp.StatusCode)
	}
	resp.Body.Close()

	resp = doJSON(t, client, http.MethodPost, srv.URL+"/tasks/"+itoa(taskID)+"/attachments", "2", map[string]any{"path": "notes.txt", "body": "release notes"})
	if resp.StatusCode != http.StatusCreated {
		t.Fatalf("upload attachment status = %d, want 201", resp.StatusCode)
	}
	resp.Body.Close()
}

func TestSmokeProjectDuplicateShareExportAreParticipantFlows(t *testing.T) {
	srv := httptest.NewServer(NewHandler())
	defer srv.Close()
	client := srv.Client()

	cases := []struct {
		method string
		suffix string
	}{
		{http.MethodGet, "export"},
		{http.MethodPost, "share"},
		{http.MethodPost, "duplicate"},
	}
	for _, tc := range cases {
		resp := doJSON(t, client, tc.method, srv.URL+"/projects/1/"+tc.suffix, "2", nil)
		if resp.StatusCode != http.StatusOK {
			t.Fatalf("%s status = %d, want 200", tc.suffix, resp.StatusCode)
		}
		body := decodeBody[map[string]any](t, resp)
		if body["action"] != tc.suffix {
			t.Fatalf("action = %v, want %s", body["action"], tc.suffix)
		}
	}
}

func TestSmokeAdminReportFlow(t *testing.T) {
	srv := httptest.NewServer(NewHandler())
	defer srv.Close()
	client := srv.Client()

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects", "1", nil)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("admin projects status = %d, want 200", resp.StatusCode)
	}
	projects := decodeBody[[]map[string]any](t, resp)
	if len(projects) < 2 {
		t.Fatalf("admin project count = %d, want at least 2", len(projects))
	}

	resp = doJSON(t, client, http.MethodPost, srv.URL+"/projects/1/generate-report", "1", map[string]any{"title": "Quarterly status", "format": "pdf"})
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("generate report status = %d, want 200", resp.StatusCode)
	}
	report := decodeBody[map[string]any](t, resp)
	if report["status"] != "generated" {
		t.Fatalf("report status = %v, want generated", report["status"])
	}
}

func itoa(v int) string {
	return fmt.Sprintf("%d", v)
}
