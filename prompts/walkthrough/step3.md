# Step 3: Build the Docker Image, Write the Prompt & Rubric

> **Goal:** Containerize the service with anti-cheating measures, write the agent-facing prompt, construct the rubric with ~15 items, and create all configuration files.

---

## 3.1 Write the Dockerfile

The Dockerfile must follow the E2B convention: uid 1000 named user, `WORKDIR /repo`, fresh git init with a single commit.

### Python Template (proven in task01)

```dockerfile
FROM python:3.14-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# E2B convention: uid 1000 named "user"
RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

COPY requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt

# Copy the buggy substrate, smoke test, and pytest config
COPY {substrate}/ /repo/{substrate}/
COPY tests/ /repo/tests/
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote
RUN git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "buggy starter ({descriptor} v1)"

RUN chown -R user:user /repo
USER user

ENV PYTHONPATH=/repo

CMD ["bash"]
```

### Go Template

```dockerfile
FROM golang:1.23-bookworm

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o /repo/server ./cmd/server

# Anti-cheating: fresh git init
RUN rm -rf .git && git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "buggy starter ({descriptor} v1)"

RUN chown -R user:user /repo
USER user

CMD ["bash"]
```

### Node.js / Express Template

```dockerfile
FROM node:22-slim

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

COPY package*.json ./
RUN npm ci --ignore-scripts

COPY . .

RUN rm -rf .git && git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "buggy starter ({descriptor} v1)"

RUN chown -R user:user /repo
USER user

CMD ["bash"]
```

### Bun Template

```dockerfile
FROM oven/bun:1.2-slim

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user

WORKDIR /repo

COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile

COPY . .

RUN rm -rf .git && git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "buggy starter ({descriptor} v1)"

RUN chown -R user:user /repo
USER user

CMD ["bash"]
```

---

## 3.2 Build & Validate the Image Locally

### Build Command

**CRITICAL:** Always use `--platform linux/amd64` even if you're on ARM/Apple Silicon:

```bash
cd micro1-aspen/tasks/task02/

# Build locally for testing (not pushing yet)
docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v1 \
  --load .
```

> **Note:** `--load` loads the image locally instead of pushing. Use this for testing.

### Validate Inside the Container

```bash
# Run the container interactively
docker run --rm -it micro1ai/aspen-{substrate}:{descriptor}-v1

# Inside the container, verify:
# 1. Smoke tests pass
user@container:/repo$ pytest tests/test_smoke.py -v
# All tests should PASS

# 2. Verify git history is clean (single commit, no remote)
user@container:/repo$ git log --oneline
# Should show exactly ONE commit:
# abc1234 buggy starter ({descriptor} v1)

user@container:/repo$ git remote -v
# Should be empty (no remotes)

# 3. Verify the service is observable
user@container:/repo$ python -c "from {substrate}.app import create_app; print('OK')"
# Should print 'OK'

# 4. Verify no answer files leaked into image
user@container:/repo$ ls tests/exfiltration/ 2>/dev/null
# Should be empty or not exist

# 5. Verify no task config leaked
user@container:/repo$ ls aspen__* 2>/dev/null
# Should not exist
```

---

## 3.3 Write prompt.txt

The prompt is a **3-paragraph engineer-to-engineer message** presented to the agent. It frames the task as a peer asking the agent to write a test suite.

### Template

```
A teammate/participant reported [brief description of the issue, written
conversationally]. They noticed [what they observed — enough context to
direct investigation without revealing rubric items]. They kept looking
and found [additional suspicious behaviors — breadcrumbs, not answers].

We don't have any tests covering [general area]. Your job is to write
the test suite that catches all of it.

**Write tests only. Do not modify any file under `{substrate}/`.** A
separate engineer will use your tests to validate their fix; for them
to trust your tests, the suite must (1) catch the [primary issues] the
[reporter] is exploiting, (2) catch [secondary issues], and (3) catch
a fix that over-blocks legitimate [same-team/normal] flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows
the legitimate participant + admin flows already in use — your suite
should pin those down with anti-overblock assertions so they cannot
regress.

Submit only your test files as a unified diff via `submit_answer`
(applies clean from `/repo`).
```

### Example from task01

```
A teammate on the platform pinged me — they noticed they can see project
tasks, comments, and internal details from other teams they're not members
of. They said they were browsing the API with their regular participant
key and stumbled into projects and tasks that belong to a completely
different team. They kept poking around and found internal reviewer notes,
admin-only budget data, and even the audit log. Then they tried the search
endpoint and noticed something weird with the SQL, and found some debug
endpoints that probably shouldn't be there. They also mentioned that when
they hit a bad URL or triggered an error, the response came back with way
too much detail — version numbers, code paths, the works.

We don't have any tests covering cross-team isolation, admin-field
redaction, injection surfaces, or the debug endpoints. Your job is to
write the test suite that catches all of it.

**Write tests only. Do not modify any file under `projhub/`.** ...
```

### Rules for prompt.txt

| Rule | Why |
|------|-----|
| Do NOT list rubric items | Agent must induce what to test from code |
| Do NOT list structural axes | Eliminates the scenario-induction signal |
| DO mention the reported behavior conversationally | Gives direction without giving answers |
| DO specify where to put tests | Agent needs to know `tests/exfiltration/` |
| DO reference `test_smoke.py` | Agent needs the legitimate-flow reference |
| DO forbid modifying the service source | Agent sometimes writes fixes instead of tests |
| DO specify submission format | `submit_answer` as unified diff |

---

## 3.4 Construct the Rubric (task_config.json)

