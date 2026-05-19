# Type System Findings

## Type definitions

```text
Type A = both models fail
Type B = Opus passes, Qwen fails
Type C = Qwen passes as much or more than Opus
Type D = both models pass
```

## Type A

Type A is useful only in small amounts. A few hard rungs prevent saturation. Too many Type A items crush Opus.

Rule:

```text
If an item remains Type A after two revisions, remove it or convert it to a simple Type D item.
```

## Type B

Type B is the core signal. Preserve Type B items once found. Do not simplify them unless Opus starts failing consistently.

Strong Type B patterns:

- response shaping with admin control,
- public/internal comment visibility,
- unsafe input plus benign control,
- internal fetch non-leak plus public control,
- serialized content assertions with sentinels.

## Type C

Type C is inverted signal. It rewards the weaker model and damages spread.

Rule:

```text
Remove Type C immediately unless the item is absolutely central.
```

## Type D

Type D stabilizes the denominator and protects product behavior. Use enough D items for floor score, but not so many that Qwen saturates.
