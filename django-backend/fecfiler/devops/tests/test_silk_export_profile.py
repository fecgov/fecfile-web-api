import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from fecfiler.devops.management.commands import silk_export_profile as export


class DummyRequest:
    def __init__(
        self,
        request_id,
        path,
        encoded_headers,
        method="GET",
        status_code=200,
        start_time=None,
        time_taken=0.1,
        sql_time=0.05,
        num_queries=1,
    ):
        self.id = request_id
        self.path = path
        self.method = method
        self.status_code = status_code
        self.start_time = start_time or timezone.now()
        self.time_taken = time_taken
        self.time_spent_on_sql = sql_time
        self.num_sql_queries = num_queries
        self.encoded_headers = encoded_headers


class DummyQuerySet:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, **kwargs):
        items = self._items
        cutoff = kwargs.get("start_time__gte")
        if cutoff:
            items = [item for item in items if item.start_time >= cutoff]
        return DummyQuerySet(items)

    def iterator(self):
        return iter(self._items)


class DummyRequestManager:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, **kwargs):
        prefix = kwargs.get("path__startswith")
        items = self._items
        if prefix:
            items = [item for item in items if item.path.startswith(prefix)]
        return DummyQuerySet(items)


class DummyRequestModel:
    def __init__(self, items):
        self.objects = DummyRequestManager(items)


class DummyQuery:
    def __init__(self, request_id, time_taken=0.1, query="select 1"):
        self.request_id = request_id
        self.time_taken = time_taken
        self.query = query


class DummyQueryManager:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, **kwargs):
        request_ids = kwargs.get("request_id__in")
        if request_ids is None:
            return self
        items = [item for item in self._items if item.request_id in request_ids]
        return DummyQueryManager(items)

    def order_by(self, *args):
        return self._items


class DummyQueryModel:
    def __init__(self, items):
        self.objects = DummyQueryManager(items)


