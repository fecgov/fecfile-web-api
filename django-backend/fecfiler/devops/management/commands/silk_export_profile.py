import importlib
import json
import os
import re
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from django.core.management.base import CommandError
from django.utils import timezone
from django.utils.html import escape
from django.core.serializers.json import DjangoJSONEncoder
from fecfiler.devops.management.commands.fecfile_base import FECCommand, Levels
from fecfiler.shared.utilities import get_boolean_from_string
from fecfiler.silk_profile_gate import extract_profile_headers

SQL_QUERY_EXPORT_LIMIT = 5000
SQL_QUERY_TEXT_LIMIT = 2000
SAFE_PATH_RE = re.compile(r"[^A-Za-z0-9._-]+")
SAFE_NAME_MAX = 80
SLOW_ITEM_LIMIT = 25


def _normalize_header_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _decode_header_bytes(raw_value: Any) -> Any:
    if isinstance(raw_value, bytes):
        try:
            return raw_value.decode("utf-8")
        except UnicodeDecodeError:
            return raw_value.decode("latin-1", errors="ignore")
    return raw_value


def _parse_header_payload(raw_value: Any) -> Any:
    if isinstance(raw_value, str):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return None
    return raw_value


def _normalize_header_mapping(mapping: Dict[Any, Any]) -> Dict[str, str]:
    return {
        str(key).lower(): _normalize_header_value(value)
        for key, value in mapping.items()
    }


def _normalize_header_list(items: List[Any]) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            headers[str(item[0]).lower()] = _normalize_header_value(item[1])
            continue
        if isinstance(item, dict):
            headers.update(_normalize_header_mapping(item))
    return headers


def _decode_encoded_headers(encoded_headers: Any) -> Dict[str, str]:
    if not encoded_headers:
        return {}

    raw_value = _decode_header_bytes(encoded_headers)
    raw_value = _parse_header_payload(raw_value)
    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return _normalize_header_mapping(raw_value)
    if isinstance(raw_value, list):
        return _normalize_header_list(raw_value)
    return {}


def _sanitize_path_segment(value: Optional[str], fallback: str) -> str:
    if not value:
        return fallback
    cleaned = SAFE_PATH_RE.sub("_", value.strip())
    cleaned = cleaned.strip("._-")
    if not cleaned:
        return fallback
    return cleaned[:SAFE_NAME_MAX]


def _sanitize_run_id(run_id: str) -> str:
    return _sanitize_path_segment(str(run_id), "unknown-run")


def _get_silk_models():
    silk_models = importlib.import_module("silk.models")
    return silk_models.Request, silk_models.SQLQuery


def _format_duration(value: Optional[float]) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _truncate_query(query_text: Optional[str]) -> str:
    if not query_text:
        return ""
    if len(query_text) <= SQL_QUERY_TEXT_LIMIT:
        return query_text
    return f"{query_text[:SQL_QUERY_TEXT_LIMIT]}..."


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, cls=DjangoJSONEncoder)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


