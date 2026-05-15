package main

import (
	"net/http"
	"strings"
	"testing"
)

func assertProjectFieldsRedacted(t *testing.T, project map[string]any) {
	t.Helper()
	if value, ok := project["internal_metrics"]; ok && value != "" && value != nil {
		t.Fatalf("internal_metrics leaked to participant: %v", value)
	}
	if value, ok := project["admin_config"]; ok && value != "" && value != nil {
		t.Fatalf("admin_config leaked to participant: %v", value)
	}
	if value, ok := project["budget_allocation"]; ok {
		if number, ok := value.(float64); !ok || number != 0 {
			t.Fatalf("budget_allocation leaked to participant: %v", value)
		}
	}
}

func assertTaskFieldsRedacted(t *testing.T, task map[string]any) {
	t.Helper()
	if value, ok := task["internal_priority"]; ok {
		if number, ok := value.(float64); !ok || number != 0 {
			t.Fatalf("internal_priority leaked to participant: %v", value)
		}
	}
	if value, ok := task["reviewer_notes"]; ok && value != "" && value != nil {
		t.Fatalf("reviewer_notes leaked to participant: %v", value)
	}
	if value, ok := task["security_classification"]; ok && value != "" && value != nil {
		t.Fatalf("security_classification leaked to participant: %v", value)
	}
	if value, ok := task["estimated_cost"]; ok {
		if number, ok := value.(float64); !ok || number != 0 {
			t.Fatalf("estimated_cost leaked to participant: %v", value)
		}
	}
}

func assertBundleRedacted(t *testing.T, body string) {
	t.Helper()
	bundle := mustMap(t, body)
	project := nestedMap(t, bundle, "project")
	assertProjectFieldsRedacted(t, project)
	for _, task := range nestedSliceMaps(t, bundle, "tasks") {
		assertTaskFieldsRedacted(t, task)
	}
	if strings.Contains(body, sentinelInternalMetricsA) ||
		strings.Contains(body, sentinelAdminConfigA) ||
		strings.Contains(body, sentinelReviewerNotesA) ||
		strings.Contains(body, sentinelInternalComment) {
		t.Fatalf("participant bundle leaked sentinel marker bytes: %s", body)
	}
}

func TestParticipantProjectDetailRedactsAdminFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(alphaProjectID), aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	project := mustMap(t, body)
	assertProjectFieldsRedacted(t, project)

	if strings.Contains(body, sentinelInternalMetricsA) || strings.Contains(body, sentinelAdminConfigA) || strings.Contains(body, "90000") {
		t.Fatalf("participant project detail leaked project sentinel data: %s", body)
	}
}

func TestParticipantTaskViewsRedactSensitiveFieldsAndInternalComments(t *testing.T) {
	srv, client := newProjectHubServer(t)

	taskResp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID), aliceUserID, nil)
	requireStatus(t, taskResp, http.StatusOK)
	taskBody := responseText(t, taskResp)
	task := mustMap(t, taskBody)
	assertTaskFieldsRedacted(t, task)
	if strings.Contains(taskBody, sentinelReviewerNotesA) || strings.Contains(taskBody, "1200") || strings.Contains(taskBody, "secret") {
		t.Fatalf("participant task detail leaked task sentinel data: %s", taskBody)
	}

	commentsResp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/comments", aliceUserID, nil)
	requireStatus(t, commentsResp, http.StatusOK)
	commentsBody := responseText(t, commentsResp)
	comments := mustSliceMaps(t, commentsBody)

	seenPublicComment := false
	for _, comment := range comments {
		if body, ok := comment["body"].(string); ok && body == "public kickoff" {
			seenPublicComment = true
		}
		if internal, ok := comment["internal"].(bool); ok && internal {
			t.Fatalf("internal comment leaked to participant: %v", comment)
		}
	}
	if !seenPublicComment {
		t.Fatalf("public comment missing from participant response")
	}
	if strings.Contains(commentsBody, sentinelInternalComment) {
		t.Fatalf("participant comment listing leaked sentinel internal comment: %s", commentsBody)
	}
}

func TestParticipantProjectBundlesRedactSensitiveFieldsAcrossActions(t *testing.T) {
	srv, client := newProjectHubServer(t)

	tests := []struct {
		name   string
		method string
		path   string
	}{
		{name: "export", method: http.MethodGet, path: "/projects/" + itoa(alphaProjectID) + "/export"},
		{name: "share", method: http.MethodPost, path: "/projects/" + itoa(alphaProjectID) + "/share"},
		{name: "duplicate", method: http.MethodPost, path: "/projects/" + itoa(alphaProjectID) + "/duplicate"},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			resp := doJSON(t, client, tc.method, srv.URL+tc.path, aliceUserID, nil)
			requireStatus(t, resp, http.StatusOK)
			body := responseText(t, resp)
			assertBundleRedacted(t, body)
		})
	}
}
