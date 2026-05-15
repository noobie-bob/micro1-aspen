package main

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"
)

const (
	adminUserID = "1"
	aliceUserID = "2"
	bobUserID   = "3"

	alphaProjectID = 1
	betaProjectID  = 2
	alphaTaskID    = 1
	betaTaskID     = 2

	alphaAttachmentPath = "readme.txt"

	sentinelInternalMetricsA = "SENTINEL_INTERNAL_METRICS_A"
	sentinelInternalMetricsB = "SENTINEL_INTERNAL_METRICS_B"
	sentinelAdminConfigA     = "SENTINEL_ADMIN_CONFIG_A"
	sentinelAdminConfigB     = "SENTINEL_ADMIN_CONFIG_B"
	sentinelReviewerNotesA   = "SENTINEL_REVIEWER_NOTES_A"
	sentinelReviewerNotesB   = "SENTINEL_REVIEWER_NOTES_B"
	sentinelInternalComment  = "SENTINEL_INTERNAL_COMMENT"
	sentinelRootSecret       = "SENTINEL_ROOT_SECRET"

	sentinelDatabaseURL = "postgres://projecthub:secret@db/prod"
	sentinelJWTSecret   = "dev-secret"
	sentinelAPIKey      = "debug-key"
	sentinelAdminToken  = "adm-token-plaintext"
	sentinelAliceToken  = "alice-token-plaintext"
	sentinelBobToken    = "bob-token-plaintext"
)

func newProjectHubServer(t *testing.T) (*httptest.Server, *http.Client) {
	t.Helper()
	srv := httptest.NewServer(NewHandler())
	t.Cleanup(srv.Close)
	return srv, srv.Client()
}

func responseText(t *testing.T, resp *http.Response) string {
	t.Helper()
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("read response body: %v", err)
	}
	return string(body)
}

func mustMap(t *testing.T, body string) map[string]any {
	t.Helper()
	var out map[string]any
	if err := json.Unmarshal([]byte(body), &out); err != nil {
		t.Fatalf("decode object body: %v\nbody=%s", err, body)
	}
	return out
}

func mustSliceMaps(t *testing.T, body string) []map[string]any {
	t.Helper()
	var out []map[string]any
	if err := json.Unmarshal([]byte(body), &out); err != nil {
		t.Fatalf("decode array body: %v\nbody=%s", err, body)
	}
	return out
}

func nestedMap(t *testing.T, parent map[string]any, key string) map[string]any {
	t.Helper()
	raw, ok := parent[key]
	if !ok {
		t.Fatalf("expected key %q in response object", key)
	}
	child, ok := raw.(map[string]any)
	if !ok {
		t.Fatalf("expected key %q to be an object, got %T", key, raw)
	}
	return child
}

func nestedSliceMaps(t *testing.T, parent map[string]any, key string) []map[string]any {
	t.Helper()
	raw, ok := parent[key]
	if !ok {
		t.Fatalf("expected key %q in response object", key)
	}
	items, ok := raw.([]any)
	if !ok {
		t.Fatalf("expected key %q to be an array, got %T", key, raw)
	}
	out := make([]map[string]any, 0, len(items))
	for _, item := range items {
		child, ok := item.(map[string]any)
		if !ok {
			t.Fatalf("expected array item to be an object, got %T", item)
		}
		out = append(out, child)
	}
	return out
}

func requireStatus(t *testing.T, resp *http.Response, want int) {
	t.Helper()
	if resp.StatusCode != want {
		t.Fatalf("status = %d, want %d", resp.StatusCode, want)
	}
}

func requireStatusOneOf(t *testing.T, resp *http.Response, wants ...int) {
	t.Helper()
	for _, want := range wants {
		if resp.StatusCode == want {
			return
		}
	}
	t.Fatalf("status = %d, want one of %v", resp.StatusCode, wants)
}

func idFromMap(t *testing.T, item map[string]any) int {
	t.Helper()
	raw, ok := item["id"]
	if !ok {
		t.Fatalf("expected id field in response object")
	}
	value, ok := raw.(float64)
	if !ok {
		t.Fatalf("expected id field to be numeric, got %T", raw)
	}
	return int(value)
}

func projectIDs(t *testing.T, projects []map[string]any) map[int]struct{} {
	t.Helper()
	ids := make(map[int]struct{}, len(projects))
	for _, project := range projects {
		ids[idFromMap(t, project)] = struct{}{}
	}
	return ids
}

func createProjectForUser(t *testing.T, client *http.Client, baseURL, userID, name, title string) map[string]any {
	t.Helper()
	resp := doJSON(t, client, http.MethodPost, baseURL+"/projects", userID, map[string]any{
		"name":  name,
		"title": title,
	})
	requireStatus(t, resp, http.StatusCreated)
	return decodeBody[map[string]any](t, resp)
}

func createTaskForProject(t *testing.T, client *http.Client, baseURL, userID string, projectID int, title string) map[string]any {
	t.Helper()
	resp := doJSON(t, client, http.MethodPost, baseURL+"/projects/"+itoa(projectID)+"/tasks", userID, map[string]any{
		"title": title,
	})
	requireStatus(t, resp, http.StatusCreated)
	return decodeBody[map[string]any](t, resp)
}

func firstStringField(data map[string]any, keys ...string) string {
	for _, key := range keys {
		if raw, ok := data[key]; ok {
			if value, ok := raw.(string); ok {
				return value
			}
		}
	}
	return ""
}