from django.db.models import Model
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_99.models import Form99
from fecfiler.memo_text.models import MemoText


def create_form3x(
    committee,
    coverage_from,
    coverage_through,
    data={},
    report_code="Q1",
):
    return create_test_report(
        Form3X, "F3XN", committee, report_code, coverage_from, coverage_through, data
    )


def create_form24(committee, data={"name": "TEST"}):
    return create_test_report(Form24, "F24N", committee, data=data)


def create_form99(committee, data={}):
    return create_test_report(Form99, "F99", committee, data=data)


def create_form1m(committee, data={}):
    return create_test_report(Form1M, "F1MN", committee, data=data)


def create_test_report(
    form,
    form_type,
    committee,
    report_code=None,
    coverage_from=None,
    coverage_through=None,
    data=None,
):
    form_object = create_form(form, data)
    report = Report.objects.create(
        form_type=form_type,
        committee_account=committee,
        coverage_from_date=coverage_from,
        coverage_through_date=coverage_through,
        report_code=report_code,
        **{FORM_CLASS_TO_FIELD[form]: form_object},
    )
    return report


def create_form(form: Model, data):
    return form.objects.create(**data)


def create_report_memo(committee_account, report, text4000):
    return MemoText.objects.create(
        rec_type="TEXT",
        text4000=text4000,
        committee_account_id=committee_account.id,
        report_id=report.id,
    )


FORM_CLASS_TO_FIELD = {
    Form3X: "form_3x",
    Form1M: "form_1m",
    Form24: "form_24",
    Form99: "form_99",
}