def _render_summary_html(
    run_id: str,
    client: str,
    group: str,
    totals: Dict[str, Any],
    slow_requests: List[Dict[str, Any]],
    slow_queries: List[Dict[str, Any]],
) -> str:
    rows = []
    for request in slow_requests:
        rows.append(
            "<tr>"
            f"<td>{escape(str(request.get('method', '')))}</td>"
            f"<td>{escape(str(request.get('path', '')))}</td>"
            f"<td>{escape(str(request.get('status_code', '')))}</td>"
            f"<td>{request.get('time_taken', 0):.4f}</td>"
            f"<td>{request.get('time_spent_on_sql', 0):.4f}</td>"
            "</tr>"
        )
    request_table = "\n".join(rows) or (
        "<tr><td colspan='5'>No requests found.</td></tr>"
    )

    query_rows = []
    for query in slow_queries:
        query_rows.append(
            "<tr>"
            f"<td>{query.get('time_taken', 0):.4f}</td>"
            f"<td>{escape(str(query.get('request_path', '')))}</td>"
            f"<td><pre>{escape(str(query.get('query', '')))}</pre></td>"
            "</tr>"
        )
    query_table = "\n".join(query_rows) or (
        "<tr><td colspan='3'>No queries found.</td></tr>"
    )

    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Silk Profile Summary</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
      h1, h2 {{ margin-bottom: 8px; }}
      table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background: #f3f3f3; }}
      pre {{ white-space: pre-wrap; margin: 0; }}
      .meta {{ margin-bottom: 16px; }}
    </style>
  </head>
  <body>
    <h1>Silk Profile Summary</h1>
    <div class="meta">
      <div><strong>Run ID:</strong> {escape(run_id)}</div>
      <div><strong>Client:</strong> {escape(client)}</div>
      <div><strong>Group:</strong> {escape(group)}</div>
      <div><strong>Total Requests:</strong> {totals.get('total_requests', 0)}</div>
      <div><strong>Total Time:</strong> {totals.get('total_time_taken', 0):.4f}s</div>
      <div><strong>Total SQL Time:</strong> {totals.get('total_sql_time', 0):.4f}s</div>
    </div>
    <h2>Slow Requests</h2>
    <table>
      <thead>
        <tr>
          <th>Method</th>
          <th>Path</th>
          <th>Status</th>
          <th>Time Taken (s)</th>
          <th>SQL Time (s)</th>
        </tr>
      </thead>
      <tbody>
        {request_table}
      </tbody>
    </table>
    <h2>Slow Queries</h2>
    <table>
      <thead>
        <tr>
          <th>Time Taken (s)</th>
          <th>Request Path</th>
          <th>Query</th>
        </tr>
      </thead>
      <tbody>
        {query_table}
      </tbody>
    </table>
  </body>
</html>
"""


def _render_index_html(run_meta: Dict[str, Any], groups: List[Dict[str, Any]]) -> str:
    rows = []
    for group in groups:
        rows.append(
            "<tr>"
            f"<td>{escape(group['client'])}</td>"
            f"<td>{escape(group['group'])}</td>"
            f"<td>{group['total_requests']}</td>"
            f"<td>{group['total_time_taken']:.4f}</td>"
            f"<td>{group['total_sql_time']:.4f}</td>"
            f"<td><a href=\"{escape(group['summary_path'])}\">summary</a></td>"
            "</tr>"
        )
    body_rows = "\n".join(rows) or "<tr><td colspan='6'>No groups found.</td></tr>"

    run_id_display = escape(str(run_meta.get("run_id", "")))
    generated_display = escape(str(run_meta.get("generated_at", "")))
    with_locust_display = escape(str(run_meta.get("with_locust", False)))
    analyze_display = escape(str(run_meta.get("silky_analyze_queries", False)))
    sample_display = escape(str(run_meta.get("locust_sample_pct", "")))

    return f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Silk Profile Index</title>
    <style>
      body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
      table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
      th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      th {{ background: #f3f3f3; }}
      .meta {{ margin-bottom: 16px; }}
    </style>
  </head>
  <body>
    <h1>Silk Profile Index</h1>
    <div class="meta">
      <div><strong>Run ID:</strong> {run_id_display}</div>
      <div><strong>Generated:</strong> {generated_display}</div>
      <div><strong>With Locust:</strong> {with_locust_display}</div>
      <div><strong>Silky Analyze Queries:</strong> {analyze_display}</div>
      <div><strong>Locust Sample Pct:</strong> {sample_display}</div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Client</th>
          <th>Group</th>
          <th>Total Requests</th>
          <th>Total Time (s)</th>
          <th>Total SQL Time (s)</th>
          <th>Link</th>
        </tr>
      </thead>
      <tbody>
        {body_rows}
      </tbody>
    </table>
  </body>
</html>
"""


def _ensure_silk_enabled() -> None:
    if "silk" not in settings.INSTALLED_APPS:
        raise CommandError(
            "Silk is not enabled. Set FECFILE_SILK_ENABLED=1 and run migrations."
        )


def _normalize_client_filter(client_filter: Optional[str]) -> Optional[str]:
    if not client_filter:
        return None
    normalized = client_filter.lower()
    if normalized not in ["cypress", "locust"]:
        raise CommandError("client must be cypress or locust")
    return normalized


def _build_request_queryset(request_model, minutes: Optional[int]):
    queryset = request_model.objects.filter(path__startswith="/api/")
    if minutes:
        cutoff = timezone.now() - timedelta(minutes=minutes)
        queryset = queryset.filter(start_time__gte=cutoff)
    return queryset


