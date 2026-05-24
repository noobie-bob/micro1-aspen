FROM python:3.14-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd -r user && useradd -r -g user -u 1000 -m -d /home/user user \
    && apt-get update \
    && apt-get install -y --no-install-recommends git curl iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /repo
COPY mcp_hub/requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt
COPY mcp_hub/ /repo/
COPY tests/test_smoke.py /repo/tests/test_smoke.py
COPY tests/conftest.py /repo/tests/conftest.py
COPY pytest.ini /repo/pytest.ini

RUN git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "starter (mcp_server v1)"

RUN chown -R user:user /repo

USER user
ENV PYTHONPATH=/repo

CMD ["bash"]