class SilkExportProfileTest(SimpleTestCase):
    def test_decode_encoded_headers_handles_variants(self):
        payload = {"X-Test": "Value"}
        encoded = json.dumps(payload).encode("utf-8")
        headers = export._decode_encoded_headers(encoded)
        self.assertEqual(headers["x-test"], "Value")

        headers = export._decode_encoded_headers("not-json")
        self.assertEqual(headers, {})

        list_payload = json.dumps([["X-Test", "Value"]])
        headers = export._decode_encoded_headers(list_payload)
        self.assertEqual(headers["x-test"], "Value")

        dict_list_payload = json.dumps([{"X-Test": "Value"}])
        headers = export._decode_encoded_headers(dict_list_payload)
        self.assertEqual(headers["x-test"], "Value")

    def test_sanitize_path_segment_and_run_id(self):
        cleaned = export._sanitize_path_segment("..//bad/..", "fallback")
        self.assertEqual(cleaned, "bad")
        run_id = export._sanitize_run_id("../")
        self.assertEqual(run_id, "unknown-run")

    def test_truncate_query(self):
        short_query = "select 1"
        self.assertEqual(export._truncate_query(short_query), short_query)
        long_query = "x" * (export.SQL_QUERY_TEXT_LIMIT + 5)
        truncated = export._truncate_query(long_query)
        self.assertTrue(truncated.endswith("..."))

    def test_normalize_client_filter(self):
        self.assertEqual(export._normalize_client_filter("CYPRESS"), "cypress")
        with self.assertRaises(CommandError):
            export._normalize_client_filter("bad-client")

    def test_match_profile_headers(self):
        profile = {"run_id": "run-1", "client": "cypress", "group": "spec-a"}
        result = export._match_profile_headers(profile, "run-1", None, None)
        self.assertEqual(result, ("cypress", "spec-a"))
        result = export._match_profile_headers(profile, "other", None, None)
        self.assertIsNone(result)

    def test_collect_requests_groups_and_totals(self):
        run_id = "run-1"
        headers = {
            "x-fecfile-profile-run-id": run_id,
            "x-fecfile-profile-client": "cypress",
            "x-fecfile-profile-group": "spec-a",
        }
        encoded = json.dumps(headers)
        request_ok = DummyRequest(1, "/api/test", encoded, time_taken=1.5)
        request_skip = DummyRequest(
            2, "/api/test", json.dumps({"x-fecfile-profile-run-id": "other"})
        )
        queryset = DummyQuerySet([request_ok, request_skip])

        (
            requests_by_group,
            totals_by_group,
            request_group_index,
            request_path_index,
        ) = export._collect_requests(queryset, run_id, None, None)

        key = ("cypress", "spec-a")
        self.assertIn(key, requests_by_group)
        self.assertEqual(totals_by_group[key]["total_requests"], 1)
        self.assertEqual(request_group_index[1], key)
        self.assertEqual(request_path_index[1], "/api/test")

    def test_load_slow_queries_filters_by_request(self):
        request_group_index = {1: ("cypress", "spec-a")}
        request_path_index = {1: "/api/test"}
        queries = [
            DummyQuery(1, time_taken=0.2, query="select 1"),
            DummyQuery(2, time_taken=0.3, query="select 2"),
        ]
        sql_model = DummyQueryModel(queries)
        result = export._load_slow_queries(
            sql_model, request_group_index, request_path_index
        )
        self.assertEqual(len(result[("cypress", "spec-a")]), 1)
        self.assertEqual(result[("cypress", "spec-a")][0]["request_path"], "/api/test")

    def test_write_group_exports_creates_files(self):
        run_id = "run-1"
        key = ("cypress", "spec-a")
        entries = [{"time_taken": 0.1, "path": "/api/test"}]
        totals = {
            "total_requests": 1,
            "total_time_taken": 0.1,
            "total_sql_time": 0.05,
            "total_queries": 1,
        }
        requests_by_group = {key: entries}
        totals_by_group = {key: totals}
        slow_queries_by_group = {key: [{"time_taken": 0.1, "query": "select 1"}]}

        with tempfile.TemporaryDirectory() as tmpdir:
            outdir = Path(tmpdir)
            summaries = export._write_group_exports(
                outdir,
                "run-1",
                run_id,
                requests_by_group,
                totals_by_group,
                slow_queries_by_group,
            )
            profile_path = outdir / "run-1" / "cypress" / "spec-a" / "profile.json"
            summary_path = outdir / "run-1" / "cypress" / "spec-a" / "summary.html"
            self.assertTrue(profile_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertEqual(summaries[0]["client"], "cypress")

    @override_settings(SILKY_ANALYZE_QUERIES=True)
    def test_build_run_meta_uses_env(self):
        group_summaries = [{"client": "locust"}]
        env = {
            "FECFILE_PROFILE_WITH_LOCUST": "1",
            "FECFILE_LOCUST_SILK_SAMPLE_PCT": "5.0",
        }
        with patch.dict(os.environ, env, clear=True):
            meta = export._build_run_meta("run-1", group_summaries)
        self.assertTrue(meta["with_locust"])
        self.assertEqual(meta["locust_sample_pct"], "5.0")
        self.assertTrue(meta["silky_analyze_queries"])

    def test_ensure_silk_enabled(self):
        with patch.object(settings, "INSTALLED_APPS", ["django.contrib.auth"]):
            with self.assertRaises(CommandError):
                export._ensure_silk_enabled()
        with patch.object(settings, "INSTALLED_APPS", ["silk"]):
            export._ensure_silk_enabled()

    def test_command_writes_index(self):
        run_id = "run-1"
        headers = {
            "x-fecfile-profile-run-id": run_id,
            "x-fecfile-profile-client": "cypress",
            "x-fecfile-profile-group": "spec-a",
        }
        encoded = json.dumps(headers)
        request = DummyRequest(1, "/api/test", encoded, time_taken=0.4)
        request_model = DummyRequestModel([request])
        query_model = DummyQueryModel([DummyQuery(1, time_taken=0.2)])

        with tempfile.TemporaryDirectory() as tmpdir:
            outdir = Path(tmpdir)
            command = export.Command()
            command.verbosity = 0
            with patch.object(export, "_ensure_silk_enabled"), patch.object(
                export, "_get_silk_models", return_value=(request_model, query_model)
            ):
                command.command(
                    run_id=run_id,
                    outdir=str(outdir),
                    client=None,
                    group=None,
                    minutes=None,
                )
            index_path = outdir / export._sanitize_run_id(run_id) / "index.html"
            self.assertTrue(index_path.exists())
