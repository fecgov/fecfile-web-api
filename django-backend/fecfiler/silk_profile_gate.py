import os
import random
from typing import Any, Dict, Mapping, Optional, Tuple

from fecfiler.shared.utilities import get_boolean_from_string, get_float_from_string

ALLOWED_PROFILE_CLIENTS = {"cypress", "locust"}
PROFILE_HEADER_NAMES = {
    "run_id": ("x-fecfile-profile-run-id", "x-fecfile-e2e-run-id"),
    "client": ("x-fecfile-profile-client",),
    "group": ("x-fecfile-profile-group", "x-fecfile-e2e-spec"),
    "test": ("x-fecfile-profile-test", "x-fecfile-e2e-test"),
    "seq": ("x-fecfile-profile-seq", "x-fecfile-e2e-seq"),
}
E2E_HEADER_NAMES = (
    "x-fecfile-e2e-run-id",
    "x-fecfile-e2e-spec",
    "x-fecfile-e2e-test",
    "x-fecfile-e2e-seq",
)
ALL_PROFILE_HEADER_NAMES = tuple(
    {name for names in PROFILE_HEADER_NAMES.values() for name in names}
)


def _normalize_header_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = ",".join(str(item) for item in value)
    value = str(value).strip()
    return value or None


def _first_header_value(
    headers: Mapping[str, Any], names: Tuple[str, ...]
) -> Optional[str]:
    for name in names:
        value = _normalize_header_value(headers.get(name))
        if value:
            return value
    return None


def extract_profile_headers(headers: Mapping[str, Any]) -> Dict[str, Optional[str]]:
    normalized = {
        key.lower(): _normalize_header_value(value)
        for key, value in headers.items()
        if key
    }
    run_id = _first_header_value(normalized, PROFILE_HEADER_NAMES["run_id"])
    client = _first_header_value(normalized, PROFILE_HEADER_NAMES["client"])
    group = _first_header_value(normalized, PROFILE_HEADER_NAMES["group"])
    test = _first_header_value(normalized, PROFILE_HEADER_NAMES["test"])
    seq = _first_header_value(normalized, PROFILE_HEADER_NAMES["seq"])

    if not client and any(normalized.get(name) for name in E2E_HEADER_NAMES):
        client = "cypress"
    if client:
        client = client.lower()
    if client not in ALLOWED_PROFILE_CLIENTS:
        client = None

    return {
        "run_id": run_id,
        "client": client,
        "group": group,
        "test": test,
        "seq": seq,
    }


def get_profile_headers(request) -> Dict[str, Optional[str]]:
    header_values: Dict[str, Any] = {}
    for header_name in ALL_PROFILE_HEADER_NAMES:
        meta_key = f"HTTP_{header_name.upper().replace('-', '_')}"
        meta_value = request.META.get(meta_key)
        if meta_value:
            header_values[header_name] = meta_value
    return extract_profile_headers(header_values)


def _locust_enabled() -> bool:
    return get_boolean_from_string(
        os.environ.get("FECFILE_PROFILE_WITH_LOCUST", "False")
    )


def _locust_sample_pct() -> float:
    return max(
        0.0,
        min(
            get_float_from_string(
                os.environ.get("FECFILE_LOCUST_SILK_SAMPLE_PCT", "2.0"), fallback=2.0
            ),
            100.0,
        ),
    )


def should_record(request) -> bool:
    if not request.path.startswith("/api/"):
        return False

    profile_headers = get_profile_headers(request)
    run_id = profile_headers.get("run_id")
    if not run_id:
        return False

    expected_run_id = os.environ.get("FECFILE_PROFILE_RUN_ID")
    if expected_run_id and expected_run_id != run_id:
        return False

    client = profile_headers.get("client")
    if client not in ALLOWED_PROFILE_CLIENTS:
        return False

    if client == "locust":
        if not _locust_enabled():
            return False
        return random.random() < (_locust_sample_pct() / 100.0)

    return True


def should_profile(request) -> bool:
    return should_record(request)
