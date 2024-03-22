import datetime
from django.core.management.base import BaseCommand
from fecfiler.authentication.models import Account
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA


class Command(BaseCommand):
    help = "Stuffs db with data to run tests on"

    # def add_arguments(self, parser):
    #     parser.add_argument("num_transactions", type=int)

    def handle(self, *args, **options):
        # create committee
        committee = CommitteeAccount.objects.create(committee_id="C12123434")
        # create user
        Account.objects.create(cmtee_id="C12123434")
        # create a report
        f3x = Form3X.objects.create()
        report = Report.objects.create(
            form_3x_id=f3x.id, committee_account_id=committee.id
        )

        contacts = Contact.objects.bulk_create(
            [
                Contact(type="IND", first_name=x, committee_account_id=committee.id)
                for x in range(25)
            ]
        )

        num_a = 10000
        schedule_as = ScheduleA.objects.bulk_create(
            [
                ScheduleA(
                    contributor_organization_name=i,
                    contribution_date=datetime.date(
                        datetime.date.today().year, (i % 12) + 1, day=(i % 28) + 1
                    ),
                    contribution_amount=1,
                )
                for i in range(num_a)
            ]
        )
        schedule_a_transactions = Transaction.objects.bulk_create(  # noqa: F841
            [
                Transaction(
                    schedule_a_id=schedule_as[i].id,
                    report_id=report.id,
                    contact_1=contacts[i % 25],
                )
                for i in range(num_a)
            ]
        )
