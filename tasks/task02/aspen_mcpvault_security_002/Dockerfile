FROM python:3.14-slim
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /repo

COPY mcp_vault/requirements.txt /repo/requirements.txt
RUN pip install -r /repo/requirements.txt

COPY mcp_vault/ /repo/
COPY tests/test_smoke.py /repo/tests/test_smoke.py
COPY tests/conftest.py /repo/tests/conftest.py
COPY pytest.ini /repo/pytest.ini

# ensure git is available for the image commit step
RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*

RUN git init -q \
    && git config user.email build@aspen.local \
    && git config user.name build \
    && git add -A \
    && git commit -q -m "starter (mcp_vault v1)"

RUN echo "user:x:1000:1000:user:/home/user:/bin/sh" >> /etc/passwd \
    && echo "user:x:1000:" >> /etc/group \
    && mkdir -p /home/user \
    && chown -R user:user /repo

USER user
ENV PYTHONPATH=/repo

CMD ["bash"]
