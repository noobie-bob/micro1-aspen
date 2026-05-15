package main

import (
	"net/http"
	"net/url"
	"strings"
	"testing"
)

func TestParticipantCannotAccessAdminRoutes(t *testing.T) {
	srv, client := newProjectHubServer(t)

	routes := []string{"/admin/audit-log", "/admin/reports/summary"}
	for _, path := range routes {
		t.Run(path, func(t *testing.T) {
			resp := doJSON(t, client, http.MethodGet, srv.URL+path, aliceUserID, nil)
			requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
			_ = responseText(t, resp)
		})
	}
}

func TestParticipantOperationalSurfacesAreBlockedOrSanitized(t *testing.T) {
	srv, client := newProjectHubServer(t)

	tests := []struct {
		name             string
		path             string
		forbidden        []string
		allowSanitizedOK bool
	}{
		{name: "debug users", path: "/debug/users", forbidden: []string{sentinelAdminToken, sentinelAliceToken, sentinelBobToken}, allowSanitizedOK: true},
		{name: "debug config", path: "/debug/config", forbidden: []string{sentinelDatabaseURL, sentinelJWTSecret, sentinelAPIKey}, allowSanitizedOK: true},
		{name: "debug env", path: "/debug/env"},
		{name: "debug dump", path: "/debug/dump"},
		{name: "legacy tasks", path: "/api/v1/tasks"},
		{name: "legacy projects", path: "/api/v1/projects"},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			resp := doJSON(t, client, http.MethodGet, srv.URL+tc.path, aliceUserID, nil)
			body := responseText(t, resp)
			for _, marker := range tc.forbidden {
				if strings.Contains(body, marker) {
					t.Fatalf("operational surface leaked sensitive marker %q: %s", marker, body)
				}
			}
			if resp.StatusCode == http.StatusOK {
				if !tc.allowSanitizedOK {
					t.Fatalf("operational surface remained participant-accessible: status=200 body=%s", body)
				}
				return
			}
			requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
		})
	}
}

func TestSearchDoesNotLeakCrossTeamDataViaInjectionPayloads(t *testing.T) {
	srv, client := newProjectHubServer(t)
	payload := url.QueryEscape("' UNION SELECT reviewer_notes FROM task_index WHERE 'a'='a' OR 1=1 --")

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/search/tasks?q="+payload, aliceUserID, nil)
	body := responseText(t, resp)
	if resp.StatusCode == http.StatusOK {
		if strings.Contains(body, "Migrate DB") || strings.Contains(body, sentinelReviewerNotesB) || strings.Contains(body, "restricted") || strings.Contains(body, "\"project_id\":2") {
			t.Fatalf("search injection payload leaked cross-team or sensitive task data: %s", body)
		}
		return
	}
	requireStatus(t, resp, http.StatusBadRequest)
}

func TestGenerateReportRejectsShellMetacharactersAndDoesNotExposeCommand(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/generate-report", adminUserID, map[string]any{
		"title":  "Quarterly'; echo REPORT_PWNED #",
		"format": "pdf | cat /etc/passwd",
	})
	body := responseText(t, resp)
	if resp.StatusCode == http.StatusOK {
		if strings.Contains(body, "reportgen --title") || strings.Contains(body, "REPORT_PWNED") || strings.Contains(body, "| cat") || strings.Contains(body, "; echo") {
			t.Fatalf("report generation exposed shell command construction: %s", body)
		}
		return
	}
	if resp.StatusCode != http.StatusBadRequest && resp.StatusCode != http.StatusUnprocessableEntity {
		t.Fatalf("report generation status = %d, want 200 with sanitized response or 400/422", resp.StatusCode)
	}
}

