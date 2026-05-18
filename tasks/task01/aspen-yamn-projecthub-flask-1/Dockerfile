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

# Copy only the conftest.py — the agent writes ALL test files.
# conftest.py provides shared fixtures (client, auth headers, two_teams).
COPY projhub/ /repo/projhub/
COPY tests/conftest.py /repo/tests/conftest.py
COPY pytest.ini /repo/pytest.ini

# Anti-cheating: fresh git init, single commit, no remote
RUN git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "starter (projhub-visibility v1)"

RUN chown -R user:user /repo
USER user

ENV PYTHONPATH=/repo

CMD ["bash"]
