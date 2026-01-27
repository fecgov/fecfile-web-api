from django.db.models import Case, When, Value, F, CharField
from fecfiler.reports.models import Report

report_code_label_mapping = {
    "Q1": "APRIL 15 QUARTERLY (Q1)",
    "Q2": "JULY 15 QUARTERLY (Q2)",
    "Q3": "OCTOBER 15 QUARTERLY (Q3)",
    "YE": "JANUARY 31 YEAR-END (YE)",
    "TER": "TERMINATION (TER)",
    "MY": "JULY 31 MID-YEAR (MY)",
    "12G": "12-DAY PRE-GENERAL (12G)",
    "12P": "12-DAY PRE-PRIMARY (12P)",
    "12R": "12-DAY PRE-RUNOFF (12R)",
    "12S": "12-DAY PRE-SPECIAL (12S)",
    "12C": "12-DAY PRE-CONVENTION (12C)",
    "30G": "30-DAY POST-GENERAL (30G)",
    "30R": "30-DAY POST-RUNOFF (30R)",
    "30S": "30-DAY POST-SPECIAL (30S)",
    "M2": "FEBRUARY 20 MONTHLY (M2)",
    "M3": "MARCH 20 MONTHLY (M3)",
    "M4": "APRIL 20 MONTHLY (M4)",
    "M5": "MAY 20 MONTHLY (M5)",
    "M6": "JUNE 20 MONTHLY (M6)",
    "M7": "JULY 20 MONTHLY (M7)",
    "M8": "AUGUST 20 MONTHLY (M8)",
    "M9": "SEPTEMBER 20 MONTHLY (M9)",
    "M10": "OCTOBER 20 MONTHLY (M10)",
    "M11": "NOVEMBER 20 MONTHLY (M11)",
    "M12": "DECEMBER 20 MONTHLY (M12)",
}

text_code_mapping = {
    "MST": "Miscellaneous Report to the FEC",
    "MSM": "Filing Frequency Change Notice",
    "MSW": "Loan Agreement / Loan Forgiveness",
    "MSI": "Disavowal Response",
    "MSR": "Form 3L Filing Frequency Change Notice",
}

# Generate the Case object
report_code_label_case = Case(
    *[When(report_code=k, then=Value(v)) for k, v in report_code_label_mapping.items()],
    When(
        form_24__isnull=False,
        then=F("form_24__name"),
    ),
    When(
        form_99__isnull=False,
        then=Case(
            *[
                When(form_99__text_code=code, then=Value(label))
                for code, label in text_code_mapping.items()
            ],
            default=Value("Miscellaneous Report to the FEC"),
            output_field=CharField(),
        ),
    ),
    When(form_1m__isnull=False, then=Value("NOTIFICATION OF MULTICANDIDATE STATUS")),
    output_field=CharField(),
)


def get_report_code_label(report: Report):
    if report.form_3x or report.form_3:
        return report_code_label_mapping[report.report_code]
    if report.form_24:
        return f"{report.form_24.report_type_24_48} HOUR"
    return ""
