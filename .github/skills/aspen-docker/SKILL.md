---
name: aspen-docker
description: "Docker setup for Aspen tasks: production vs local Dockerfile templates (Python/Go/Node/Bun), E2B uid-1000 convention, buildx linux/amd64 commands, image naming (micro1ai/aspen-{substrate}:{descriptor}-v{N}), push/digest capture, .dockerignore, known gotchas (tag poisoning, sticky cache). Load when writing Dockerfiles, building images, or pushing to micro1ai registry."
user-invocable: false
---

# Realm Aspen: Docker Setup

## Overview

Every Aspen task ships as an isolated, containerized image. Docker is required for:

1. **Reproducibility:** The image must produce identical states across every run.
2. **Anti-cheating:** No `.git` history beyond a single commit, no remote.
3. **E2B compatibility:** uid 1000 named `user`, no OCI attestation manifests, `linux/amd64`.

## Two Dockerfiles Per Task

| Dockerfile | Location | What it copies | Purpose |
|---|---|---|---|
| Local testing | `taskNN/Dockerfile` | Substrate + ALL tests | Run gold-standard tests locally |
| Production | `taskNN/aspen__*/Dockerfile` | Substrate + `conftest.py` ONLY | Pushed to Docker Hub — agent's environment |

**The production image must contain NO pre-written tests.**

## Production Dockerfile Template (Python)

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

## Go Template

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

RUN rm -rf .git && git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "starter ({descriptor} v{N})"

RUN chown -R user:user /repo
USER user

CMD ["bash"]
```

## Node.js / Express Template

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
    && git commit -q -m "starter ({descriptor} v{N})"

RUN chown -R user:user /repo
USER user

CMD ["bash"]
```

## .dockerignore

```dockerignore
# Exclude gold-answer test files from Docker context
tests/exfiltration/

**/__pycache__/
**/*.pyc
**/.pytest_cache/

aspen__*_*/
*.md
reasoning.txt
```

## Building and Pushing

> **WARNING:** Apple Silicon produces arm64. Always use `docker buildx --platform linux/amd64`.

### Build production image:

```bash
cd micro1-aspen/tasks/taskNN/

docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -f aspen__{substrate}_{descriptor}_{NNN}/Dockerfile \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .
```

`--provenance=false --sbom=false` prevents OCI attestation manifests that E2B cannot parse.

### Capture the digest:

```bash
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --format '{{.Manifest.Digest}}'
```

### Get the base_commit from inside the container:

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  git rev-parse HEAD
```

### Verify image contents:

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  find /repo -type f -not -path '/repo/.git/*' | sort
```

Expected: ONLY substrate files, `tests/conftest.py`, `pytest.ini`, `requirements.txt`. No `test_smoke.py`, no `exfiltration/`.

## Image Naming Convention

`micro1ai/aspen-{substrate}:{descriptor}-v{N}`

- Increment `v{N}` on every push, even corrections — E2B's cache is sticky.
- Set to **PRIVATE** on Docker Hub after first push.

## Known Gotchas

- **E2B's image cache is sticky:** A poisoned tag (wrong arch, broken deps) is permanent. Increment version suffix.
- **Realm does not pick up task_config.json changes** after initial upload — create a new task.
- **No test_smoke.py in production:** Do not reference it in `prompt.txt`. Reference `conftest.py` instead.
- **No placeholder strings in config:** Replace `"LEAVE_BLANK"` with empty strings.
- **No pipeline-name leftovers:** No `shield`, `sequoia`, or `hornbeam` in git config or commit messages.

## First-Push Checklist

- [ ] Building from PRODUCTION Dockerfile (`aspen__*/Dockerfile`)
- [ ] `--platform linux/amd64` flag set
- [ ] `--provenance=false --sbom=false` flags set
- [ ] E2B uid-1000-user convention followed
- [ ] Fresh git init, single commit, no remote
- [ ] Image contains ONLY substrate + conftest.py + pytest.ini
- [ ] No `test_smoke.py`, no `exfiltration/`, no `__pycache__/`
- [ ] `task_config.json` has no placeholders; `image_name`, `image_digest`, `base_commit` all match
- [ ] Image set to PRIVATE on Docker Hub
