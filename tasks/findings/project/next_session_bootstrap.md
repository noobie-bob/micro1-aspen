# Next Session Bootstrap

## Start here

1. Read current type distribution.
2. Identify Type C and remove it.
3. Identify persistent Type A and remove or simplify it.
4. Preserve stable Type B.
5. Keep enough Type D for floor score.
6. Compare final count with reference ratio.

## Default MCP assumptions

- Use Go if possible.
- Keep app code small and flat.
- Prefer direct `CallTool` unit tests.
- Use serialized response assertions.
- Keep rubric descriptions short.
- Keep justifications one-line and task-focused.
- Avoid long chains unless deliberately creating a hard rung.

## When results are bad

If Opus and Qwen are both low:

```text
too many Type A items
```

If Qwen is too high:

```text
too many Type D items or B items got too easy
```

If Qwen beats Opus:

```text
Type C exists; remove it
```

If Opus misses expected floor items:

```text
description likely too chained or too exact
```
