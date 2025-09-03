from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from fecfiler.s3 import S3_SESSION
from fecfiler.settings import AWS_STORAGE_BUCKET_NAME, MOCK_OPENFEC_REDIS_URL
import redis
import structlog
import json

# Committee Accounts and Users
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User

# Reports
from fecfiler.reports.models import Report, ReportTransaction
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_3.models import Form3
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_99.models import Form99

# Contacts
from fecfiler.contacts.models import Contact

# Transactions
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.transactions.schedule_f.models import ScheduleF

# Memos
from fecfiler.memo_text.models import MemoText

# Cash On Hand
from fecfiler.cash_on_hand.models import CashOnHandYearly

# Submissions
from fecfiler.web_services.models import DotFEC, UploadSubmission, WebPrintSubmission

# Faker bits
from faker import Faker
from faker.providers import person, phone_number

FORM_MODELS = [Form1M, Form24, Form3, Form3X, Form99]
SUBMISSION_MODELS = [UploadSubmission, WebPrintSubmission]
SCHEDULE_MODELS = [
    ScheduleA,
    ScheduleB,
    ScheduleC,
    ScheduleC1,
    ScheduleC2,
    ScheduleD,
    ScheduleE,
    ScheduleF,
]


logger = structlog.get_logger(__name__)
fake = Faker()
fake.add_provider(person)
fake.add_provider(phone_number)


class Command(BaseCommand):
    help = "Dump all data for a given committee into a valid JSON fixture"

    def add_arguments(self, parser):
        parser.add_argument(
            "committee_id", help="The ID (not UUID) for the target committee"
        )
        parser.add_argument("--redis", action="store_true")

    def serialize(self, queryset):
        return serializers.serialize("json", queryset)[1:-1]  # Strip square brackets

    def dump_model(self, Model, filter_args, order_by=None):
        queryset = Model.objects.filter(**filter_args)
        if order_by is not None:
            queryset.order_by(order_by)

        dumped_model = self.serialize(queryset)
        if len(dumped_model) > 0:
            return [dumped_model]
        else:
            return []

    def dump_model_list(self, model_list, filter_args, order_by=None):
        dumped_models = []
        for Model in model_list:
            dumped_models += self.dump_model(Model, filter_args, order_by)
        return dumped_models

    def dump_committee_and_users(self, committee):
        users = self.dump_model(User, {"committeeaccount": committee})

        if not users:
            return []

        # mask names and emails
        user_nodes = json.loads(f"[{users[0]}]")
        for user_obj in user_nodes:
            if "fields" in user_obj and "first_name" in user_obj["fields"]:
                user_obj["fields"]["first_name"] = fake.first_name()
            if "fields" in user_obj and "last_name" in user_obj["fields"]:
                user_obj["fields"]["last_name"] = fake.last_name()
            if "fields" in user_obj and "email" in user_obj["fields"]:
                user_obj["fields"]["email"] = fake.email()
        # users = [json.dumps(user_obj) for user_obj in user_nodes]

        dumped_data = self.dump_model(CommitteeAccount, {"id": committee.id})
        dumped_data += users
        dumped_data += self.dump_model(Membership, {"committee_account": committee})

        return dumped_data

    def dump_contacts(self, committee):
        contacts = self.dump_model(Contact, {"committee_account": committee})

        if not contacts:
            return []

        # mask telephone numbers
        contact_nodes = json.loads(f"[{contacts[0]}]")
        for contact_obj in contact_nodes:
            if "fields" in contact_obj and "telephone" in contact_obj["fields"]:
                contact_obj["fields"]["telephone"] = fake.phone_number()
        contacts = [json.dumps(contact_obj) for contact_obj in contact_nodes]

        return contacts

    def dump_reports(self, committee):
        dumped_data = self.dump_model_list(
            FORM_MODELS, {"report__committee_account": committee}
        )
        dumped_data += self.dump_model(Report, {"committee_account": committee})

        return dumped_data

    def dump_transactions(self, committee):
        dumped_data = self.dump_model_list(
            SCHEDULE_MODELS, {"transaction__committee_account": committee}
        )
        dumped_data += self.dump_model(
            Transaction,
            {"committee_account": committee},
            order_by="created",  # Ensure that parents are loaded before children
        )
        dumped_data += self.dump_model(
            ReportTransaction, {"transaction__committee_account": committee}
        )

        return dumped_data

    def dump_memos(self, committee):
        return self.dump_model(MemoText, {"committee_account": committee})

    def dump_cash_on_hand(self, committee):
        return self.dump_model(CashOnHandYearly, {"committee_account": committee})

    def dump_submissions(self, committee):
        dumped_data = self.dump_model(DotFEC, {"report__committee_account": committee})
        dumped_data += self.dump_model_list(
            SUBMISSION_MODELS, {"dot_fec__report__committee_account": committee}
        )
        return dumped_data

    def dump_all_committee_data(self, committee):
        dumplist = [
            *self.dump_committee_and_users(committee),
            *self.dump_contacts(committee),
            *self.dump_reports(committee),
            *self.dump_transactions(committee),
            *self.dump_memos(committee),
            *self.dump_cash_on_hand(committee),
            *self.dump_submissions(committee),
        ]
        """
        Records will be loaded in the same order that they're dumped,
        so the order in which they're dumped is load-bearing.
        """

        return dumplist

    def get_filename(self, options):
        return f"dumped_data_for_{options.get("committee_id")}.json"

    def save_to_s3(self, filename, formatted_json):
        try:
            logger.info(f"Uploading file to s3: {filename}")
            s3_object = S3_SESSION.Object(AWS_STORAGE_BUCKET_NAME, filename)
            s3_object.put(Body=formatted_json.encode("utf-8"))
            logger.info("Successfully uploaded file to s3")
        except Exception as E:
            raise CommandError(f"Failed to upload to s3: {str(E)}")

    def save_to_local(self, filename, formatted_json):
        logger.info(f"Saving committee data to local file: {filename}")

        file = open(filename, "w")
        file.write(formatted_json)
        file.close()

    def save_to_redis(self, filename, formatted_json):
        redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
        redis_instance.set(filename, formatted_json)

    def save_data(self, formatted_json, options):
        filename = self.get_filename(options)

        if options.get("redis", False):
            return self.save_to_redis(filename, formatted_json)
        elif S3_SESSION is not None:
            return self.save_to_s3(filename, formatted_json)
        else:
            return self.save_to_local(filename, formatted_json)

    def handle(self, *args, **options):
        committee_id = options.get("committee_id")
        committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
        if committee is None:
            raise CommandError("No Committee Account found matching that Committee ID")

        dumped_committee_data = self.dump_all_committee_data(committee)
        formatted_json = f"[{','.join(dumped_committee_data)}]"

        self.save_data(formatted_json, options)
