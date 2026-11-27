import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

from micro_pi import cli
from micro_pi.app import SKILL_ID, Workspace
from micro_pi.config import ENV_NAMES, ModelConfig, save_config


TEST_KEY = "test-only-key"


def model_message(content):
    return {"role": "assistant", "content": content}


def word_count_request():
    return {
        **model_message(None),
        "tool_calls": [{
            "id": "count-1",
            "type": "function",
            "function": {"name": "word_count", "arguments": '{"text":"one two three four"}'},
        }],
    }


class InstalledCLITest(unittest.TestCase):
    def setUp(self):
        temp = self.enterContext(tempfile.TemporaryDirectory())
        self.root = Path(temp)
        self.home = self.root / "home"
        self.first = self.root / "first workspace"
        self.second = self.root / "second workspace"
        for directory in (self.home, self.first, self.second):
            directory.mkdir()
        self.config_file = self.home / ".micro-pi" / "config.json"
        self.responses = []
        self.requests = []
        self.env = {key: value for key, value in os.environ.items() if key not in ENV_NAMES.values()}
        self.env.update(USERPROFILE=str(self.home), HOME=str(self.home), PYTHONIOENCODING="utf-8", NO_PROXY="127.0.0.1")
        self.command = shutil.which("micro-pi", path=sysconfig.get_path("scripts"))
        self.assertIsNotNone(self.command, "Install the wheel into the test interpreter first.")

        case = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                case.requests.append((self.path, self.headers.get("Authorization"), request))
                if case.responses:
                    status, message = case.responses.pop(0)
                    payload = {"choices": [{"message": message}]} if status == 200 else {"error": TEST_KEY}
                else:
                    status, payload = 500, {"error": "unexpected model request"}
                content = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def log_message(self, *_):
                pass

        server = self.enterContext(ThreadingHTTPServer(("127.0.0.1", 0), Handler))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        self.url = f"http://127.0.0.1:{server.server_port}/v1"

    def run_console(self, args=(), *, cwd=None, text="", env=None):
        return subprocess.run(
            [self.command, *args], cwd=cwd or self.first, env=env or self.env,
            input=text, capture_output=True, encoding="utf-8", timeout=20,
        )

    def run_wizard(self, args=(), secret=TEST_KEY, chat_inputs=()):
        stdout, stderr = io.StringIO(), io.StringIO()
        previous = Path.cwd()
        try:
            os.chdir(self.first)
            with (
                patch.dict(os.environ, self.env, clear=True),
                patch.object(sys.stdin, "isatty", return_value=True),
                patch.object(stderr, "isatty", return_value=True),
                patch("builtins.input", side_effect=[self.url, "test-model", *chat_inputs]),
                patch.object(cli, "getpass", side_effect=secret if isinstance(secret, BaseException) else None,
                             return_value=secret),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                code = cli.main(list(args))
        finally:
            os.chdir(previous)
        output = stdout.getvalue() + stderr.getvalue()
        self.assertNotIn(TEST_KEY, output)
        return code, output

    def test_help_version_and_noninteractive_configuration(self):
        help_result = self.run_console(("--help",))
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("init", help_result.stdout)
        version_result = subprocess.run(
            [sys.executable, "-m", "micro_pi", "--version"], cwd=self.first,
            env=self.env, capture_output=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(version_result.returncode, 0, version_result.stderr)
        self.assertEqual(version_result.stdout.strip(), "micro-pi 1.1.0")
        missing = self.run_console()
        self.assertEqual(missing.returncode, 1)
        self.assertIn("micro-pi init", missing.stderr)
        self.assertEqual(self.requests, [])

    def test_first_run_counts_words_then_reuses_config_in_another_directory(self):
        self.responses.extend([
            (200, model_message("OK")), (200, word_count_request()), (200, model_message("Four words.")),
        ])
        code, output = self.run_wizard(chat_inputs=("Please use word_count.", "/exit"))
        self.assertEqual(code, 0, output)
        self.assertIn("Word count: 4", output)
        self.assertIn("Four words.", output)
        self.assertEqual(json.loads(self.config_file.read_text(encoding="utf-8"))["api_key"], TEST_KEY)
        first_session = self.first / ".micro-pi" / "parent.jsonl"
        first_history = first_session.read_text(encoding="utf-8")
        self.assertNotIn(TEST_KEY, first_history)
        self.assertEqual(self.requests[0][0:2], ("/v1/chat/completions", f"Bearer {TEST_KEY}"))
        self.assertNotIn("tools", self.requests[0][2])

        self.responses.append((200, model_message("Hello.")))
        second = self.run_console(cwd=self.second, text="Hello\n/exit\n")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("History: 0 messages", second.stdout)
        self.assertTrue((self.second / ".micro-pi" / "parent.jsonl").exists())
        self.assertEqual(first_session.read_text(encoding="utf-8"), first_history)
        reopened = self.run_console(text="/exit\n")
        self.assertEqual(reopened.returncode, 0, reopened.stderr)
        self.assertIn("History: 4 messages", reopened.stdout)

    def test_failed_or_cancelled_setup_preserves_saved_config(self):
        save_config(self.config_file, ModelConfig(self.url, "old-model", "old-key"))
        original = self.config_file.read_bytes()
        self.responses.append((401, None))
        code, output = self.run_wizard(("init",))
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", output)
        self.assertEqual(self.config_file.read_bytes(), original)
        code, output = self.run_wizard(("init",), secret=KeyboardInterrupt())
        self.assertEqual(code, 130)
        self.assertIn("已取消配置", output)
        self.assertEqual(self.config_file.read_bytes(), original)

    def test_pending_tool_resumes_from_another_process(self):
        state = self.first / ".micro-pi"
        state.mkdir()
        assistant = word_count_request()
        session = state / "parent.jsonl"
        history = [{"role": "user", "content": "Please count."}, assistant]
        session.write_text("".join(json.dumps(message) + "\n" for message in history), encoding="utf-8")
        (state / "run.json").write_text(json.dumps({
            "status": "WAITING_TOOL", "tool_calls": assistant["tool_calls"],
        }), encoding="utf-8")
        self.responses.append((200, model_message("Four words.")))
        env = dict(self.env, MICRO_PI_BASE_URL=self.url, MICRO_PI_MODEL="env-model", MICRO_PI_API_KEY=TEST_KEY)
        result = self.run_console(text="/exit\n", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Run resumed: WAITING_TOOL", result.stdout)
        self.assertIn("Word count: 4", result.stdout)
        self.assertEqual(self.requests[0][2]["messages"][-1]["tool_call_id"], "count-1")
        self.assertEqual(json.loads((state / "run.json").read_text(encoding="utf-8"))["status"], "SUCCEEDED")
        self.assertEqual(sum(json.loads(line)["role"] == "user" for line in session.read_text().splitlines()), 1)

    def test_installed_skill_and_workspace_boundaries(self):
        workspace = Workspace(self.root, self.config_file)
        self.assertIn("# Code Review", workspace.read_file(SKILL_ID))
        with self.assertRaises(ValueError):
            workspace.write_file(SKILL_ID, "change")
        for path in (str(self.config_file), ".micro-pi/run.json", ".env", "../outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                workspace.read_file(path)


if __name__ == "__main__":
    unittest.main()
