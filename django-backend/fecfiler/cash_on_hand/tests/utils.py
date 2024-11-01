from ..models import CashOnHandYearly


def create_cash_on_hand_yearly(committee_account, year, cash_on_hand):
    return CashOnHandYearly.objects.create(
        committee_account=committee_account, year=year, cash_on_hand=cash_on_hand
    )
