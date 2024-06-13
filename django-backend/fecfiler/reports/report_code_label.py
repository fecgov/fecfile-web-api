from django.db.models import Case, When, Value
from fecfiler.reports.models import Report

report_code_label_mapping = {
    "Q1": "APRIL 15 QUARTERLY REPORT (Q1)",
    "Q2": "JULY 15 QUARTERLY REPORT (Q2)",
    "Q3": "OCTOBER 15 QUARTERLY REPORT (Q3)",
    "YE": "JANUARY 31 YEAR-END (YE)",
    "TER": "TERMINATION REPORT (TER)",
    "MY": "JULY 31 MID-YEAR REPORT (MY)",
    "12G": "12-DAY PRE-GENERAL (12G)",
    "12P": "12-DAY PRE-PRIMARY (12P)",
    "12R": "12-DAY PRE-RUNOFF (12R)",
    "12S": "12-DAY PRE-SPECIAL (12S)",
    "12C": "12-DAY PRE-CONVENTION (12C)",
    "30G": "30-DAY POST-GENERAL (30G)",
    "30R": "30-DAY POST-RUNOFF (30R)",
    "30S": "30-DAY POST-SPECIAL (30S)",
    "M2": "FEBRUARY 20 MONTHLY REPORT (M2)",
    "M3": "MARCH 20 MONTHLY REPORT (M3)",
    "M4": "APRIL 20 MONTHLY REPORT (M4)",
    "M5": "MAY 20 MONTHLY REPORT (M5)",
    "M6": "JUNE 20 MONTHLY REPORT (M6)",
    "M7": "JULY 20 MONTHLY REPORT (M7)",
    "M8": "AUGUST 20 MONTHLY REPORT (M8)",
    "M9": "SEPTEMBER 20 MONTHLY REPORT (M9)",
    "M10": "OCTOBER 20 MONTHLY REPORT (M10)",
    "M11": "NOVEMBER 20 MONTHLY REPORT (M11)",
    "M12": "DECEMBER 20 MONTHLY REPORT (M12)",
}

# Generate the Case object
report_code_label_case = Case(
    *[When(report_code=k, then=Value(v)) for k, v in report_code_label_mapping.items()],
    When(form_24__report_type_24_48=24, then=Value("24 HOUR")),
    When(form_24__report_type_24_48=48, then=Value("48 HOUR")),
    When(form_99__isnull=False, then=Value("")),
    When(form_1m__isnull=False, then=Value("")),
)


def get_report_code_label(report: Report):
    if report.form_3x:
        return report_code_label_mapping[report.report_code]
    if report.form_24:
        return f"{report.form_24.report_type_24_48} HOUR"
    return ""
