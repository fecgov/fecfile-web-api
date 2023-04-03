from datetime import datetime
from uuid import UUID
from celery import shared_task

from fecfiler.transactions.schedule_a.models import ScheduleA


@shared_task
def update_future_transaction_contacts(
    contact_id: UUID,
    schedule_a_data: dict,
):
    contribution_date = datetime.fromisoformat(
        schedule_a_data.get('contribution_date')
    )
    attributes_to_update = [
        'contributor_organization_name',
        'contributor_last_name',
        'contributor_first_name',
        'contributor_middle_name',
        'contributor_prefix',
        'contributor_suffix',
        'contributor_street_1',
        'contributor_street_2',
        'contributor_city',
        'contributor_state',
        'contributor_zip',
        'contributor_employer',
        'contributor_occupation',
        'donor_committee_fec_id',
        'donor_committee_name',
    ]
    scha_transactions = ScheduleA.objects.filter(
        transaction__contact_id=contact_id,
        contribution_date__gte=contribution_date,
        transaction__report__upload_submission__isnull=True
    )
    for scha_transaction in scha_transactions:
        for attribute in attributes_to_update:
            setattr(
                scha_transaction, attribute,
                schedule_a_data.get(attribute)
            )
    ScheduleA.objects.bulk_update(scha_transactions, attributes_to_update, 50)
