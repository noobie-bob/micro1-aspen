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


> **Note:** Apple Silicon (M1/M2) hosts are natively arm64. To make images runnable both on Linux (amd64) and macOS (arm64), prefer publishing a multi-arch manifest that contains both `linux/amd64` and `linux/arm64` variants. Building only `linux/amd64` is still acceptable for some workflows, but Docker Desktop will warn about a platform mismatch when running an amd64-only image on an arm64 host and may rely on emulation.

### Build production image (single-arch)

If you intentionally target only linux/amd64 (legacy requirement), use:

```bash
cd micro1-aspen/tasks/taskNN/

docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -f aspen__{substrate}_{descriptor}_{NNN}/Dockerfile \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .
```

`--provenance=false --sbom=false` prevents OCI attestation manifests that E2B cannot parse.

### Build production image (recommended: multi-arch)

To support both Apple Silicon and Linux runners, build a multi-arch image that contains amd64 and arm64 variants:

```bash
cd micro1-aspen/tasks/taskNN/

docker buildx build --platform linux/amd64,linux/arm64 \
  --provenance=false --sbom=false \
  -f aspen__{substrate}_{descriptor}_{NNN}/Dockerfile \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .
```

Notes:
- Building multi-arch requires `docker buildx` and may use emulation for cross-platform stages. It creates an index (manifest list) that lets Docker automatically pull the correct platform variant on the target host.
- If you later run into "platform mismatch" warnings on macOS, re-publish as multi-arch.

### Multi-arch verification & digest capture

After pushing, inspect the image index (manifest list) and capture the top-level digest (the index digest). Use that index digest for `image_digest` in `task_config.json` when the image is multi-arch:

```bash
docker buildx imagetools inspect micro1ai/aspen-{substrate}:{descriptor}-v{N}

# The output shows a top-level "Digest:" (index digest) and per-platform manifests.
# Use the top-level "Digest:" value (sha256:...) as `image_digest` in task_config.json
```

Example verification commands (pulls correct platform variant automatically when available):

```bash
docker image rm micro1ai/aspen-{substrate}:{descriptor}-v{N} || true
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} uname -m

# Force a specific platform if needed:
docker run --rm --platform linux/amd64 micro1ai/aspen-{substrate}:{descriptor}-v{N} uname -m
```

To extract the commit stored in the image (commit location depends on Dockerfile):

```bash
# common places to check inside the running container
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} cat /repo/.git/refs/heads/master || true
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} cat /repo/{substrate}/.git/refs/heads/master || true

# or, if git is available in the image
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} git -C /repo rev-parse HEAD || true
```

If you see "No such file or directory" for `/repo` or `.git`, inspect the container root to locate where files were copied (context path differences):

```bash
docker run --rm micro1ai/aspen-{substrate}:{descriptor}-v{N} sh -c "ls -la / && ls -la /repo || true && ls -la /{substrate} || true"
```

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

- **Chown / user creation gotcha:** `chown -R user:user /repo` will fail if `user` does not exist. Create the `user` before chown (recommended: `groupadd` + `useradd` with uid 1000) or use numeric ownership `chown -R 1000:1000 /repo`.
- **Context path gotcha:** When running `docker buildx build` the final argument is the build context. If you run the command from inside `tasks/taskNN` use `.` as context; from repo root you can pass `tasks/taskNN` as the context and adjust `-f` accordingly.

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