def _match_profile_headers(
    profile_headers: Dict[str, Optional[str]],
    run_id: str,
    client_filter: Optional[str],
    group_filter: Optional[str],
) -> Optional[Tuple[str, str]]:
    if profile_headers.get("run_id") != run_id:
        return None

    client = profile_headers.get("client") or "unknown-client"
    group = profile_headers.get("group") or "unknown-group"
    if client_filter and client != client_filter:
        return None
    if group_filter and group != group_filter:
        return None
    return client, group


def _extract_request_metrics(request) -> Tuple[float, float, int]:
    time_taken = _format_duration(getattr(request, "time_taken", None))
    sql_time = _format_duration(getattr(request, "time_spent_on_sql", None))
    num_queries = getattr(request, "num_sql_queries", 0) or 0
    return time_taken, sql_time, num_queries


def _get_request_status_code(request) -> Optional[int]:
    try:
        response = request.response
    except Exception:
        response = None
    if response is not None:
        return getattr(response, "status_code", None)
    return getattr(request, "status_code", None)


def _update_totals(
    totals: Dict[str, Any], time_taken: float, sql_time: float, num_queries: int
) -> None:
    totals["total_requests"] += 1
    totals["total_time_taken"] += time_taken
    totals["total_sql_time"] += sql_time
    totals["total_queries"] += num_queries


def _build_request_entry(
    request,
    profile_headers: Dict[str, Optional[str]],
    time_taken: float,
    sql_time: float,
    num_queries: int,
) -> Dict[str, Any]:
    return {
        "id": request.id,
        "method": request.method,
        "path": request.path,
        "status_code": _get_request_status_code(request),
        "start_time": request.start_time,
        "time_taken": time_taken,
        "num_queries": num_queries,
        "time_spent_on_sql": sql_time,
        "profile_headers": profile_headers,
    }


def _collect_requests(
    queryset,
    run_id: str,
    client_filter: Optional[str],
    group_filter: Optional[str],
) -> Tuple[
    Dict[Tuple[str, str], List[Dict[str, Any]]],
    Dict[Tuple[str, str], Dict[str, Any]],
    Dict[int, Tuple[str, str]],
    Dict[int, str],
]:
    requests_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(
        list
    )
    totals_by_group: Dict[Tuple[str, str], Dict[str, Any]] = {}
    request_group_index: Dict[int, Tuple[str, str]] = {}
    request_path_index: Dict[int, str] = {}

    for request in queryset.iterator():
        headers = _decode_encoded_headers(request.encoded_headers)
        profile_headers = extract_profile_headers(headers)
        group_key = _match_profile_headers(
            profile_headers, run_id, client_filter, group_filter
        )
        if not group_key:
            continue

        time_taken, sql_time, num_queries = _extract_request_metrics(request)
        totals = totals_by_group.setdefault(
            group_key,
            {
                "total_requests": 0,
                "total_time_taken": 0.0,
                "total_sql_time": 0.0,
                "total_queries": 0,
            },
        )
        _update_totals(totals, time_taken, sql_time, num_queries)

        requests_by_group[group_key].append(
            _build_request_entry(
                request, profile_headers, time_taken, sql_time, num_queries
            )
        )
        request_group_index[request.id] = group_key
        request_path_index[request.id] = request.path

    return (
        requests_by_group,
        totals_by_group,
        request_group_index,
        request_path_index,
    )


