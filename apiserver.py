"""a small local API over the brain.

the whole point of pulling the brain out into echoself_core (the Phase 0 split)
was so a frontend that isn't this pygame window - a desktop build, a phone later -
could drive the same EchoSelf. this is the first stone of that: a tiny JSON API,
stdlib only, no framework.

it binds to localhost ONLY, on purpose - a companion that knows how you feel must
never be reachable from the network. your data never leaves the machine. run with
`python main.py --serve [port]`."""

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import echoself_core

HOST         = "127.0.0.1"   # local only - never open this to the network
DEFAULT_PORT = 8765

# live conversations, kept in memory only and dropped on end - same as the window:
# nothing typed is ever written to disk, only the emotion behind it.
_SESSIONS = {}
_LOCK     = threading.Lock()


def _get_routes():
    # path -> a no-arg callable returning something json-able
    return {
        "/api/health":        lambda: {"ok": True},
        "/api/today":         lambda: echoself_core.boot(),
        "/api/echo-distance": lambda: echoself_core.echo_distance(),
        "/api/portrait":      lambda: {"facts": echoself_core.portrait_facts(20)},
        "/api/mode":          lambda: {
            "companion":    echoself_core.companion_mode(),
            "nlp":          echoself_core.nlp_active(),
            "mirror":       echoself_core.mirror_enabled(),
            "voice_speak":  echoself_core.voice_speaking(),
            "voice_listen": echoself_core.voice_listening(),
        },
    }


class Handler(BaseHTTPRequestHandler):

    def _send(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = self.path.split("?")[0]
        fn = _get_routes().get(route)
        if fn is None:
            return self._send(404, {"error": "no such endpoint"})
        try:
            self._send(200, fn())
        except Exception as e:
            self._send(500, {"error": str(e)})

    def do_POST(self):
        route  = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(400, {"error": "bad json"})
        try:
            if route == "/api/respond":
                text = (data.get("text") or "").strip()
                if not text:
                    return self._send(400, {"error": "text is required"})
                return self._send(200, echoself_core.respond(text))
            if route == "/api/emotion":
                return self._send(200, echoself_core.read_emotion(data.get("text") or ""))
            if route == "/api/session/start":
                sid  = secrets.token_hex(8)
                conv = echoself_core.conversation()
                opener = conv.open()
                with _LOCK:
                    _SESSIONS[sid] = conv
                return self._send(200, {"session_id": sid, "opener": opener})
            if route == "/api/session/say":
                with _LOCK:
                    conv = _SESSIONS.get(data.get("session_id"))
                if conv is None:
                    return self._send(404, {"error": "no such session"})
                text = (data.get("text") or "").strip()
                if not text:
                    return self._send(400, {"error": "text is required"})
                result = conv.say(text)
                echoself_core.after_turn(result)
                return self._send(200, result)
            if route == "/api/session/end":
                with _LOCK:
                    conv = _SESSIONS.pop(data.get("session_id"), None)
                if conv is not None:
                    try:
                        conv.end()
                    except Exception:
                        pass
                return self._send(200, {"ended": True})
            self._send(404, {"error": "no such endpoint"})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def log_message(self, *args):
        pass   # don't spam the console


def make_server(port=DEFAULT_PORT):
    return ThreadingHTTPServer((HOST, port), Handler)


def serve(port=DEFAULT_PORT):
    echoself_core.prepare_environment()
    srv = make_server(port)
    print(f"EchoSelf serving on http://{HOST}:{port}  (local only - ctrl-c to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
