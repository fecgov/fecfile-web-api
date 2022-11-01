from fecfiler.scha_transactions.models import SchATransaction

def get_from_sched_tables_by_uuid(uuid):
    tables = [SchATransaction]
    matches = []
    for table in tables:
        matches += list(table.objects.filter(id=uuid))

    if len(matches) > 1:
        raise LookupError
    if len(matches) == 1:
        return matches[0]
    return None
