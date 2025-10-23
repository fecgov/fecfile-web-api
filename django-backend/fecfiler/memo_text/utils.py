from fecfiler.memo_text.models import MemoText
from fecfiler.transactions.models import Transaction


def copy_memo_between_records(original_record, new_record):
    original_memo = original_record.memo_text
    new_memo = new_record.memo_text

    if original_memo is None:
        raise ValueError("Original record's memo is None")

    memo_values = {
        "committee_account": original_memo.committee_account,
        "rec_type": original_memo.rec_type,
        "is_report_level_memo": original_memo.is_report_level_memo,
        "text4000": original_memo.text4000,
        "text_prefix": original_memo.text_prefix,
        "transaction_uuid": (
            new_record.id if isinstance(new_record, Transaction) else None
        )
    }

    if new_memo is None:
        new_memo = MemoText(**memo_values)
        new_record.memo_text = new_memo
        new_memo.save()
    else:
        for key in memo_values.keys():
            setattr(new_memo, key, memo_values[key])
            new_memo.save()
