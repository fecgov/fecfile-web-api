import os
from unittest.mock import patch

from django.test import SimpleTestCase

from fecfiler.silk_profile_gate import (
    _locust_should_record,
    extract_profile_headers,
    get_profile_headers,
    should_profile,
    should_record,
)


class DummyRequest:
    def __init__(self, path, meta):
        self.path = path
        self.META = meta


def _build_meta(headers):
    meta = {}
    for name, value in headers.items():
        meta_key = f"HTTP_{name.upper().replace('-', '_')}"
        meta[meta_key] = value
    return meta


class SilkProfileGateTest(SimpleTestCase):
    def test_extract_profile_headers_uses_aliases(self):
        headers = {
            "x-fecfile-e2e-run-id": "run-1",
            "x-fecfile-e2e-spec": "spec-a",
            "x-fecfile-e2e-test": "test-1",
            "x-fecfile-e2e-seq": "1",
        }
        result = extract_profile_headers(headers)
        self.assertEqual(result["run_id"], "run-1")
        self.assertEqual(result["client"], "cypress")
        self.assertEqual(result["group"], "spec-a")
        self.assertEqual(result["test"], "test-1")
        self.assertEqual(result["seq"], "1")

    def test_extract_profile_headers_rejects_invalid_client(self):
        headers = {
            "x-fecfile-profile-run-id": "run-1",
            "x-fecfile-profile-client": "unknown",
        }
        result = extract_profile_headers(headers)
        self.assertIsNone(result["client"])

    def test_get_profile_headers_reads_request_meta(self):
        meta = _build_meta(
            {
                "x-fecfile-profile-run-id": "run-2",
                "x-fecfile-profile-client": "cypress",
                "x-fecfile-profile-group": "spec-b",
            }
        )
        request = DummyRequest("/api/test", meta)
        result = get_profile_headers(request)
        self.assertEqual(result["run_id"], "run-2")
        self.assertEqual(result["client"], "cypress")
        self.assertEqual(result["group"], "spec-b")

    def test_should_record_requires_api_and_run_id(self):
        meta = _build_meta({"x-fecfile-profile-client": "cypress"})
        request = DummyRequest("/api/test", meta)
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(should_record(request))
        request = DummyRequest("/not-api/test", meta)
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(should_record(request))

    def test_should_record_enforces_expected_run_id(self):
        meta = _build_meta(
            {
                "x-fecfile-profile-run-id": "run-1",
                "x-fecfile-profile-client": "cypress",
            }
        )
        request = DummyRequest("/api/test", meta)
        with patch.dict(os.environ, {"FECFILE_PROFILE_RUN_ID": "run-2"}, clear=True):
            self.assertFalse(should_record(request))

    def test_should_record_cypress_allows(self):
        meta = _build_meta(
            {
                "x-fecfile-profile-run-id": "run-1",
                "x-fecfile-profile-client": "cypress",
            }
        )
        request = DummyRequest("/api/test", meta)
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(should_record(request))
            self.assertEqual(should_profile(request), should_record(request))

    def test_should_record_locust_requires_enabled(self):
        meta = _build_meta(
            {
                "x-fecfile-profile-run-id": "run-1",
                "x-fecfile-profile-client": "locust",
            }
        )
        request = DummyRequest("/api/test", meta)
        with patch.dict(os.environ, {"FECFILE_PROFILE_WITH_LOCUST": "0"}, clear=True):
            self.assertFalse(should_record(request))

    def test_locust_sampling_uses_secure_rng(self):
        meta = _build_meta(
            {
                "x-fecfile-profile-run-id": "run-1",
                "x-fecfile-profile-client": "locust",
            }
        )
        request = DummyRequest("/api/test", meta)
        env = {
            "FECFILE_PROFILE_WITH_LOCUST": "1",
            "FECFILE_LOCUST_SILK_SAMPLE_PCT": "2.0",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch(
                "fecfiler.silk_profile_gate.secrets.randbelow", return_value=0
            ):
                self.assertTrue(should_record(request))
            with patch(
                "fecfiler.silk_profile_gate.secrets.randbelow", return_value=9999
            ):
                self.assertFalse(should_record(request))

    def test_locust_should_record_handles_bounds(self):
        self.assertFalse(_locust_should_record(0))
        self.assertTrue(_locust_should_record(100))
