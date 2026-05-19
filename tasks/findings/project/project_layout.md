# Recommended Project and Findings Layout

## Go MCP project layout

```text
/repo
  go.mod
  common.go
  types.go
  seed.go
  tools.go
  wire.go
  prompt.txt
  reasoning.txt
  task_config.json
```

## Optional documentation

```text
README.md
DEEP_DIVE.md
```

## Findings layout

```text
findings/
  README.md
  patterns/
    success_patterns.md
    failure_patterns.md
  project/
    app_structure.md
    project_layout.md
    next_session_bootstrap.md
  rubrics/
    rubric_design.md
    type_system.md
    task_mix_and_ratio.md
  archive/
    historical_cross_language_patterns.md
    trimmed_and_hard_rungs.md
```

## Avoid

```text
cmd/
internal/
pkg/
large fixture directories
many nested packages
unclear generated code
```

Keep the app and findings easy to scan. Calibration work benefits from fast comprehension.
