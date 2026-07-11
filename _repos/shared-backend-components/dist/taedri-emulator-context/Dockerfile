# taedri-emulator — a containerized USER MACHINE: browsers + Claude Code CLI + optional VNC desktop.
FROM mcr.microsoft.com/playwright/python:v1.61.0-noble
RUN apt-get update && apt-get install -y --no-install-recommends \
        x11vnc novnc websockify fluxbox curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# the base image ships the BROWSERS (/ms-playwright) but not the python package — install it version-matched.
RUN pip install --no-cache-dir playwright==1.61.0
# Claude Code CLI (native installer, no node needed). If the install ever fails, the cli journey
# reports an HONEST labeled skip at runtime — the image still works for api/mcp/browser.
RUN curl -fsSL https://claude.ai/install.sh | bash \
    || echo "claude CLI install failed; the cli journey will skip honestly"
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /emulator
COPY taedri_real_use_emulator.py .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 6080
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--base", "https://taedri.fly.dev", "--journeys", "api,mcp,cli,browser"]
