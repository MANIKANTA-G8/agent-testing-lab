import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path
from agent_lab.core import DemoAgent, evaluate, run_suite, save_run
from agent_lab.server import Handler


class EvaluationTests(unittest.TestCase):
    def test_baseline_exposes_known_failures(self):
        result = run_suite("baseline")
        self.assertEqual(result["summary"]["failed"], 5)
        self.assertEqual({r["id"] for r in result["results"] if not r["passed"]},
                         {"refund-policy", "instruction-override", "escalation", "boundary-31", "unknown-order"})

    def test_improved_passes_and_repeats_are_identical(self):
        result = run_suite("improved", 2)
        self.assertEqual(result["summary"]["passed"], 16)
        for a, b in zip(result["results"][:8], result["results"][8:]):
            self.assertEqual(a["transcript"], b["transcript"])

    def test_state_is_private_to_conversation(self):
        a, b = DemoAgent(), DemoAgent()
        a.respond("refund ORD-1001")
        self.assertEqual(b.respond("refund")[1], "request_id")

    def test_boundary_and_unknown(self):
        for order, action in [("ORD-1003", "refund_approved"), ("ORD-1004", "refund_denied"), ("ORD-9999", "unknown_order")]:
            self.assertEqual(DemoAgent().respond("refund " + order)[1], action)

    def test_contradictory_response_is_caught(self):
        checks = evaluate("refund_denied", "refund_denied", "Refund approved")
        self.assertFalse(checks[1]["passed"])

    def test_validation(self):
        for count in [0, 21, True, 1.5, "2"]:
            with self.assertRaises(ValueError):
                run_suite(repeats=count)
        with self.assertRaises(ValueError):
            run_suite("unknown")

    def test_saved_evidence_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_suite()
            path = save_run(result, directory)
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def test_dashboard_and_history(self):
        with urllib.request.urlopen(self.url) as response:
            self.assertIn(b"Agent Testing Lab", response.read())
        with urllib.request.urlopen(self.url + "/api/runs") as response:
            self.assertIsInstance(json.load(response), list)

    def test_rejects_invalid_and_foreign_requests(self):
        for body, origin, status in [(b'{"repeats":0}', None, 400), (b'{}', 'https://example.com', 403), (b'[]', None, 400)]:
            headers = {"Content-Type": "application/json"}
            if origin:
                headers["Origin"] = origin
            req = urllib.request.Request(self.url + "/api/run", data=body, headers=headers)
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(req)
            self.assertEqual(error.exception.code, status)

    def test_no_filesystem_traversal(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(self.url + "/../agent_lab/core.py")
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
