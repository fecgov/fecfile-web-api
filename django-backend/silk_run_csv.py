#!/usr/bin/env python3
import csv
import json
import os
import sys

def _usage() -> int:
    print("Usage: python silk_run_csv.py <silkRunId> [--limit N]", file=sys.stderr)
    return 2


def _parse_args():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        sys.exit(_usage())
    run_id = sys.argv[1]
    limit = None
    if len(sys.argv) > 2:
        if len(sys.argv) == 4 and sys.argv[2] == "--limit":
            try:
                limit = int(sys.argv[3])
            except ValueError:
                sys.exit(_usage())
        elif len(sys.argv) == 3 and sys.argv[2].startswith("--limit="):
            try:
                limit = int(sys.argv[2].split("=", 1)[1])
            except ValueError:
                sys.exit(_usage())
        else:
            sys.exit(_usage())
    return run_id, limit


def _debug_enabled() -> bool:
    return str(os.environ.get("SILK_RUN_CSV_DEBUG", "")).lower() in {"1", "true", "yes", "on"}


def _debug(message: str) -> None:
    if _debug_enabled():
        print(message, file=sys.stderr)


def _fmt_dt(value):
    if not value:
        return ""
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def _get_sql_count(req):
    rel = getattr(req, "sql_queries", None)
    if rel is None:
        return ""
    try:
        return rel.count()
    except Exception:
        return ""


def _pick_meta_field(field_names):
    for candidate in ("meta", "headers", "request_headers", "request_header", "meta_data"):
        if candidate in field_names:
            return candidate
    for name in field_names:
        if "header" in name or "meta" in name:
            return name
    return None


def _filter_by_meta_field(qs, Request, meta_field, run_id):
    from django.core.exceptions import FieldError  # noqa: WPS433

    try:
        field = Request._meta.get_field(meta_field)
        if field.get_internal_type() == "JSONField":
            qs = qs.filter(**{f"{meta_field}__contains": {"HTTP_X_TEST_RUN_ID": run_id}})
        else:
            qs = qs.filter(**{f"{meta_field}__icontains": run_id})
        return qs
    except (FieldError, TypeError, ValueError):
        pass

    def _meta_contains(req):
        meta_value = getattr(req, meta_field, "")
        if meta_value is None:
            return False
        if isinstance(meta_value, (dict, list)):
            try:
                return run_id in json.dumps(meta_value)
            except Exception:
                return run_id in str(meta_value)
        return run_id in str(meta_value)

    return [req for req in qs if _meta_contains(req)]


def _find_header_related_model(Request):
    for rel in Request._meta.related_objects:
        model = rel.related_model
        table_name = getattr(model._meta, "db_table", "").lower()
        if "header" not in table_name:
            continue
        field_names = {field.name for field in model._meta.get_fields()}
        name_field = None
        value_field = None
        for candidate in ("name", "header", "key"):
            if candidate in field_names:
                name_field = candidate
                break
        for candidate in ("value", "val"):
            if candidate in field_names:
                value_field = candidate
                break
        if name_field and value_field:
            return model, rel.field.name, name_field, value_field
    return None


def _filter_by_related_headers(Request, run_id):
    from django.db.models import Q  # noqa: WPS433

    header_info = _find_header_related_model(Request)
    if not header_info:
        return None

    model, request_fk_name, name_field, value_field = header_info
    _debug(
        "Using header model "
        + model._meta.db_table
        + f" (name={name_field}, value={value_field}, fk={request_fk_name})"
    )
    name_match = Q(**{f"{name_field}__iexact": "x-test-run-id"}) | Q(
        **{f"{name_field}__iexact": "HTTP_X_TEST_RUN_ID"}
    )
    header_qs = model.objects.filter(name_match, **{value_field: run_id})
    request_ids = list(header_qs.values_list(request_fk_name, flat=True).distinct())
    if not request_ids:
        return None
    return Request.objects.filter(pk__in=request_ids)


def _filter_by_text_fields(Request, run_id):
    from django.db.models import Q  # noqa: WPS433

    text_fields = []
    for field in Request._meta.fields:
        if field.get_internal_type() in {"TextField", "CharField", "JSONField"}:
            text_fields.append(field)
    if not text_fields:
        return None

    qs = Request.objects.all()
    filters = Q()
    for field in text_fields:
        if field.get_internal_type() == "JSONField":
            filters |= Q(**{f"{field.name}__contains": {"HTTP_X_TEST_RUN_ID": run_id}})
            filters |= Q(**{f"{field.name}__contains": {"X-Test-Run-Id": run_id}})
        else:
            filters |= Q(**{f"{field.name}__icontains": run_id})
    try:
        return qs.filter(filters)
    except Exception:
        pass

    def _field_contains(req):
        for field in text_fields:
            value = getattr(req, field.name, None)
            if value is None:
                continue
            if isinstance(value, (dict, list)):
                try:
                    if run_id in json.dumps(value):
                        return True
                except Exception:
                    if run_id in str(value):
                        return True
            elif run_id in str(value):
                return True
        return False

    return [req for req in qs if _field_contains(req)]


def main() -> int:
    run_id, limit = _parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fecfiler.settings")
    try:
        import django  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        print(f"Django import failed: {exc}", file=sys.stderr)
        return 2

    django.setup()

    from django.conf import settings  # noqa: WPS433
    try:
        from silk.models import Request  # noqa: WPS433
    except Exception as exc:  # pragma: no cover
        print(f"Silk import failed: {exc}", file=sys.stderr)
        return 2

    if "silk" not in settings.INSTALLED_APPS:
        print("Silk is not enabled. Run with INCLUDE_SILK=True.", file=sys.stderr)
        return 2

    field_names = {field.name for field in Request._meta.get_fields()}
    meta_field = _pick_meta_field(field_names)
    _debug("Request fields: " + ", ".join(sorted(field_names)))

    qs = None
    if meta_field:
        _debug(f"Filtering via Request field: {meta_field}")
        qs = _filter_by_meta_field(Request.objects.all(), Request, meta_field, run_id)
    if qs is None:
        qs = _filter_by_related_headers(Request, run_id)
    if qs is None:
        qs = _filter_by_text_fields(Request, run_id)
    if qs is None:
        print(
            "Could not find header storage to filter by run id. "
            "Re-run with SILK_RUN_CSV_DEBUG=1 for diagnostics.",
            file=sys.stderr,
        )
        return 2

    if hasattr(qs, "order_by"):
        qs = qs.order_by("start_time")

    if limit is not None:
        if hasattr(qs, "__iter__") and not hasattr(qs, "__len__"):
            qs = list(qs)
        qs = qs[:limit]

    writer = csv.writer(sys.stdout)
    writer.writerow(
        [
            "run_id",
            "request_id",
            "method",
            "path",
            "status_code",
            "time_taken",
            "start_time",
            "end_time",
            "view_name",
            "view_method",
            "sql_count",
        ]
    )
    for req in qs:
        writer.writerow(
            [
                run_id,
                getattr(req, "id", ""),
                getattr(req, "method", ""),
                getattr(req, "path", ""),
                getattr(req, "status_code", ""),
                getattr(req, "time_taken", ""),
                _fmt_dt(getattr(req, "start_time", None)),
                _fmt_dt(getattr(req, "end_time", None)),
                getattr(req, "view_name", ""),
                getattr(req, "view_method", ""),
                _get_sql_count(req),
            ]
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
