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

    def test_binds_localhost_only(self):
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")

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


if __name__ == "__main__":
    unittest.main()
