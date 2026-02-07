import asyncio
import json
from pathlib import Path

from aiohttp import web


class WebCore:
    def __init__(self, state, telemetry_hz: float, *, on_ws_msg=None):
        self.state = state
        self.telemetry_hz = telemetry_hz
        self.on_ws_msg = on_ws_msg
        self.clients = set()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        static_dir = Path(__file__).parent / "static"
        self._index_path = static_dir / "index.html"
        self.app.router.add_get("/", self.index)
        self.app.router.add_get("/ws", self.ws_handler)
        self.app.router.add_static("/static/", path=str(static_dir), name="static")

    async def index(self, request):
        return web.FileResponse(self._index_path)

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        self.clients.add(ws)
        try:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                if self.on_ws_msg is not None:
                    await self.on_ws_msg(msg.data)
        finally:
            self.clients.discard(ws)
        return ws

    async def broadcaster(self):
        period = 1.0 / self.telemetry_hz
        while True:
            payload = self.state.snapshot()
            data = json.dumps(payload, separators=(",", ":"))
            dead = []
            for ws in list(self.clients):
                try:
                    await ws.send_str(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.clients.discard(ws)
            await asyncio.sleep(period)

    async def run(self, host="0.0.0.0", port=8080):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        print(f"Web server started on {host}:{port}")
        return runner
