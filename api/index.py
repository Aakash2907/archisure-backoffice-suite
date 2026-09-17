import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import app as original_app


class StripAPIPrefix:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")

            if path == "/api":
                scope["path"] = "/"
            elif path.startswith("/api/"):
                scope["path"] = path[4:]

        await self.app(scope, receive, send)


app = StripAPIPrefix(original_app)