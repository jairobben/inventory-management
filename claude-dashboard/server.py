"""Servidor del dashboard de sesiones de Claude Code.

Uso:
    uv run python server.py            # o: python3 server.py
    # con datos de demo:
    python3 demo_data.py /tmp/claude-demo
    CLAUDE_DASHBOARD_DIR=/tmp/claude-demo python3 server.py

Abre http://localhost:8020
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from analyzer import analyze

HERE = Path(__file__).parent
app = FastAPI(title="Claude Sessions Dashboard")


@app.get("/api/stats")
def stats() -> dict:
    return analyze()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(HERE / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8020)
