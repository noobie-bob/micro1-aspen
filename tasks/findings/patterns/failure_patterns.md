# Failure Patterns

## Persistent failure causes

- too many steps in one rubric,
- exact literal requirements where equivalent values are acceptable,
- requiring one continuous flow when models split checks across tests,
- requiring captured-ID continuity across long chains,
- checking multiple surfaces and multiple callers in one item,
- Type C items left in the rubric,
- broad anti-overblock criteria that are not tied to one concrete product path,
- crypto/token non-derivability expectations without very clear artifacts.

## Common model misses

- tested seeded object instead of newly created object,
- used a nearby query or benign value,
- checked only error and not content absence,
- inspected typed result but did not serialize it,
- omitted positive control,
- skipped the cross-caller half of a comparison,
- covered related endpoint/tool but not the same captured ID or marker,
- asserted status only instead of body/sentinel evidence.

## MCP over-chaining failures

Models repeatedly failed long flows:

```text
create task → update → add comment → list
create team → create project → retrieve
delete → search absent → update not found
cross-user setup → same query → dual assertions
```

They often wrote nearby tests but missed one link, such as carrying the captured ID forward or checking serialized content absence.

## Fixes

- shorten the item,
- allow input classes,
- ask for serialized response,
- remove persistent hard items,
- remove inverted items,
- keep stable discriminators unchanged,
- archive old examples instead of keeping stale rubric-ID-specific instructions in active findings.
