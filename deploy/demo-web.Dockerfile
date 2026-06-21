# deploy/demo-web.Dockerfile — containerized static web server for the DEMO surfaces (dist/).
# Serves the YC demo, the capability showcase, and the architecture map over real HTTP so the recorder
# (e2e/record_yc_demo.mjs) and reviewers hit an origin, not file://. stdlib-only (no deps). Build from repo root.
#
#   docker build -f deploy/demo-web.Dockerfile -t aidr-demos .
#   docker run --rm -p 8088:8088 aidr-demos
#   -> http://127.0.0.1:8088/yc-demo/index.html   ·   /teleon-demos/showcase.html   ·   /architecture/index.html
#
# This is the demo/recording surface; the product service plane (Baltor/Teleon) is generated separately by
# scripts/deploy/generate_provider_configs.py (fly/ + docker-compose.deploy.yml + the OpenTofu Cloudflare emitter).
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
COPY dist/ /srv/dist/
EXPOSE 8088
# stdlib static server; serves /srv/dist at the root (matches yc_demo_storyboard.json base_url + relative links)
CMD ["python3", "-m", "http.server", "8088", "--directory", "/srv/dist"]
