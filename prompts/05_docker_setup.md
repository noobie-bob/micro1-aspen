# Realm Aspen: Docker Setup

## Overview

Every Aspen task ships as an isolated, containerized image. Docker is required for three reasons:

1. **Reproducibility:** The agent reviews the buggy starter live; rubric matching happens at scoring time. The image must produce identical states across every run.
2. **Anti-cheating:** The agent must not be able to read the original `.git` history, search for an upstream patch, or hop branches. The image squashes history to a single commit with no remote.
3. **E2B compatibility:** Aspen runs on the E2B template-builder platform. The image must follow the E2B convention: uid 1000 named user, no OCI attestation manifests, linux/amd64 architecture.

## Two Dockerfiles Per Task

Each task has **two Dockerfiles** serving different purposes:

| Dockerfile | Location | What it copies | Purpose |
|---|---|---|---|
| Local testing | `taskNN/Dockerfile` | Substrate + ALL tests | Run gold-standard tests locally to validate rubric items |
| Production | `taskNN/aspen__*/Dockerfile` | Substrate + `conftest.py` ONLY | Pushed to Docker Hub — this is the agent's working environment |

**The production image must contain NO pre-written tests.** The agent writes ALL test files from scratch. Only `conftest.py` ships because it provides shared fixtures (client, auth headers, data topology) that the agent's tests will import.

## Production Dockerfile Template

Template for a Python substrate. This is the Dockerfile that gets pushed to Docker Hub.

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

# Copy only the substrate — the agent writes ALL test files.
# conftest.py provides shared fixtures (client, auth headers, data setup).
COPY {substrate}/ /repo/{substrate}/
COPY tests/conftest.py /repo/tests/conftest.py
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote
RUN git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git add -A \
 && git commit -q -m "starter ({descriptor} v{N})"

RUN chown -R user:user /repo
USER user

ENV PYTHONPATH=/repo

CMD ["bash"]
```

## Local Testing Dockerfile Template

This stays in the task root for running gold-standard tests locally:

```dockerfile
FROM python:3.14-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo

COPY requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt

# Local testing — copies substrate + all tests.
# .dockerignore excludes tests/exfiltration/ (gold-answer tests).
COPY {substrate}/ /repo/{substrate}/
COPY tests/ /repo/tests/
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote
RUN git init -q \
 && git config user.email build@aspen.local \
 && git config user.name build \
 && git add -A \
 && git commit -q -m "starter ({descriptor} v{N})"

RUN chown -R user:user /repo
USER user

ENV PYTHONPATH=/repo

CMD ["bash"]
```

## .dockerignore

Both Dockerfiles share the same `.dockerignore` in the task root:

```dockerignore
# Exclude gold-answer test files from Docker context
tests/exfiltration/

# Python artifacts
**/__pycache__/
**/*.pyc
**/.pytest_cache/

# Exclude task config and supporting docs from container
aspen__*_*/
*.md
reasoning.txt
```

## Building and Pushing

WARNING: Apple Silicon produces an arm64 image, running `docker build` will silently fail in our pipeline. Use `docker buildx` to specifically target the platform E2B runs on, `linux/amd64`.

### Build the production image (from the aspen__ Dockerfile):

```bash
cd micro1-aspen/tasks/taskNN/

docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -f aspen__{substrate}_{descriptor}_{NNN}/Dockerfile \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .
```

NOTE: The `--provenance=false --sbom=false` flags prevent Docker from generating OCI attestation manifests that E2B cannot parse. The `--push` flag pushes after build; you must be logged in (`docker login`) and have access to the `micro1ai` org.

### Get the git commit from inside the container:

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  git rev-parse HEAD
```

### Verify the image contents:

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  find /repo -type f -not -path '/repo/.git/*' | sort
```

Expected output should show ONLY: `{substrate}/` source files, `tests/conftest.py`, `pytest.ini`, `requirements.txt`. No `test_smoke.py`, no `exfiltration/`, no `__pycache__/`.

### After pushing, capture the digest:

```bash
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --format '{{.Manifest.Digest}}'
```

Update `task_config.json` → `repo.image_name`, `repo.image_digest`, and `repo.base_commit` to match the pushed tag, digest, and git commit exactly.

## Image Naming Convention

Format: `micro1ai/aspen-{substrate}:{descriptor}-v{N}`

- `{substrate}` — short identifier for the codebase (e.g., `projhub`, `billing-api`).
- `{descriptor}` — short identifier for the task variant or vulnerability (e.g., `visibility`, `idor`).
- `v{N}` — version suffix. Increment on every push, even if you're correcting a broken build. E2B's cache is sticky.

Set every pushed image to PRIVATE in the Docker Hub UI after the first push.

## Known Gotchas

- **E2B's image cache is sticky:** E2B never re-pulls a tag it has already seen, even if you overwrite the tag with a corrected build. If your first push has the wrong architecture or broken dependencies, that tag is permanently poisoned. You must increment the version suffix `v{N+1}` and update `task_config.json`.
- **Realm does not pick up task_config.json changes:** If you update your config after initial upload, Realm will ignore the changes. You must create a new task and re-upload (known issue with a fix pending).
- **Placeholder strings in config:** Replace placeholder values like `"LEAVE_BLANK"` with empty strings. The pipeline will choke on unexpected placeholder text.
- **conftest.py path expectations:** The agent's submitted tests will import fixtures from `conftest.py`. Document the fixture surface in your prompt or DEEP_DIVE — agents can't infer a hidden conftest.
- **No test_smoke.py in production:** The production image does NOT contain `test_smoke.py`. The prompt must NOT reference it. Reference `conftest.py` for available fixtures instead.

## First-Push Checklist

Before you push your first Docker image for a task, verify:

- You are building from the PRODUCTION Dockerfile (`aspen__*/Dockerfile`), not the root one.
- You are building with `--platform linux/amd64`.
- You are using `--provenance=false --sbom=false`.
- Dockerfile uses the E2B uid-1000-user convention.
- Anti-cheating: fresh git init, single commit, no remote.
- No leftover pipeline-name strings (no `shield`, `sequoia`, `hornbeam` in git config or commit messages).
- Image contains ONLY substrate + conftest.py + pytest.ini (verified with `find`).
- No `test_smoke.py`, no `exfiltration/`, no `__pycache__/` in the image.
- `task_config.json` has no placeholder strings, `image_name`, `image_digest`, and `base_commit` match the pushed tag.
- Image is set to PRIVATE on Docker Hub.
