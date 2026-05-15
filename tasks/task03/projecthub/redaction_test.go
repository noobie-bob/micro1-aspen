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

func TestParticipantTaskDetailRedactsAdminFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID), aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	task := mustMap(t, body)
	assertTaskFieldsRedacted(t, task)

	if strings.Contains(body, sentinelReviewerNotesA) || strings.Contains(body, "1200") || strings.Contains(body, "secret") {
		t.Fatalf("participant task detail leaked task sentinel data: %s", body)
	}
}

func TestParticipantCommentsHideInternalEntries(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/comments", aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	comments := mustSliceMaps(t, body)

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
	if strings.Contains(body, sentinelInternalComment) {
		t.Fatalf("participant comment listing leaked sentinel internal comment: %s", body)
	}
}

func TestParticipantExportRedactsBundleFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(alphaProjectID)+"/export", aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	assertBundleRedacted(t, body)
}

func TestParticipantShareRedactsBundleFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/share", aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	assertBundleRedacted(t, body)
}

func TestParticipantDuplicateRedactsBundleFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/duplicate", aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	assertBundleRedacted(t, body)
}