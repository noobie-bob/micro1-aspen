package main

import (
	"net/http"
	"testing"
)

func TestParticipantListProjectsOnlyOwnTeam(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects", aliceUserID, nil)
	requireStatus(t, resp, http.StatusOK)
	body := responseText(t, resp)
	projects := mustSliceMaps(t, body)
	ids := projectIDs(t, projects)

	if _, ok := ids[alphaProjectID]; !ok {
		t.Fatalf("own-team project %d missing from participant listing", alphaProjectID)
	}
	if _, ok := ids[betaProjectID]; ok {
		t.Fatalf("cross-team project %d leaked into participant listing", betaProjectID)
	}
}

func TestParticipantCannotGetCrossTeamProject(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(betaProjectID), aliceUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)
}

func TestParticipantCannotPatchCrossTeamProject(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodPatch, srv.URL+"/projects/"+itoa(betaProjectID), aliceUserID, map[string]any{
		"name": "attacker-controlled-name",
	})
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)

	verify := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(betaProjectID), adminUserID, nil)
	requireStatus(t, verify, http.StatusOK)
	project := decodeBody[map[string]any](t, verify)
	if project["name"] != "Borealis" {
		t.Fatalf("cross-team patch mutated project name: got %v", project["name"])
	}
}

func TestParticipantCannotListCrossTeamProjectTasks(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(betaProjectID)+"/tasks", aliceUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)
}

func TestParticipantCannotGetCrossTeamTask(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(betaTaskID), aliceUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)
}

func TestParticipantCannotPatchCrossTeamTask(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodPatch, srv.URL+"/tasks/"+itoa(betaTaskID), aliceUserID, map[string]any{
		"title": "attacker-edited-title",
	})
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)

	verify := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(betaTaskID), adminUserID, nil)
	requireStatus(t, verify, http.StatusOK)
	task := decodeBody[map[string]any](t, verify)
	if task["title"] != "Migrate DB" {
		t.Fatalf("cross-team patch mutated task title: got %v", task["title"])
	}
}

func TestParticipantCannotDeleteCrossTeamTask(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodDelete, srv.URL+"/tasks/"+itoa(betaTaskID), aliceUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)

	verify := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(betaTaskID), adminUserID, nil)
	requireStatus(t, verify, http.StatusOK)
	_ = decodeBody[map[string]any](t, verify)
}

func TestParticipantCannotReadCrossTeamAttachment(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/attachments/"+alphaAttachmentPath, bobUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)
}