### Rubric Design (~15 items)

Decompose your scenario into **atomic, binary** rubric items along structural axes:

| Structural Axis | Item Count | Purpose |
|-----------------|-----------|---------|
| Direct coverage (primary) | 6-8 items | Exercise the target scenario at its primary surfaces |
| Direct coverage (secondary) | 2-3 items | Cover secondary/adjacent surfaces |
| Anti-overblock / regression guards | 2-3 items | Legitimate flows must still work |
| Test quality | 1-2 items | Beyond-surface assertions (sentinel markers, side effects) |

### Severity Distribution

| Severity | Weight | Target Count | Purpose |
|----------|--------|-------------|---------|
| critical | 4 | 0-1 | Reserved: missing = zero discrimination. Most tasks have 0. |
| major | 3 | 10-13 | Standard weight for primary + anti-regression |
| minor | 2 | 1-3 | Secondary coverage, peripheral checks |
| nitpick | 1 | 1 | Test quality — sentinel markers, rigor |

### Rubric Arithmetic

```
rubric_max_score = Σ(severity_weight × count)

Example (task01):
  13 major (×3) + 2 minor (×2) + 1 nitpick (×1)
  = 39 + 4 + 1
  = 44
```

### Rubric Item Anatomy

Each item in `ground_truth_issues[]`:

```json
{
  "id": "RUB-001",
  "severity": "major",
  "category": "access_control",
  "description": "A test asserts that a non-admin GET /projects (list endpoint) returns only projects belonging to the caller's team, not projects from other teams."
}
```

**Description Rules:**
- Write as a precise specification: what endpoint, what role, what assertion
- Start with "A test asserts that..." or "An anti-overblock test asserts that..."
- Avoid vague phrasing like "the test should cover X"
- Specific enough for a human reviewer to audit the LLM judge's MET/UNMET call

### Complete task_config.json Template

```json
{
  "instance_id": "aspen__test_authoring_{substrate}_{descriptor}_{NNN}",
  "pipeline": "aspen",
  "task_type": "test_authoring",
  "repo": {
    "source_url": "https://github.com/{org}/{repo}/tree/main/tasks/taskNN",
    "base_commit": "FILL_AFTER_DOCKER_BUILD",
    "image_name": "micro1ai/aspen-{substrate}:{descriptor}-v1",
    "image_digest": "FILL_AFTER_DOCKER_PUSH",
    "repo_dir": "/repo",
    "language": "python"
  },
  "title": "Author tests for {brief human-readable title}",
  "track": "Realm Aspen",
  "cwe": ["CWE-284", "CWE-639"],
  "severity": "critical",
  "behavioral_prompt": "prompt.txt",
  "rubric_only": true,
  "submission": {
    "expected_diff_paths": ["tests/exfiltration/"],
    "presentation": "git_diff"
  },
  "ground_truth_issues": [
    {
      "id": "RUB-001",
      "severity": "major",
      "category": "access_control",
      "description": "A test asserts that..."
    }
    // ... 14 more items
  ],
  "rubric_max_score": 44,
  "rubric_severity_weights": {
    "critical": 4,
    "major": 3,
    "minor": 2,
    "nitpick": 1
  }
}
```

---

## 3.5 Write reasoning.txt

Concise (8-15 lines) technical justification:

```
The seeded vulnerabilities in this {service-type} span multiple {classes}:

1. {Vulnerability/scenario class 1}: brief description
2. {Vulnerability/scenario class 2}: brief description
3. ...

Test-authoring is the right shape because {reason — e.g., the threat
surface spans N endpoints across M modules}.

Severity distribution: X major + Y minor + Z nitpick = Xa + Yb + Zc
rubric_max_score = {total}
```

### Example from task01

```
The seeded vulnerabilities in this project-management API span multiple OWASP
classes, all centered on a Flask service managing teams, projects, tasks,
comments, and attachments:

1. Cross-team data isolation failure (BOLA/IDOR)
2. Missing field redaction
3. SQL injection
4. Mass assignment
5. Sensitive data exposure
6. Information exposure

Test-authoring is the right shape because the threat surface spans 25+ endpoints
across 9 route modules.

Severity distribution: 13 major + 2 minor + 1 nitpick = 13x3 + 2x2 + 1x1 = 44
rubric_max_score = 44
```

---

## 3.6 Stress-Test Your Rubric (Mental Exercise)

Before moving on, mentally run the rubric against two hypothetical agents:

### Agent A: Minimal Tester (only checks status codes = 200)
- Should **FAIL** at least: all redaction items, test quality items, and some access control items
- If this agent passes most items → rubric is too weak

### Agent B: Over-Blocker (locks down everything, including legitimate flows)
- Should **FAIL** at least: all regression guard items
- If this agent passes all items → you're missing anti-overblock guards

If either hypothetical agent passes everything, go back and add more rubric items.

---

## 3.7 Checklist

- [ ] Dockerfile follows E2B convention (uid 1000, WORKDIR /repo, fresh git init)
- [ ] Image builds successfully with `--platform linux/amd64`
- [ ] Smoke tests pass inside the container
- [ ] No answer files or task config leaked into the image
- [ ] `prompt.txt` is 3 paragraphs, conversational, no rubric enumeration
- [ ] `task_config.json` has all fields filled (except `base_commit` and `image_digest`)
- [ ] `rubric_max_score` arithmetic verified
- [ ] `reasoning.txt` is 8-15 lines with severity distribution
- [ ] Rubric has both direct-coverage AND anti-overblock items
- [ ] Rubric passes the mental stress test (Agent A and Agent B both fail at least 1 item)
