# Realm Aspen: Docker Setup

## Overview

Every Aspen task ships as an isolated, containerized image. Docker is required for three reasons:

1. **Reproducibility:** The agent reviews the buggy starter live; rubric matching happens at scoring time. The image must produce identical states across every run.
2. **Anti-cheating:** The agent must not be able to read the original `.git` history, search for an upstream patch, or hop branches. The image squashes history to a single commit with no remote.
3. **E2B compatibility:** Aspen runs on the E2B template-builder platform. The image must follow the E2B convention: uid 1000 named user, no OCI attestation manifests, linux/amd64 architecture.

## Environment Setup Workflow

1. Install Docker
2. Submit a request to access the `micro1ai` Docker Hub org via the expert Slack channel.
3. Author the substrate. Build the buggy service, conftest, and smoke test locally in `image_build/`.
4. Write the Dockerfile (template below).
5. Validate locally. Build the image, run the smoke test inside the container, and confirm it passes. Confirm the buggy behavior is observable to a non-admin caller.
6. Push to the private registry under a versioned tag and record the digest in `task_config.json`.

## Dockerfile Template

Template for a Python substrate (adjust the base image and dependency install for other languages).

```dockerfile
FROM python:3.12-slim

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

## Building and Pushing

WARNING: Apple Silicon produces an arm64 image, running `docker build` will silently fail in our pipeline. Use `docker buildx` to specifically target the platform E2B runs on, `linux/amd64`.

Recommended single command (works on any host architecture):

```bash
docker buildx build --platform linux/amd64 \
  --provenance=false --sbom=false \
  -t micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --push .
```

NOTE: The `--provenance=false --sbom=false` flags prevent Docker from generating OCI attestation manifests that E2B cannot parse. The `--push` flag pushes after build; you must be logged in (`docker login`) and have access to the `micro1ai` org.

After pushing, capture the digest:

```bash
docker buildx imagetools inspect \
  micro1ai/aspen-{substrate}:{descriptor}-v{N} \
  --format '{{.Manifest.Digest}}'
```

Update `task_config.json` → `repo.image_name` and `repo.image_digest` to match the pushed tag and digest exactly.

## Image Naming Convention

Format: `micro1ai/aspen-{substrate}:{descriptor}-v{N}`

- `{substrate}` — short identifier for the codebase (e.g., `taskhub`, `billing-api`).
- `{descriptor}` — short identifier for the task variant or vulnerability (e.g., `idor`, `xss`).
- `v{N}` — version suffix. Increment on every push, even if you're correcting a broken build. E2B's cache is sticky.

Set every pushed image to PRIVATE in the Docker Hub UI after the first push.

## Known Gotchas

- **E2B's image cache is sticky:** E2B never re-pulls a tag it has already seen, even if you overwrite the tag with a corrected build. If your first push has the wrong architecture or broken dependencies, that tag is permanently poisoned. You must increment the version suffix `v{N+1}` and update `task_config.json`.
- **Realm does not pick up task_config.json changes:** If you update your config after initial upload, Realm will ignore the changes. You must create a new task and re-upload (known issue with a fix pending).
- **Placeholder strings in config:** Replace placeholder values like `"LEAVE_BLANK"` with empty strings. The pipeline will choke on unexpected placeholder text.
- **conftest.py path expectations:** If your `test_smoke.py` depends on fixtures from `conftest.py`, the agent's submitted tests will too. Document the fixture surface in your prompt — agents can't infer a hidden conftest.

## First-Push Checklist

Before you push your first Docker image for a task, verify:

- You are building with `--platform linux/amd64`.
- You are using `--provenance=false --sbom=false`.
- Dockerfile uses the E2B uid-1000-user convention.
- Anti-cheating: fresh git init, single commit, no remote.
- No leftover pipeline-name strings (no `shield`, `sequoia`, `hornbeam` in git config or commit messages).
- Smoke test passes inside the container.
- `task_config.json` has no placeholder strings, `image_name` and `image_digest` match the pushed tag.
- Image is set to PRIVATE on Docker Hub.
