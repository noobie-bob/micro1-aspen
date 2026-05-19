# App Structure Findings

## Ideal app size

The sweet spot is a compact project that can be read in one sitting.

```text
500–900 LOC: ideal
900–1500 LOC: acceptable if organized clearly
>1500 LOC: risk of shallow tests and missed details
<300 LOC: often too easy and Qwen may pass too much
```

## Best Go MCP structure

Use a flat, boring layout:

```text
/repo
  go.mod
  types.go
  seed.go
  common.go
  tools.go
  wire.go
  prompt.txt
  task_config.json
  reasoning.txt
```

Recommended responsibilities:

```text
types.go   -> structs only
seed.go    -> seeded actors, resources, sentinels
common.go  -> helpers, JSON, parameter parsing, auth utilities
tools.go   -> tool implementations
wire.go    -> NewServer, NewHandler, CallTool, dispatch
```

## Avoid excessive architecture

Avoid deep package nesting, interface-heavy code, reflection dispatch, generated files, or unnecessary framework machinery. The task difficulty should come from domain relationships and visibility rules, not source-code archaeology.

## Direct testing surface

For Go MCP, expose:

```go
func NewServer() *API
func NewHandler() http.Handler
func (a *API) CallTool(name string, params map[string]any) (any, error)
```

`CallTool` is the critical affordance. It tells models how to write simple unit tests and avoids confusion around MCP protocol details.

## Complexity placement

Good complexity lives in domain relationships:

- admin vs user,
- alpha team vs beta team,
- public vs internal content,
- safe utility input vs unsafe utility input,
- sentinel visible vs hidden.

Bad complexity lives in engineering machinery:

- deep package nesting,
- excessive interfaces,
- reflection dispatch,
- generated handlers,
- large fixture trees.
