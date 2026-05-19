FROM golang:1.22-bookworm
ENV DEBIAN_FRONTEND=noninteractive
RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user && apt-get update && apt-get install -y --no-install-recommends git ca-certificates curl && rm -rf /var/lib/apt/lists/*
WORKDIR /repo
COPY go.mod /repo/go.mod
COPY projecthub/ /repo/projecthub/
COPY tests/ /repo/tests/
RUN git init -q && git config user.email build@aspen.local && git config user.name build && git add -A && git commit -q -m "buggy starter (projecthub visibility v3 weird-passing)"
RUN chown -R user:user /repo
USER user
CMD ["bash"]
