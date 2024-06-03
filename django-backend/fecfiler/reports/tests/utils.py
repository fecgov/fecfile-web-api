from django.db.models import Model
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_99.models import Form99


def create_form3x(committee, coverage_from, coverage_through, data={}):
    return create_test_report(Form3X, committee, coverage_from, coverage_through, data)


def create_form24(committee, data={}):
    return create_test_report(Form24, committee, data=data)

def create_form99(committee, data={}):
    return create_test_report(Form99, committee, data=data)

def create_form1m(committee, data={}):
    return create_test_report(Form1M, committee, data=data)


def create_test_report(
    form, committee, coverage_from=None, coverage_through=None, data={}
):
    form_object = create_form(form, data)
    report = Report.objects.create(
        committee_account=committee,
        coverage_from_date=coverage_from,
        coverage_through_date=coverage_through,
        **{FORM_CLASS_TO_FIELD[form]: form_object},
    )
    return report


def create_form(form: Model, data):
    return form.objects.create(**data)


FORM_CLASS_TO_FIELD = {
    Form3X: "form_3x",
    Form1M: "form_1m",
    Form24: "form_24",
    Form99: "form_99",
}