def _load_slow_queries(
    sql_query_model,
    request_group_index: Dict[int, Tuple[str, str]],
    request_path_index: Dict[int, str],
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    slow_queries_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(
        list
    )
    if request_group_index:
        request_ids = list(request_group_index.keys())
        for query in sql_query_model.objects.filter(
            request_id__in=request_ids
        ).order_by("-time_taken"):
            group_key = request_group_index.get(query.request_id)
            if not group_key:
                continue
            group_queries = slow_queries_by_group[group_key]
            if len(group_queries) >= SQL_QUERY_EXPORT_LIMIT:
                continue
            group_queries.append(
                {
                    "time_taken": _format_duration(getattr(query, "time_taken", None)),
                    "query": _truncate_query(getattr(query, "query", None)),
                    "request_path": request_path_index.get(query.request_id),
                }
            )
    return slow_queries_by_group


def _write_group_exports(
    outdir: Path,
    safe_run_id: str,
    run_id: str,
    requests_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]],
    totals_by_group: Dict[Tuple[str, str], Dict[str, Any]],
    slow_queries_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    group_summaries: List[Dict[str, Any]] = []

    for (client, group), entries in requests_by_group.items():
        safe_client = _sanitize_path_segment(client, "unknown-client")
        safe_group = _sanitize_path_segment(group, "unknown-group")
        group_dir = outdir / safe_run_id / safe_client / safe_group

        totals = totals_by_group[(client, group)]
        entries_sorted = sorted(
            entries, key=lambda item: item.get("time_taken", 0), reverse=True
        )
        slow_requests = entries_sorted[:SLOW_ITEM_LIMIT]
        slow_queries = slow_queries_by_group.get((client, group), [])[:SLOW_ITEM_LIMIT]

        profile_payload = {
            "run_id": run_id,
            "client": client,
            "group": group,
            "generated_at": timezone.now(),
            "totals": totals,
            "requests": entries_sorted,
            "slow_queries": slow_queries_by_group.get((client, group), []),
        }

        _write_json(group_dir / "profile.json", profile_payload)

        summary_html = _render_summary_html(
            run_id, client, group, totals, slow_requests, slow_queries
        )
        _write_text(group_dir / "summary.html", summary_html)

        group_summaries.append(
            {
                "client": client,
                "group": group,
                "total_requests": totals["total_requests"],
                "total_time_taken": totals["total_time_taken"],
                "total_sql_time": totals["total_sql_time"],
                "summary_path": f"./{safe_client}/{safe_group}/summary.html",
            }
        )

    group_summaries.sort(
        key=lambda item: (item["total_time_taken"], item["total_sql_time"]),
        reverse=True,
    )
    return group_summaries


def _build_run_meta(
    run_id: str, group_summaries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    with_locust = any(item["client"] == "locust" for item in group_summaries)
    with_locust = with_locust or get_boolean_from_string(
        os.environ.get("FECFILE_PROFILE_WITH_LOCUST", "False")
    )
    return {
        "run_id": run_id,
        "generated_at": timezone.now().isoformat(),
        "with_locust": with_locust,
        "silky_analyze_queries": getattr(settings, "SILKY_ANALYZE_QUERIES", False),
        "locust_sample_pct": os.environ.get("FECFILE_LOCUST_SILK_SAMPLE_PCT", "2.0"),
    }


class Command(FECCommand):
    help = "Export Silk profiling artifacts grouped by profiling headers."
    command_name = "silk_export_profile"

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True)
        parser.add_argument("--outdir", default="silk")
        parser.add_argument("--client", choices=["cypress", "locust"])
        parser.add_argument("--group")
        parser.add_argument("--minutes", type=int)

    def command(self, *args, **options):
        _ensure_silk_enabled()
        request_model, sql_query_model = _get_silk_models()

        run_id = options["run_id"]
        safe_run_id = _sanitize_run_id(run_id)
        outdir = Path(options["outdir"])
        client_filter = _normalize_client_filter(options.get("client"))
        group_filter = options.get("group")
        minutes = options.get("minutes")

        queryset = _build_request_queryset(request_model, minutes)
        (
            requests_by_group,
            totals_by_group,
            request_group_index,
            request_path_index,
        ) = _collect_requests(queryset, run_id, client_filter, group_filter)

        if not requests_by_group:
            self.log("No matching Silk requests found.", Levels.WARNING)

        slow_queries_by_group = _load_slow_queries(
            sql_query_model, request_group_index, request_path_index
        )

        group_summaries = _write_group_exports(
            outdir,
            safe_run_id,
            run_id,
            requests_by_group,
            totals_by_group,
            slow_queries_by_group,
        )

        run_meta = _build_run_meta(run_id, group_summaries)
        index_html = _render_index_html(run_meta, group_summaries)
        _write_text(outdir / safe_run_id / "index.html", index_html)

        self.log(
            f"Wrote Silk profiling export to {outdir / safe_run_id}",
            Levels.SUCCESS,
        )
