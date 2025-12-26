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


def _normalize_header_value(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _decode_encoded_headers(encoded_headers: Any) -> Dict[str, str]:
    if not encoded_headers:
        return {}

    raw_value = encoded_headers
    if isinstance(raw_value, bytes):
        try:
            raw_value = raw_value.decode("utf-8")
        except UnicodeDecodeError:
            raw_value = raw_value.decode("latin-1", errors="ignore")

    if isinstance(raw_value, str):
        try:
            raw_value = json.loads(raw_value)
        except json.JSONDecodeError:
            return {}

    if isinstance(raw_value, dict):
        return {
            str(key).lower(): _normalize_header_value(value)
            for key, value in raw_value.items()
        }

    if isinstance(raw_value, list):
        headers: Dict[str, str] = {}
        for item in raw_value:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                headers[str(item[0]).lower()] = _normalize_header_value(item[1])
            elif isinstance(item, dict):
                for key, value in item.items():
                    headers[str(key).lower()] = _normalize_header_value(value)
        return headers

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
        if "silk" not in settings.INSTALLED_APPS:
            raise CommandError(
                "Silk is not enabled. Set FECFILE_SILK_ENABLED=1 and run migrations."
            )

        Request, SQLQuery = _get_silk_models()

        run_id = options["run_id"]
        safe_run_id = _sanitize_run_id(run_id)
        outdir = Path(options["outdir"])
        client_filter = options.get("client")
        group_filter = options.get("group")
        minutes = options.get("minutes")

        if client_filter:
            client_filter = client_filter.lower()
            if client_filter not in ["cypress", "locust"]:
                raise CommandError("client must be cypress or locust")

        queryset = Request.objects.filter(path__startswith="/api/")
        if minutes:
            cutoff = timezone.now() - timedelta(minutes=minutes)
            queryset = queryset.filter(start_time__gte=cutoff)

        requests_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(
            list
        )
        totals_by_group: Dict[Tuple[str, str], Dict[str, Any]] = {}
        request_group_index: Dict[int, Tuple[str, str]] = {}
        request_path_index: Dict[int, str] = {}

        for request in queryset.iterator():
            headers = _decode_encoded_headers(request.encoded_headers)
            profile_headers = extract_profile_headers(headers)
            if profile_headers.get("run_id") != run_id:
                continue

            client = profile_headers.get("client") or "unknown-client"
            group = profile_headers.get("group") or "unknown-group"
            if client_filter and client != client_filter:
                continue
            if group_filter and group != group_filter:
                continue

            key = (client, group)
            total = totals_by_group.setdefault(
                key,
                {
                    "total_requests": 0,
                    "total_time_taken": 0.0,
                    "total_sql_time": 0.0,
                    "total_queries": 0,
                },
            )

            time_taken = _format_duration(getattr(request, "time_taken", None))
            sql_time = _format_duration(getattr(request, "time_spent_on_sql", None))
            num_queries = getattr(request, "num_sql_queries", 0) or 0

            total["total_requests"] += 1
            total["total_time_taken"] += time_taken
            total["total_sql_time"] += sql_time
            total["total_queries"] += num_queries

            requests_by_group[key].append(
                {
                    "id": request.id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": request.status_code,
                    "start_time": request.start_time,
                    "time_taken": time_taken,
                    "num_queries": num_queries,
                    "time_spent_on_sql": sql_time,
                    "profile_headers": profile_headers,
                }
            )
            request_group_index[request.id] = key
            request_path_index[request.id] = request.path

        if not requests_by_group:
            self.log("No matching Silk requests found.", Levels.WARNING)

        request_ids = list(request_group_index.keys())
        slow_queries_by_group: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(
            list
        )
        if request_ids:
            for query in SQLQuery.objects.filter(request_id__in=request_ids).order_by(
                "-time_taken"
            ):
                group_key = request_group_index.get(query.request_id)
                if not group_key:
                    continue
                group_queries = slow_queries_by_group[group_key]
                if len(group_queries) >= SQL_QUERY_EXPORT_LIMIT:
                    continue
                group_queries.append(
                    {
                        "time_taken": _format_duration(
                            getattr(query, "time_taken", None)
                        ),
                        "query": _truncate_query(getattr(query, "query", None)),
                        "request_path": request_path_index.get(query.request_id),
                    }
                )

        group_summaries: List[Dict[str, Any]] = []
        for (client, group), entries in requests_by_group.items():
            safe_client = _sanitize_path_segment(client, "unknown-client")
            safe_group = _sanitize_path_segment(group, "unknown-group")
            group_dir = outdir / safe_run_id / safe_client / safe_group

            totals = totals_by_group[(client, group)]
            entries_sorted = sorted(
                entries, key=lambda item: item.get("time_taken", 0), reverse=True
            )
            slow_requests = entries_sorted[:25]
            slow_queries = slow_queries_by_group.get((client, group), [])[:25]

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

        run_meta = {
            "run_id": run_id,
            "generated_at": timezone.now().isoformat(),
            "with_locust": any(item["client"] == "locust" for item in group_summaries)
            or get_boolean_from_string(
                os.environ.get("FECFILE_PROFILE_WITH_LOCUST", "False")
            ),
            "silky_analyze_queries": getattr(settings, "SILKY_ANALYZE_QUERIES", False),
            "locust_sample_pct": os.environ.get("FECFILE_LOCUST_SILK_SAMPLE_PCT", "2.0"),
        }

        index_html = _render_index_html(run_meta, group_summaries)
        _write_text(outdir / safe_run_id / "index.html", index_html)

        self.log(
            f"Wrote Silk profiling export to {outdir / safe_run_id}", Levels.SUCCESS
        )
