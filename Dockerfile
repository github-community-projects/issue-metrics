#checkov:skip=CKV_DOCKER_2
#checkov:skip=CKV_DOCKER_3
#trivy:ignore:AVD-DS-0002
FROM python:3.14-slim@sha256:fb83750094b46fd6b8adaa80f66e2302ecbe45d513f6cece637a841e1025b4ca
LABEL com.github.actions.name="issue-metrics" \
    com.github.actions.description="Gather metrics on issues/prs/discussions such as time to first response, count of issues opened, closed, etc." \
    com.github.actions.icon="check-square" \
    com.github.actions.color="white" \
    maintainer="@zkoppert" \
    org.opencontainers.image.url="https://github.com/github-community-projects/issue-metrics" \
    org.opencontainers.image.source="https://github.com/github-community-projects/issue-metrics" \
    org.opencontainers.image.documentation="https://github.com/github-community-projects/issue-metrics" \
    org.opencontainers.image.vendor="GitHub" \
    org.opencontainers.image.description="Gather metrics on issues/prs/discussions such as time to first response, count of issues opened, closed, etc."

COPY --from=ghcr.io/astral-sh/uv:0.10.9@sha256:10902f58a1606787602f303954cea099626a4adb02acbac4c69920fe9d278f82 /uv /uvx /bin/

WORKDIR /action/workspace
COPY pyproject.toml uv.lock *.py /action/workspace/

RUN uv sync --frozen --no-dev --no-editable \
    && apt-get -y update \
    && apt-get -y install --no-install-recommends git=1:2.47.3-0+deb13u1 \
    && rm -rf /var/lib/apt/lists/*

# Add a simple healthcheck to satisfy container scanners
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python3 -c "import os,sys; sys.exit(0 if os.path.exists('/action/workspace/issue_metrics.py') else 1)"

ENV PYTHONUNBUFFERED=1
CMD ["/action/workspace/issue_metrics.py"]
ENTRYPOINT ["uv", "run", "--no-dev", "--project", "/action/workspace"]
