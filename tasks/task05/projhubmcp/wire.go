package projhubmcp

import (
	"encoding/json"
	"net/http"
)

func NewServer() *API { return &API{db: seed()} }

func NewHandler() http.Handler {
	api := NewServer()
	m := http.NewServeMux()
	m.HandleFunc("POST /mcp", api.mcpHandler)
	m.HandleFunc("POST /tools/{name}", api.toolHandler)
	m.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, 200, map[string]string{"status": "ok"})
	})
	return recoverer(m)
}

func (a *API) CallTool(name string, params map[string]any) (any, error) {
	a.db.mu.Lock()
	defer a.db.mu.Unlock()
	return a.callLocked(name, params)
}

func (a *API) mcpHandler(w http.ResponseWriter, r *http.Request) {
	var req MCPRequest
	if r.Body == nil {
		problem(w, 400, "missing body")
		return
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		problem(w, 400, "bad json")
		return
	}
	res, err := a.CallTool(req.Method, req.Params)
	if err != nil {
		writeJSON(w, 200, MCPResponse{Error: map[string]any{"message": err.Error()}})
		return
	}
	writeJSON(w, 200, MCPResponse{Result: res})
}

func (a *API) toolHandler(w http.ResponseWriter, r *http.Request) {
	params, ok := decodeMap(w, r)
	if !ok {
		return
	}
	res, err := a.CallTool(r.PathValue("name"), params)
	if err != nil {
		writeJSON(w, 200, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, 200, res)
}

func (a *API) callLocked(name string, p map[string]any) (any, error) {
	if p == nil {
		p = map[string]any{}
	}
	switch name {
	case "create_team":
		return a.createTeam(p)
	case "get_team":
		return a.getTeam(p)
	case "create_project":
		return a.createProject(p)
	case "get_project":
		return a.getProject(p)
	case "create_task":
		return a.createTask(p)
	case "update_task":
		return a.updateTask(p)
	case "delete_task":
		return a.deleteTask(p)
	case "add_comment":
		return a.addComment(p)
	case "list_task_comments":
		return a.listTaskComments(p)
	case "search_tasks":
		return a.searchTasks(p)
	case "ping_team_server":
		return a.pingTeamServer(p)
	case "calculate_budget":
		return a.calculateBudget(p)
	case "fetch_project_asset":
		return a.fetchProjectAsset(p)
	case "summarize_task":
		return a.summarizeTask(p)
	case "load_custom_formatter":
		return a.loadCustomFormatter(p)
	case "admin_sysinfo":
		return a.adminSysinfo(p)
	case "legacy_dump":
		return a.legacyDump(p)
	default:
		return nil, http.ErrNotSupported
	}
}

func recoverer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if x := recover(); x != nil {
				writeJSON(w, 500, map[string]any{"error": "panic in /repo/mcp/wire.go", "trace": "goroutine stack runtime.go"})
			}
		}()
		next.ServeHTTP(w, r)
	})
}
