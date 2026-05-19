# Trimmed and Hard Rung Lessons

## Items often trimmed because both models pass

- simple cross-boundary list denial,
- simple direct ID denial,
- simple single-payload command injection,
- broad but generic diagnostic denial,
- generic exception-only quality checks.

These are floor items unless paired with a stronger content or positive-control requirement.

## Items often trimmed because both models fail

- token/share non-derivability,
- multi-address-class SSRF sweeps,
- multi-surface redaction across clone/share/export,
- admin create-project-retrieve chains,
- full lifecycle create-update-comment-list chains,
- delete plus multiple follow-up assertions,
- multi-caller privileged tool denial across many surfaces,
- stored prompt injection chains,
- cross-tool SSRF chaining.

These can be used as deliberate hard rungs, but too many will crush Opus.

## Items trimmed because of Type C risk

- generic project-boundary checks that Qwen can satisfy more often than Opus,
- direct prompt override checks where Qwen writes simpler matching tests,
- no-token admin tool checks that become easier for Qwen than Opus,
- generic sentinel absence quality checks without scenario anchoring.

Type C items should be removed quickly.
