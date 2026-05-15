package main

import (
	"net/http"
	"strings"
	"testing"
)

func TestAdminProjectsStillShowAllTeamsWithAdminFields(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects", adminUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	projects := mustSliceMaps(t, body)
	ids := projectIDs(t, projects)

	if _, ok := ids[alphaProjectID]; !ok {
		t.Fatalf("admin listing missing project %d", alphaProjectID)
	}
	if _, ok := ids[betaProjectID]; !ok {
		t.Fatalf("admin listing missing project %d", betaProjectID)
	}
	if !strings.Contains(body, sentinelInternalMetricsA) || !strings.Contains(body, sentinelAdminConfigA) || !strings.Contains(body, sentinelInternalMetricsB) || !strings.Contains(body, sentinelAdminConfigB) {
		t.Fatalf("admin listing lost full admin detail: %s", body)
	}
}

func TestParticipantCanStillAccessOwnProjectAndTask(t *testing.T) {
	srv, client := newProjectHubServer(t)

	projectResp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(alphaProjectID), aliceUserID, nil)
	requireStatus(t, projectResp, http.StatusOK)
	_ = responseText(t, projectResp)

	taskResp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID), aliceUserID, nil)
	requireStatus(t, taskResp, http.StatusOK)
	_ = responseText(t, taskResp)
}

func TestParticipantCanStillCreateCommentAndUploadInOwnTeam(t *testing.T) {
	srv, client := newProjectHubServer(t)
	project := createProjectForUser(t, client, srv.URL, aliceUserID, "Delta", "Own team expansion")
	projectID := idFromMap(t, project)
	task := createTaskForProject(t, client, srv.URL, aliceUserID, projectID, "Write rollout checklist")
	taskID := idFromMap(t, task)

	commentResp := doJSON(t, client, http.MethodPost, srv.URL+"/tasks/"+itoa(taskID)+"/comments", aliceUserID, map[string]any{
		"body": "looks ready",
	})
	requireStatus(t, commentResp, http.StatusCreated)
	_ = responseText(t, commentResp)

	attachmentResp := doJSON(t, client, http.MethodPost, srv.URL+"/tasks/"+itoa(taskID)+"/attachments", aliceUserID, map[string]any{
		"path": "notes.txt",
		"body": "participant upload body",
	})
	requireStatus(t, attachmentResp, http.StatusCreated)
	_ = responseText(t, attachmentResp)
}

func TestParticipantCanStillDuplicateShareAndExportOwnProject(t *testing.T) {
	srv, client := newProjectHubServer(t)

	exportResp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(alphaProjectID)+"/export", aliceUserID, nil)
	requireStatus(t, exportResp, http.StatusOK)
	_ = responseText(t, exportResp)

	shareResp := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/share", aliceUserID, nil)
	requireStatus(t, shareResp, http.StatusOK)
	_ = responseText(t, shareResp)

	duplicateResp := doJSON(t, client, http.MethodPost, srv.URL+"/projects/"+itoa(alphaProjectID)+"/duplicate", aliceUserID, nil)
	requireStatus(t, duplicateResp, http.StatusOK)
	_ = responseText(t, duplicateResp)
}