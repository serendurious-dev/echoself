"""the local API over the brain - the first stone of the multi-platform build."""

import http.client
import json
import tempfile
import threading
import unittest

from core import datastore
import apiserver


class TestApiServer(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old = datastore.DATA_DIR
        datastore.DATA_DIR = self._tmp.name
        self.srv  = apiserver.make_server(0)            # port 0 = OS picks a free one
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self.thread.join(timeout=2)
        apiserver._SESSIONS.clear()
        datastore.DATA_DIR = self._old
        self._tmp.cleanup()

    def _get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        body = json.loads(r.read())
        c.close()
        return r.status, body

    def _post(self, path, payload):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("POST", path, body=json.dumps(payload),
                  headers={"Content-Type": "application/json"})
        r = c.getresponse()
        body = json.loads(r.read())
        c.close()
        return r.status, body

    def _get_raw(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read()
        ctype = r.getheader("Content-Type")
        c.close()
        return r.status, ctype, body

    def test_binds_localhost_only(self):
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")

    def test_serves_the_web_ui_at_root(self):
        status, ctype, body = self._get_raw("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn(b"EchoSelf", body)

    def test_serves_the_frontend_assets(self):
        for path, want in (("/style.css", "css"), ("/app.js", "javascript")):
            status, ctype, _ = self._get_raw(path)
            self.assertEqual(status, 200, path)
            self.assertIn(want, ctype, path)

    def test_static_cannot_climb_out_of_the_frontend_dir(self):
        # a path that tries to escape the folder must not leak files
        status, _, _ = self._get_raw("/../apiserver.py")
        self.assertEqual(status, 404)

    def test_api_still_routes_under_static(self):
        # /api/ is the api; everything else is the web ui - they don't collide
        status, body = self._get("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_serves_her_face_as_png(self):
        # the same character the window draws, rendered for the web ui
        status, ctype, body = self._get_raw("/api/face?emotion=sadness&h=200")
        self.assertEqual(status, 200)
        self.assertIn("image/png", ctype)
        self.assertEqual(body[:8], b"\x89PNG\r\n\x1a\n")

    def test_face_falls_back_on_an_unknown_emotion(self):
        status, _, body = self._get_raw("/api/face?emotion=zzzz")
        self.assertEqual(status, 200)
        self.assertEqual(body[:8], b"\x89PNG\r\n\x1a\n")

    def test_portrait_lists_and_forgets(self):
        # the portrait room: she lists what she remembers, and any line can be dropped
        from core import portrait
        portrait.remember("is writing a thesis", kind="goal", source="her")
        status, body = self._get("/api/portrait")
        self.assertEqual(status, 200)
        self.assertTrue(body["facts"])
        fid = body["facts"][0]["id"]
        status, b2 = self._post("/api/portrait/forget", {"fact_id": fid})
        self.assertEqual(status, 200)
        self.assertTrue(b2["forgotten"])
        _, b3 = self._get("/api/portrait")
        self.assertFalse(any(f["id"] == fid for f in b3["facts"]))

    def test_forget_needs_a_fact_id(self):
        status, _ = self._post("/api/portrait/forget", {})
        self.assertEqual(status, 400)

    def test_echo_distance_returns_the_four_axes(self):
        status, body = self._get("/api/echo-distance")
        self.assertEqual(status, 200)
        for axis in ("mental", "behavioral", "emotional", "learning"):
            self.assertIn(axis, body)
            self.assertIsInstance(body[axis], (int, float))
            self.assertGreaterEqual(body[axis], 0.0)
            self.assertLessEqual(body[axis], 1.0)

    def test_health(self):
        status, body = self._get("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_today_reports_onboarding_on_a_fresh_profile(self):
        status, body = self._get("/api/today")
        self.assertEqual(status, 200)
        self.assertIn("needs_onboarding", body)

    def test_respond_returns_a_reply(self):
        status, body = self._post("/api/respond", {"text": "i feel so sad and empty"})
        self.assertEqual(status, 200)
        self.assertEqual(body["emotion"], "sadness")
        self.assertIn("reply", body)
        self.assertFalse(body["crisis"])

    def test_respond_needs_text(self):
        status, _ = self._post("/api/respond", {})
        self.assertEqual(status, 400)

    def test_emotion_endpoint(self):
        status, body = self._post("/api/emotion", {"text": "i'm so anxious"})
        self.assertEqual(status, 200)
        self.assertEqual(body["primary"], "fear")

    def test_unknown_endpoint_is_404(self):
        status, _ = self._get("/api/nope")
        self.assertEqual(status, 404)

    def test_a_multi_turn_session_holds_the_thread(self):
        status, body = self._post("/api/session/start", {})
        self.assertEqual(status, 200)
        sid = body["session_id"]
        self.assertTrue(body["opener"])

        status, r1 = self._post("/api/session/say",
                                {"session_id": sid, "text": "i feel so empty and sad"})
        self.assertEqual(status, 200)
        self.assertEqual(r1["emotion"], "sadness")

        status, r2 = self._post("/api/session/say",
                                {"session_id": sid, "text": "still sad, it won't lift"})
        self.assertEqual(status, 200)
        self.assertNotEqual(r1["reply"], r2["reply"])     # holds context, doesn't repeat

        status, _ = self._post("/api/session/end", {"session_id": sid})
        self.assertEqual(status, 200)
        # ended -> the session is gone
        status, _ = self._post("/api/session/say", {"session_id": sid, "text": "hello"})
        self.assertEqual(status, 404)

    def test_say_to_an_unknown_session_is_404(self):
        status, _ = self._post("/api/session/say", {"session_id": "nope", "text": "hi"})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
