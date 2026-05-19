# Task Mix and Ratio Findings

## Ratio-based tuning

Do not judge a task by vulnerability coverage alone. The final rubric set needs a healthy A/B/D mix.

Use the reference ratio table to decide whether to remove or add items. A smaller clean set is better than a larger noisy set with Type C or persistent Type A.

## Practical target

For medium-size tasks, a good shape is usually:

```text
A: a few hard rungs
B: core discriminators
D: stable floor and anti-overblock items
C: zero
```

## What happened in MCP tuning

When too many hard chains existed, both models failed and Opus was too low.

When too many items were converted to one-step checks, Qwen became too high.

The correct move was to preserve stable Type B items, keep a controlled number of Type D items, remove Type C, and remove stubborn Type A items until the ratio matched the active rubric count.

## Design rule

Never add complexity blindly. First classify each item. Then decide:

```text
Type A -> keep few, remove persistent ones
Type B -> preserve
Type C -> remove
Type D -> keep enough, avoid saturation
```
