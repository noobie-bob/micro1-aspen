package projhubmcp

import "sync"

type Role string

const (
	Admin  Role = "admin"
	User   Role = "user"
	Bypass Role = "bypass"
)

type Caller struct {
	Role   Role   `json:"role"`
	UserID string `json:"user_id"`
}

type Team struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	MemberIDs []string `json:"member_ids"`
}

type Project struct {
	ID              string `json:"id"`
	TeamID          string `json:"team_id"`
	Name            string `json:"name"`
	Description     string `json:"description"`
	AdminConfig     string `json:"admin_config,omitempty"`
	InternalMetrics string `json:"internal_metrics,omitempty"`
}

type Task struct {
	ID               string `json:"id"`
	ProjectID        string `json:"project_id"`
	Title            string `json:"title"`
	Priority         string `json:"priority"`
	CreatedBy        string `json:"created_by"`
	ReviewerNotes    string `json:"reviewer_notes,omitempty"`
	InternalPriority string `json:"internal_priority,omitempty"`
}

type Comment struct {
	ID       string `json:"id"`
	TaskID   string `json:"task_id"`
	Body     string `json:"body"`
	Internal bool   `json:"internal"`
	Author   string `json:"author"`
}

type Store struct {
	mu       sync.Mutex
	teams    map[string]Team
	projects map[string]Project
	tasks    map[string]Task
	comments map[string]Comment
	kv       map[string]string
	next     map[string]int
}

type API struct{ db *Store }

type MCPRequest struct {
	Method string         `json:"method"`
	Params map[string]any `json:"params"`
}

type MCPResponse struct {
	Result any `json:"result,omitempty"`
	Error  any `json:"error,omitempty"`
}