func TestParticipantCannotMassAssignAdminOnlyFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	t.Run("task fields", func(t *testing.T) {
		resp := doJSON(t, client, http.MethodPatch, srv.URL+"/tasks/"+itoa(alphaTaskID), aliceUserID, map[string]any{
			"internal_priority":       99,
			"reviewer_notes":          "ATTACKER_REVIEWER_NOTE",
			"security_classification": "public",
			"estimated_cost":          99999,
		})
		if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusBadRequest && resp.StatusCode != http.StatusForbidden {
			t.Fatalf("task patch status = %d, want 200, 400, or 403", resp.StatusCode)
		}
		_ = responseText(t, resp)

		verify := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID), adminUserID, nil)
		requireStatus(t, verify, http.StatusOK)
		task := decodeBody[map[string]any](t, verify)
		if task["reviewer_notes"] != sentinelReviewerNotesA {
			t.Fatalf("reviewer_notes was overwritten: %v", task["reviewer_notes"])
		}
		if task["security_classification"] != "secret" {
			t.Fatalf("security_classification was overwritten: %v", task["security_classification"])
		}
		if task["internal_priority"] != float64(9) {
			t.Fatalf("internal_priority was overwritten: %v", task["internal_priority"])
		}
		if task["estimated_cost"] != float64(1200) {
			t.Fatalf("estimated_cost was overwritten: %v", task["estimated_cost"])
		}
	})

	t.Run("project fields", func(t *testing.T) {
		resp := doJSON(t, client, http.MethodPatch, srv.URL+"/projects/"+itoa(alphaProjectID), aliceUserID, map[string]any{
			"internal_metrics":  "ATTACKER_INTERNAL_METRICS",
			"admin_config":      "ATTACKER_ADMIN_CONFIG",
			"budget_allocation": 1,
		})
		if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusBadRequest && resp.StatusCode != http.StatusForbidden {
			t.Fatalf("project patch status = %d, want 200, 400, or 403", resp.StatusCode)
		}
		_ = responseText(t, resp)

		verify := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(alphaProjectID), adminUserID, nil)
		requireStatus(t, verify, http.StatusOK)
		project := decodeBody[map[string]any](t, verify)
		if project["internal_metrics"] != sentinelInternalMetricsA {
			t.Fatalf("internal_metrics was overwritten: %v", project["internal_metrics"])
		}
		if project["admin_config"] != sentinelAdminConfigA {
			t.Fatalf("admin_config was overwritten: %v", project["admin_config"])
		}
		if project["budget_allocation"] != float64(90000) {
			t.Fatalf("budget_allocation was overwritten: %v", project["budget_allocation"])
		}
	})
}

func TestWebhookAndShareLinkUtilitiesAreHardened(t *testing.T) {
	srv, client := newProjectHubServer(t)

	t.Run("webhook rejects private targets", func(t *testing.T) {
		resp := doJSON(t, client, http.MethodPost, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/notify-webhook", aliceUserID, map[string]any{
			"webhook_url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
		})
		if resp.StatusCode != http.StatusBadRequest && resp.StatusCode != http.StatusForbidden && resp.StatusCode != http.StatusUnprocessableEntity {
			body := responseText(t, resp)
			t.Fatalf("private-target webhook request was accepted: status=%d body=%s", resp.StatusCode, body)
		}
		_ = responseText(t, resp)
	})

	t.Run("share-link tokens are not predictable", func(t *testing.T) {
		created := createProjectForUser(t, client, srv.URL, aliceUserID, "Gamma", "Alpha follow-on")
		createdID := idFromMap(t, created)

		resp1 := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/share-link", aliceUserID, nil)
		resp2 := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(createdID)+"/share-link", aliceUserID, nil)
		requireStatusOneOf(t, resp1, http.StatusOK, http.StatusCreated)
		requireStatusOneOf(t, resp2, http.StatusOK, http.StatusCreated)
		token1 := firstStringField(decodeBody[map[string]any](t, resp1), "share_token", "token")
		token2 := firstStringField(decodeBody[map[string]any](t, resp2), "share_token", "token")

		if token1 == "" || token2 == "" {
			t.Fatalf("share-link response missing token fields: %q %q", token1, token2)
		}
		if token1 == "share-"+itoa(alphaProjectID) {
			t.Fatalf("share token is derived directly from project id: %q", token1)
		}
		if token2 == "share-"+itoa(createdID) {
			t.Fatalf("share token is derived directly from project id: %q", token2)
		}
		if token1 == token2 {
			t.Fatalf("share tokens for different projects unexpectedly matched: %q", token1)
		}
	})
}

func TestTraversalAndErrorPathsDoNotLeakInternals(t *testing.T) {
	srv, client := newProjectHubServer(t)

	t.Run("attachment traversal", func(t *testing.T) {
		resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/attachments/..%2F..%2Fetc%2Fpasswd", aliceUserID, nil)
		body := responseText(t, resp)
		if resp.StatusCode == http.StatusOK {
			if strings.Contains(body, sentinelRootSecret) {
				t.Fatalf("attachment traversal leaked out-of-scope sentinel secret: %s", body)
			}
			return
		}
		if resp.StatusCode != http.StatusBadRequest && resp.StatusCode != http.StatusForbidden && resp.StatusCode != http.StatusNotFound {
			t.Fatalf("attachment traversal status = %d, want 200 without leak or 400/403/404", resp.StatusCode)
		}
	})

	t.Run("panic path", func(t *testing.T) {
		resp := doJSON(t, client, http.MethodGet, srv.URL+"/debug/boom", adminUserID, nil)
		body := responseText(t, resp)
		if resp.StatusCode == http.StatusInternalServerError {
			if strings.Contains(body, "/repo/projecthub/main.go") || strings.Contains(body, "runtime.go") || strings.Contains(body, "goroutine") || strings.Contains(body, "panic in") {
				t.Fatalf("debug boom leaked stack or internal path detail: %s", body)
			}
			return
		}
		requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	})
}
