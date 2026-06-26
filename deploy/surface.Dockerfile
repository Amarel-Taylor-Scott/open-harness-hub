# One image serves ANY of the 5 AI Done Right surfaces — pick via the SURFACE env (cloud) or a positional arg (local).
# The server is stdlib-only (no pip install); cloud platforms inject PORT, SURFACE selects which surface to render.
#
#   docker build -f deploy/surface.Dockerfile -t aidr-surface .
#   docker run -e SURFACE=baltor -e PORT=8080 -p 8080:8080 aidr-surface
#   # surfaces: ai-done-right · teleon · baltor · aidevobserver · open-star-hubs
FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV PYTHONPATH=/app \
    SURFACE=ai-done-right \
    HOST=0.0.0.0 \
    PORT=8080
EXPOSE 8080
# surface_server reads SURFACE + PORT + HOST from the env (see scripts/surface_server.py main()).
CMD ["python3", "scripts/surface_server.py"]
