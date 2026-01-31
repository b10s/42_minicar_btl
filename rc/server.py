import asyncio
import json
import logging
from pathlib import Path

from aiohttp import web

from state import SharedState
from runtime_config import save_runtime, RuntimeConfig

log = logging.getLogger("web")


class WebServer:
    def __init__(self, state: SharedState, telemetry_hz: float):
        self.state = state
        self.telemetry_hz = telemetry_hz
        self.clients = set()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        static_dir = Path(__file__).parent / "static"
        self.app.router.add_get("/", self.index)
        self.app.router.add_get("/ws", self.ws_handler)
        self.app.router.add_static("/static/", path=str(static_dir), name="static")

    async def index(self, request):
        return web.FileResponse(Path(__file__).parent / "static" / "index.html")

    async def ws_handler(self, request):
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        log.info("WS connected from %s", request.remote)
        self.clients.add(ws)

        try:
            async for msg in ws:
                if msg.type != web.WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                except Exception:
                    continue

                log.info("WS msg: %s", data)
                cmd = data.get("cmd")
                if cmd == "arm":
                    val = bool(data.get("value", False))
                    with self.state.lock:
                        self.state.armed = val

                elif cmd == "pid":
                    try:
                        kp = float(data.get("kp"))
                        ki = float(data.get("ki"))
                        kd = float(data.get("kd"))
                    except Exception:
                        continue
                    with self.state.lock:
                        self.state.kp = kp
                        self.state.ki = ki
                        self.state.kd = kd

                elif cmd == "save":
                    with self.state.lock:
                        rc = RuntimeConfig(
                            armed=self.state.armed,
                            kp=self.state.kp,
                            ki=self.state.ki,
                            kd=self.state.kd,
                        )
                    try:
                        save_runtime(rc)
                    except Exception:
                        pass

        finally:
            log.info("WS disconnected %s", request.remote)
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
        return runner
