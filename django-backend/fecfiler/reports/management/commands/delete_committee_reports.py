from django.core.management.base import BaseCommand
from fecfiler.reports.views import delete_all_reports
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.contacts.models import Contact
import re


class Command(BaseCommand):
    help = "Delete all reports (and transactions) for a given committee"

    def add_arguments(self, parser):
        parser.add_argument("committee_id", nargs=1, type=str)
        parser.add_argument(
            "--delete-contacts",
            action="store_true",
            help="Also delete contacts associated with the committee",
        )

    def handle(self, *args, **options):
        committee_ids = options.get("committee_id", None)
        if committee_ids is None or len(committee_ids) == 0:
            self.stderr.write("Error: no committee id provided")
            return
        committee_id = committee_ids[0]

        cid_regex = re.compile("^C[0-9]{8}$")
        if not cid_regex.match(str(committee_id)):
            self.stderr.write(f'Error: invalid committee id "{committee_id}"')
            return

        committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
        if committee is None:
            self.stderr.write("Error: no matching committee")
            return

        self.delete_committee_reports(committee_id)

        # If delete-contacts flag is set, delete contacts as well
        if options["delete_contacts"]:
            self.stdout.write("Deleting contacts associated with the committee...")
            self.delete_committee_contacts(committee_id)

    def delete_committee_reports(self, committee_id):
        delete_all_reports(committee_id, log_method=self.stdout.write)

    def delete_committee_contacts(self, committee_id):
        Contact.objects.filter(committee_account__committee_id=committee_id).delete()
