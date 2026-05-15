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

func TestParticipantCannotUseCrossTeamProjectSurfaces(t *testing.T) {
	srv, client := newProjectHubServer(t)

	tests := []struct {
		name   string
		method string
		path   string
		body   any
	}{
		{name: "project detail", method: http.MethodGet, path: "/projects/" + itoa(betaProjectID)},
		{name: "project task listing", method: http.MethodGet, path: "/projects/" + itoa(betaProjectID) + "/tasks"},
		{name: "project patch", method: http.MethodPatch, path: "/projects/" + itoa(betaProjectID), body: map[string]any{"name": "attacker-controlled-name"}},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			resp := doJSON(t, client, tc.method, srv.URL+tc.path, aliceUserID, tc.body)
			requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
			_ = responseText(t, resp)
		})
	}

	verify := doJSON(t, client, http.MethodGet, srv.URL+"/projects/"+itoa(betaProjectID), adminUserID, nil)
	requireStatus(t, verify, http.StatusOK)
	project := decodeBody[map[string]any](t, verify)
	if project["name"] != "Borealis" {
		t.Fatalf("cross-team patch mutated project name: got %v", project["name"])
	}
}

func TestParticipantCannotUseCrossTeamTaskSurfaces(t *testing.T) {
	srv, client := newProjectHubServer(t)

	tests := []struct {
		name   string
		method string
		body   any
	}{
		{name: "task detail", method: http.MethodGet},
		{name: "task patch", method: http.MethodPatch, body: map[string]any{"title": "attacker-edited-title"}},
		{name: "task delete", method: http.MethodDelete},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			resp := doJSON(t, client, tc.method, srv.URL+"/tasks/"+itoa(betaTaskID), aliceUserID, tc.body)
			requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
			_ = responseText(t, resp)
		})
	}

	verify := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(betaTaskID), adminUserID, nil)
	requireStatus(t, verify, http.StatusOK)
	task := decodeBody[map[string]any](t, verify)
	if task["title"] != "Migrate DB" {
		t.Fatalf("cross-team patch mutated task title: got %v", task["title"])
	}
}

func TestParticipantCannotReadCrossTeamAttachment(t *testing.T) {
	srv, client := newProjectHubServer(t)

	resp := doJSON(t, client, http.MethodGet, srv.URL+"/tasks/"+itoa(alphaTaskID)+"/attachments/"+alphaAttachmentPath, bobUserID, nil)
	requireStatusOneOf(t, resp, http.StatusForbidden, http.StatusNotFound)
	_ = responseText(t, resp)
}
