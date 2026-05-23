FROM python:3.14-slim
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git curl iputils-ping \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /mcp_vault
COPY mcp_vault/ /mcp_vault/
RUN python -m pip install -r requirements.txt
RUN git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "starter (mcp_server v1)"
RUN chown -R user:user /mcp_vault
USER user
CMD ["bash"]
