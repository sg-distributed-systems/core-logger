"""Routing regression tests; run with stdlib unittest discovery."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from core_logger import (
    FileHandler, HttpHandler, StdoutHandler, Tier, clear_correlation_id, get_logger,
)
from core_logger.config import (
    LoggerConfig, get_logger_config, load_logger_config, reload_logger_config,
)
from core_logger.formatter import format_log
from core_logger.handlers import SafeHandler, build_handlers, default_handlers
from core_logger.tiers import resolve_tier


class RecordingHandler:
    def __init__(self):
        self.entries = []

    def emit(self, entry):
        self.entries.append(entry.copy())


class FailingHandler:
    def emit(self, entry):
        raise RuntimeError("destination unavailable")


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        reload_logger_config()
        clear_correlation_id()

    def tearDown(self):
        self.env.stop()
        reload_logger_config()
        clear_correlation_id()

    def test_tier_resolution_precedence(self):
        self.assertEqual(resolve_tier(), Tier.INFRASTRUCTURE)
        os.environ["LOG_SERVICE_TIER"] = "BuSiNeSs"
        self.assertEqual(resolve_tier(), Tier.BUSINESS)
        self.assertEqual(resolve_tier("CoMpLiAnCe"), Tier.COMPLIANCE)
        self.assertEqual(resolve_tier(Tier.INFRASTRUCTURE), Tier.INFRASTRUCTURE)
        os.environ["LOG_SERVICE_TIER"] = "invalid"
        self.assertEqual(resolve_tier(), Tier.INFRASTRUCTURE)
        for value in ("invalid", "", 42):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_tier(value)

    def test_logger_exposes_resolved_tier(self):
        os.environ["LOG_SERVICE_TIER"] = "BUSINESS"
        self.assertEqual(get_logger("x", log_handlers=[]).tier, Tier.BUSINESS)
        self.assertEqual(get_logger("x", tier="compliance", log_handlers=[]).tier,
                         Tier.COMPLIANCE)

    def test_custom_handlers_fan_out_and_replace_defaults(self):
        first, second = RecordingHandler(), RecordingHandler()
        output = io.StringIO()
        with redirect_stdout(output):
            get_logger("x", log_handlers=[first, second]).info("hello", value=3)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(first.entries, second.entries)
        self.assertEqual(first.entries[0]["value"], 3)
        self.assertEqual(first.entries[0]["tier"], "infrastructure")
        with patch("core_logger.logger.format_log", wraps=format_log) as formatter:
            get_logger("x", log_handlers=[first, second]).info("once")
            self.assertEqual(formatter.call_count, 1)

    def test_empty_custom_handlers_disable_output(self):
        output = io.StringIO()
        with redirect_stdout(output):
            get_logger("x", log_handlers=[]).info("not emitted")
        self.assertEqual(output.getvalue(), "")

    def test_failure_falls_back_and_does_not_block_other_handlers(self):
        good = RecordingHandler()
        output = io.StringIO()
        with redirect_stdout(output):
            get_logger("x", log_handlers=[FailingHandler(), good]).info("hello")
        fallback = json.loads(output.getvalue())
        self.assertEqual(fallback["log_handler_error"],
                         "FailingHandler: destination unavailable")
        self.assertEqual(fallback["message"], "hello")
        self.assertEqual(len(good.entries), 1)
        self.assertNotIn("log_handler_error", good.entries[0])

    def test_safe_handler_does_not_raise_if_fallback_fails(self):
        with patch("builtins.print", side_effect=OSError("stdout closed")):
            SafeHandler(FailingHandler()).emit({"message": "hello"})

    def test_default_stdout_is_backward_compatible(self):
        output = io.StringIO()
        with patch("core_logger.formatter.datetime") as clock:
            clock.now.return_value.isoformat.return_value = "fixed-timestamp"
            with redirect_stdout(output):
                get_logger("x").info("hello", answer=42)
        self.assertEqual(output.getvalue(), json.dumps({
            "level": "INFO", "service": "x", "message": "hello", "answer": 42,
            "timestamp": "fixed-timestamp", "tier": "infrastructure",
        }) + "\n")

    def test_pretty_stdout_unchanged(self):
        os.environ.update(LOG_PRETTY="true", LOG_INCLUDE_TIMESTAMP="false")
        output = io.StringIO()
        with redirect_stdout(output):
            get_logger("x").info("hello")
        entry = {"level": "INFO", "service": "x", "message": "hello",
                 "tier": "infrastructure"}
        self.assertEqual(output.getvalue(), json.dumps(entry, indent=2, sort_keys=True) + "\n")

    def test_level_filtering(self):
        recorder = RecordingHandler()
        logger = get_logger("x", log_handlers=[recorder])
        logger.debug("filtered")
        logger.info("included")
        self.assertEqual([e["message"] for e in recorder.entries], ["included"])

    def test_compliance_redacts_before_all_destinations_and_fallback(self):
        recorder = RecordingHandler()
        output = io.StringIO()
        with redirect_stdout(output):
            get_logger("x", Tier.COMPLIANCE,
                       [FailingHandler(), recorder]).info(
                           "audit", password="sensitive", TOKEN="private", user="alice")
        for entry in (recorder.entries[0], json.loads(output.getvalue())):
            self.assertEqual(entry["password"], "***redacted***")
            self.assertEqual(entry["TOKEN"], "***redacted***")
            self.assertEqual(entry["user"], "alice")
            self.assertEqual(entry["tier"], "compliance")

    def test_other_tiers_do_not_redact(self):
        for tier in (Tier.BUSINESS, Tier.INFRASTRUCTURE):
            recorder = RecordingHandler()
            get_logger("x", tier, [recorder]).info("hello", password="unchanged")
            self.assertEqual(recorder.entries[0]["password"], "unchanged")

    def test_handler_spec_parsing(self):
        errors = io.StringIO()
        with redirect_stderr(errors):
            handlers = build_handlers(
                " stdout, file:/tmp/audit.log, http:https://example.test/logs, "
                "http://example.test/logs, https://example.test/logs, unknown, ,", True)
        self.assertEqual([type(h) for h in handlers],
                         [StdoutHandler, FileHandler, HttpHandler, HttpHandler, HttpHandler])
        self.assertTrue(handlers[0].pretty)
        self.assertEqual(handlers[1].path, Path("/tmp/audit.log"))
        self.assertEqual(handlers[2].url, "https://example.test/logs")
        self.assertEqual(handlers[3].url, "http://example.test/logs")
        self.assertIn("unknown", errors.getvalue())

    def test_per_tier_environment_overrides(self):
        for tier in Tier:
            with self.subTest(tier=tier), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "nested" / "log.jsonl"
                os.environ[f"LOG_HANDLERS_{tier.name}"] = f"stdout,file:{path}"
                reload_logger_config()
                output = io.StringIO()
                with redirect_stdout(output):
                    get_logger("x", tier).info("routed")
                self.assertEqual(json.loads(output.getvalue()),
                                 json.loads(path.read_text(encoding="utf-8")))
                handlers = default_handlers(tier, get_logger_config())
                self.assertTrue(all(isinstance(h, SafeHandler) for h in handlers))

    def test_empty_environment_spec_replaces_defaults(self):
        os.environ["LOG_HANDLERS_COMPLIANCE"] = ""
        self.assertEqual(default_handlers(Tier.COMPLIANCE, load_logger_config()), [])

    def test_default_destinations(self):
        cfg = LoggerConfig()
        compliance = default_handlers(Tier.COMPLIANCE, cfg)
        self.assertEqual([type(h.inner) for h in compliance], [StdoutHandler, FileHandler])
        self.assertEqual(compliance[1].inner.path, Path("/var/log/compliance/audit.log"))
        self.assertEqual([type(h.inner) for h in default_handlers(Tier.BUSINESS, cfg)],
                         [StdoutHandler])
        self.assertEqual([type(h.inner) for h in default_handlers(Tier.INFRASTRUCTURE, cfg)],
                         [StdoutHandler])
        os.environ.update(LOG_COMPLIANCE_FILE="custom/audit.log",
                          LOG_BUSINESS_HTTP_URL="https://example.test/logs")
        cfg = load_logger_config()
        self.assertEqual(default_handlers(Tier.COMPLIANCE, cfg)[1].inner.path,
                         Path("custom/audit.log"))
        self.assertEqual(default_handlers(Tier.BUSINESS, cfg)[1].inner.url,
                         "https://example.test/logs")

    def test_file_handler_appends_json_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "log.jsonl"
            handler = FileHandler(path)
            handler.emit({"n": 1})
            handler.emit({"n": 2})
            self.assertEqual([json.loads(line) for line in path.read_text().splitlines()],
                             [{"n": 1}, {"n": 2}])

    def test_http_handler_posts_json(self):
        with patch("core_logger.handlers.urllib.request.urlopen") as urlopen:
            HttpHandler("https://example.test/logs", timeout=0.5).emit({"n": 1})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/logs")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data), {"n": 1})
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 0.5)

    def test_configuration_is_cached_and_reloadable(self):
        original = get_logger_config()
        os.environ.update(LOG_INCLUDE_TIMESTAMP="false", LOG_SERVICE_TIER="business")
        self.assertIs(get_logger_config(), original)
        self.assertTrue(get_logger_config().include_timestamp)
        self.assertFalse(load_logger_config().include_timestamp)
        self.assertEqual(load_logger_config().service_tier, "business")
        self.assertIn("timestamp", format_log("INFO", "x", "hello", {}))
        reload_logger_config()
        self.assertFalse(get_logger_config().include_timestamp)
        self.assertNotIn("timestamp", format_log("INFO", "x", "hello", {}))


if __name__ == "__main__":
    unittest.main()
