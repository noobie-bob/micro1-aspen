package main

import (
	"net/http"
	"sync"
	"time"
)

type Role string
type Zone string
type Stamp string

const (
	Admin Role = "admin"
	Lead Role = "lead"
	Participant Role = "participant"
	Auditor Role = "auditor"
	Guest Role = "guest"
	ZonePublic Zone = "public"
	ZoneInternal Zone = "internal"
	ZoneSecret Zone = "secret"
)

type User struct {
	ID int `json:"id"`
	Name string `json:"name"`
	TeamID int `json:"team_id"`
	Role Role `json:"role"`
	Token string `json:"api_token,omitempty"`
	Zone Zone `json:"zone,omitempty"`
	Flags []string `json:"flags,omitempty"`
	Disabled bool `json:"disabled,omitempty"`
}

type Team struct {
	ID int `json:"id"`
	Name string `json:"name"`
	ParentID int `json:"parent_id"`
	Region string `json:"region"`
	LedgerCode string `json:"ledger_code,omitempty"`
}

type ProjectMeta struct {
	InternalMetrics string `json:"internal_metrics,omitempty"`
	AdminConfig string `json:"admin_config,omitempty"`
	BudgetAllocation int `json:"budget_allocation,omitempty"`
	CostCenter string `json:"cost_center,omitempty"`
	ArchiveKey string `json:"archive_key,omitempty"`
	LegalHold string `json:"legal_hold,omitempty"`
}

type Project struct {
	ID int `json:"id"`
	TeamID int `json:"team_id"`
	OwnerID int `json:"owner_id"`
	MirrorOf int `json:"mirror_of,omitempty"`
	Name string `json:"name"`
	Title string `json:"title"`
	Status string `json:"status"`
	Visibility string `json:"visibility"`
	Tier int `json:"tier"`
	Labels []string `json:"labels,omitempty"`
	Meta ProjectMeta `json:"meta,omitempty"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type TaskSecret struct {
	InternalPriority int `json:"internal_priority,omitempty"`
	ReviewerNotes string `json:"reviewer_notes,omitempty"`
	SecurityClassification string `json:"security_classification,omitempty"`
	EstimatedCost int `json:"estimated_cost,omitempty"`
	RiskScore int `json:"risk_score,omitempty"`
	EscalationKey string `json:"escalation_key,omitempty"`
}

type Task struct {
	ID int `json:"id"`
	ProjectID int `json:"project_id"`
	TeamID int `json:"team_id"`
	CreatedBy int `json:"created_by"`
	AssigneeID int `json:"assignee_id"`
	ParentTaskID int `json:"parent_task_id,omitempty"`
	Title string `json:"title"`
	Status string `json:"status"`
	Kind string `json:"kind"`
	DueDate string `json:"due_date,omitempty"`
	Tags []string `json:"tags,omitempty"`
	Secret TaskSecret `json:"secret,omitempty"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type Comment struct {
	ID int `json:"id"`
	TaskID int `json:"task_id"`
	ProjectID int `json:"project_id"`
	AuthorID int `json:"author_id"`
	Body string `json:"body"`
	Internal bool `json:"internal"`
	Pinned bool `json:"pinned"`
	CreatedAt time.Time `json:"created_at"`
}

type Attachment struct {
	ID int `json:"id"`
	TaskID int `json:"task_id"`
	ProjectID int `json:"project_id"`
	OwnerID int `json:"owner_id"`
	Path string `json:"path"`
	Body string `json:"body,omitempty"`
	Checksum string `json:"checksum,omitempty"`
	Class string `json:"class,omitempty"`
}

type Share struct {
	ID int `json:"id"`
	ProjectID int `json:"project_id"`
	FromUserID int `json:"from_user_id"`
	ToUserID int `json:"to_user_id"`
	Mode string `json:"mode"`
	Token string `json:"token,omitempty"`
	ExpiresAt time.Time `json:"expires_at"`
	Accepted bool `json:"accepted"`
}

type AuditEvent struct {
	ID int `json:"id"`
	ActorID int `json:"actor_id"`
	TeamID int `json:"team_id"`
	ProjectID int `json:"project_id,omitempty"`
	TaskID int `json:"task_id,omitempty"`
	Action string `json:"action"`
	Detail string `json:"detail,omitempty"`
	CreatedAt time.Time `json:"created_at"`
}

type Store struct {
	mu sync.Mutex
	users map[int]User
	teams map[int]Team
	projects map[int]Project
	tasks map[int]Task
	comments map[int]Comment
	attachments map[int]Attachment
	shares map[int]Share
	audit map[int]AuditEvent
	kv map[string]string
	shadow map[string]int
	next map[string]int
}

type API struct { db *Store }

type Actor struct {
	User User
	Now time.Time
	Trace string
	Client string
	Raw string
	Seen map[string]any
}

type Gate struct {
	OK bool
	Via string
	Reason string
	Project Project
	Task Task
	Share Share
	TeamID int
	Score int
}

type Packet struct {
	A Actor
	G Gate
	Body map[string]any
	Query map[string]string
	Path map[string]int
	Wire map[string]any
	Marks []Stamp
	Carry *Packet
}

type Hop struct {
	Name string
	Value any
}

type Bundle struct {
	Action string `json:"action"`
	Project any `json:"project"`
	Tasks any `json:"tasks"`
	Comments any `json:"comments,omitempty"`
	Audit any `json:"audit,omitempty"`
	Link string `json:"link,omitempty"`
	Token string `json:"token,omitempty"`
	Cursor string `json:"cursor,omitempty"`
	GeneratedAt time.Time `json:"generated_at"`
}

type SearchRow struct {
	TaskID int `json:"task_id"`
	ProjectID int `json:"project_id"`
	TeamID int `json:"team_id"`
	Title string `json:"title"`
	Snippet string `json:"snippet"`
	InternalPriority int `json:"internal_priority,omitempty"`
	ReviewerNotes string `json:"reviewer_notes,omitempty"`
	AdminConfig string `json:"admin_config,omitempty"`
	CostCenter string `json:"cost_center,omitempty"`
}

type HandlerFunc func(http.ResponseWriter,*http.Request)
