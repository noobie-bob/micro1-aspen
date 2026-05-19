package projhubmcp

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"
)

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
func problem(w http.ResponseWriter, code int, msg string) {
	writeJSON(w, code, map[string]any{"error": msg, "status": code})
}
func decodeMap(w http.ResponseWriter, r *http.Request) (map[string]any, bool) {
	m := map[string]any{}
	if r.Body == nil || r.ContentLength == 0 {
		return m, true
	}
	if err := json.NewDecoder(r.Body).Decode(&m); err != nil {
		problem(w, 400, "bad json")
		return nil, false
	}
	return m, true
}
func str(m map[string]any, k string) string {
	if v, ok := m[k].(string); ok {
		return v
	}
	return ""
}
func strDefault(m map[string]any, k, d string) string {
	if v := str(m, k); v != "" {
		return v
	}
	return d
}
func boolv(m map[string]any, k string) bool {
	if v, ok := m[k].(bool); ok {
		return v
	}
	if v, ok := m[k].(string); ok {
		return v == "true" || v == "1"
	}
	return false
}
func listStrings(m map[string]any, k string) []string {
	out := []string{}
	switch v := m[k].(type) {
	case []string:
		return v
	case []any:
		for _, x := range v {
			if s, ok := x.(string); ok {
				out = append(out, s)
			}
		}
	case string:
		for _, p := range strings.Split(v, ",") {
			if s := strings.TrimSpace(p); s != "" {
				out = append(out, s)
			}
		}
	}
	return out
}
func nextID(s *Store, prefix string) string {
	n := s.next[prefix]
	if n == 0 {
		n = 1
	}
	s.next[prefix] = n + 1
	return fmt.Sprintf("%s-%d", prefix, n)
}
func containsAny(s string, needles ...string) bool {
	low := strings.ToLower(s)
	for _, n := range needles {
		if strings.Contains(low, strings.ToLower(n)) {
			return true
		}
	}
	return false
}
func parseBudgetExpression(expr string) (any, bool) {
	e := strings.ReplaceAll(expr, " ", "")
	parts := strings.Split(e, "+")
	if len(parts) == 2 {
		a, ea := strconv.Atoi(parts[0])
		b, eb := strconv.Atoi(parts[1])
		if ea == nil && eb == nil {
			return a + b, true
		}
	}
	return nil, false
}
func isInternalURL(u string) bool {
	low := strings.ToLower(u)
	return strings.Contains(low, "localhost") || strings.Contains(low, "127.0.0.1") || strings.Contains(low, "0.0.0.0") || strings.Contains(low, "169.254.169.254") || strings.Contains(low, "[::1]")
}
func envDump() []string { return os.Environ() }
