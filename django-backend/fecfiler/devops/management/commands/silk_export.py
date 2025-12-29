import json
import os
import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError


MAX_SLOW_REQUESTS = 20


def _parse_headers(encoded_headers):
    if not encoded_headers:
        return {}
    try:
        headers = json.loads(encoded_headers)
    except Exception:
        return {}
    if not isinstance(headers, dict):
        return {}
    return {str(key).lower(): value for key, value in headers.items()}


def _get_header_value(headers, name):
    value = headers.get(name)
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    return str(value)


def _sanitize_spec_name(spec_name):
    if not spec_name:
        return "unknown-spec"
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", str(spec_name).strip())
    sanitized = sanitized.strip("._-")
    return sanitized or "unknown-spec"


def _get_status_code(request_obj):
    status_code = getattr(request_obj, "status_code", None)
    if status_code is not None:
        return status_code
    try:
        response = request_obj.response
    except Exception:
        return None
    return getattr(response, "status_code", None)


def _get_num_sql_queries(request_obj):
    for attr in ("num_sql_queries", "num_queries", "num_db_queries"):
        if hasattr(request_obj, attr):
            value = getattr(request_obj, attr)
            if value is not None:
                return value
    return None


def _get_time_taken(request_obj):
    value = getattr(request_obj, "time_taken", None)
    if value is None:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0


class Command(BaseCommand):
    help = "Export Silk profiling summaries grouped by Cypress spec."

    def add_arguments(self, parser):
        parser.add_argument("--run-id", required=True, help="Silk run id to export.")
        parser.add_argument(
            "--spec",
            default=None,
            help="Optional spec name to export (sanitized).",
        )
        parser.add_argument(
            "--outdir",
            default="silk-artifacts",
            help="Output directory for artifacts.",
        )

    def handle(self, *args, **options):
        run_id = options["run_id"]
        spec_filter = options.get("spec")
        outdir = options["outdir"]

        try:
            from silk.models import Request
        except Exception as exc:
            raise CommandError("django-silk is not available in this environment.") from exc

        spec_filter = _sanitize_spec_name(spec_filter) if spec_filter else None
        run_dir = os.path.join(outdir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        requests_by_spec = defaultdict(list)
        spec_display_names = {}
        all_entries = []
        spec_summaries = []

        queryset = Request.objects.filter(path__startswith="/api/")

        for request_obj in queryset.iterator():
            headers = _parse_headers(request_obj.encoded_headers)
            if _get_header_value(headers, "x-silk-profile") != "1":
                continue
            if _get_header_value(headers, "x-silk-run-id") != run_id:
                continue

            raw_spec = _get_header_value(headers, "x-silk-spec") or "unknown-spec"
            safe_spec = _sanitize_spec_name(raw_spec)
            if spec_filter and safe_spec != spec_filter:
                continue

            spec_display_names.setdefault(safe_spec, raw_spec)

            entry = {
                "method": request_obj.method,
                "path": request_obj.path,
                "time_taken": _get_time_taken(request_obj),
            }
            status_code = _get_status_code(request_obj)
            if status_code is not None:
                entry["status_code"] = status_code
            num_sql_queries = _get_num_sql_queries(request_obj)
            if num_sql_queries is not None:
                entry["num_sql_queries"] = num_sql_queries
            test_name = _get_header_value(headers, "x-silk-test")
            if test_name:
                entry["x-silk-test"] = test_name

            requests_by_spec[safe_spec].append(entry)
            all_entries.append(entry)

        index_specs = []
        for safe_spec, entries in requests_by_spec.items():
            entries_sorted = sorted(
                entries, key=lambda item: item.get("time_taken", 0.0), reverse=True
            )
            total_time = sum(item.get("time_taken", 0.0) for item in entries)
            slowest_time = entries_sorted[0]["time_taken"] if entries_sorted else 0.0

            summary = {
                "run_id": run_id,
                "spec": spec_display_names.get(safe_spec, safe_spec),
                "spec_dir": safe_spec,
                "request_count": len(entries),
                "total_time": total_time,
                "slow_requests": entries_sorted[:MAX_SLOW_REQUESTS],
            }

            spec_dir = os.path.join(run_dir, safe_spec)
            os.makedirs(spec_dir, exist_ok=True)
            summary_path = os.path.join(spec_dir, "summary.json")
            with open(summary_path, "w", encoding="utf-8") as summary_file:
                json.dump(summary, summary_file, indent=2)

            spec_summaries.append(summary)
            index_specs.append(
                {
                    "spec": spec_display_names.get(safe_spec, safe_spec),
                    "spec_dir": safe_spec,
                    "request_count": len(entries),
                    "total_time": total_time,
                    "slowest_request_time": slowest_time,
                    "summary_path": os.path.relpath(summary_path, run_dir),
                }
            )

        exported_specs = len(index_specs)
        if spec_filter:
            if exported_specs == 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"No requests found for run {run_id} and spec {spec_filter}; "
                        "run summary left unchanged."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Exported {exported_specs} spec(s) to {os.path.abspath(run_dir)}"
                    )
                )
            return

        index_specs.sort(
            key=lambda item: (item["total_time"], item["slowest_request_time"]),
            reverse=True,
        )

        index_path = os.path.join(run_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as index_file:
            json.dump({"run_id": run_id, "specs": index_specs}, index_file, indent=2)

        all_entries_sorted = sorted(
            all_entries, key=lambda item: item.get("time_taken", 0.0), reverse=True
        )
        run_summary = {
            "run_id": run_id,
            "request_count": len(all_entries),
            "total_time": sum(item.get("time_taken", 0.0) for item in all_entries),
            "slow_requests": all_entries_sorted[:MAX_SLOW_REQUESTS],
            "specs": index_specs,
            "spec_summaries": spec_summaries,
        }
        summary_path = os.path.join(run_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as summary_file:
            json.dump(run_summary, summary_file, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {exported_specs} spec(s) to {os.path.abspath(run_dir)}"
            )
        )
