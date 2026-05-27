













FROM micro1ai/aspen-taskhub-idor:sample-v1








ENV M1_RL_ENVS_TEMPLATE_REV=v2-public

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh \
 && chmod 755 /usr/local/bin/uv /usr/local/bin/uvx

ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN mkdir -p /opt/uv-python /opt/uv-cache \
 && uv python install --install-dir /opt/uv-python 3.13 \
 && chmod -R a+rX /opt/uv-python /opt/uv-cache





ENV UV_CACHE_DIR=/opt/uv-cache \
    UV_TOOL_DIR=/opt/uv-tools \
    UV_TOOL_BIN_DIR=/opt/uv-tools/bin \
    UV_PYTHON=3.13 \
    UV_PYTHON_PREFERENCE=only-managed
RUN id -u user >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash user \
 && mkdir -p /opt/uv-tools/bin \
 && chown -R user:user /opt/uv-cache /opt/uv-tools

USER user
WORKDIR /repo
