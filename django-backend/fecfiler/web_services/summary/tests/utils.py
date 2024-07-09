from fecfiler.transactions.tests.utils import (
    create_ie,
    create_schedule_b,
    create_schedule_a,
    create_loan,
    create_debt,
)
from fecfiler.reports.tests.utils import create_form3x
from datetime import datetime
from fecfiler.contacts.models import Contact

sc10 = "SC/10"


def generate_data(committee, contact, f3x, schedules):
    debt = None
    other_f3x = create_form3x(
        committee,
        datetime.strptime("2007-01-30", "%Y-%m-%d").date(),
        datetime.strptime("2007-02-28", "%Y-%m-%d").date(),
        {"L6a_cash_on_hand_jan_1_ytd": 61},
    )
    if "a" in schedules:
        sch_a_transactions = [
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-02-08",
                "amount": "3.77",
                "group": "GENERAL",
                "form_type": "SA11AII",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "444.44",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "555.55",
                "group": "OTHER",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1212.12",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1313.13",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1414.14",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "1234.56",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "891.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "10000.23",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "OFFSET_TO_OPEX",
                "memo": True,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "16",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "200.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "-1",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2005-02-01",
                "amount": "800.50",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
        ]
        debt_a = gen_schedule_a(sch_a_transactions, f3x, committee, contact)

        sch_a_transactions = [
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": False,
            },
            {
                "date": "2022-03-01",
                "amount": "8.23",
                "group": "GENERAL",
                "form_type": "SA11AI",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11B",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA11C",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "PARTY_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA12",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA13",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA14",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA15",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-05-01",
                "amount": "1000.00",
                "group": "GENERAL",
                "form_type": "SA16",
                "tti": "REFUND_TO_FEDERAL_CANDIDATE",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "300.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-01-01",
                "amount": "100",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": False,
                "itemized": True,
            },
            {
                "date": "2005-03-01",
                "amount": "500.00",
                "group": "GENERAL",
                "form_type": "SA17",
                "tti": "INDIVIDUAL_RECEIPT",
                "memo": True,
                "itemized": True,
            },
        ]
        debt_b = gen_schedule_a(sch_a_transactions, other_f3x, committee, contact)
        debt = debt_b or debt_a

    if "b" in schedules:
        sch_b_transactions = [
            {
                "amount": 150,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 22,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 14,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 44,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 31,
                "date": "2005-02-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 101.50,
                "date": "2005-02-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 201.50,
                "date": "2005-02-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 301.50,
                "date": "2005-02-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 201.50,
                "date": "2005-02-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 102.25,
                "date": "2005-02-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
        ]
        gen_schedule_b(sch_b_transactions, f3x, committee, contact)
        sch_b_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB21B",
            },
            {
                "amount": 100,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB22",
            },
            {
                "amount": 50,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB23",
            },
            {
                "amount": 17,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 1000,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB26",
            },
            {
                "amount": 10,
                "date": "2005-01-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 100,
                "date": "2005-05-01",
                "type": "TRANSFER_TO_AFFILIATES",
                "group": "GENERAL",
                "form_type": "SB27",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_INDIVIDUAL_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28A",
            },
            {
                "amount": 2000.00,
                "date": "2005-01-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_PARTY_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28B",
            },
            {
                "amount": 3000.00,
                "date": "2005-01-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "REFUND_PAC_CONTRIBUTION",
                "group": "GENERAL",
                "form_type": "SB28C",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "OTHER_DISBURSEMENT",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 500,
                "date": "2005-03-01",
                "type": "OTHER_DISBURSEMENT",
                "group": "GENERAL",
                "form_type": "SB29",
            },
            {
                "amount": 600.00,
                "date": "2005-03-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
            {
                "amount": 1000.00,
                "date": "2005-01-01",
                "type": "FEDERAL_ELECTION_ACTIVITY_100PCT_PAYMENT",
                "group": "GENERAL",
                "form_type": "SB30B",
            },
        ]
        gen_schedule_b(sch_b_transactions, other_f3x, committee, contact)

    if "c" in schedules:
        sch_c_transactions = [
            {
                "amount": 150,
                "date": "2005-02-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 30,
                "date": "2005-02-01",
                "percent": "2.0",
                "form_type": sc10,
            },
        ]
        gen_schedule_c(sch_c_transactions, f3x, committee, contact)
        sch_c_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "percent": "2.0",
                "form_type": "SC/9",
            },
            {
                "amount": 100,
                "date": "2005-01-01",
                "percent": "2.0",
                "form_type": sc10,
            },
            {
                "amount": 100,
                "date": "2004-12-01",
                "percent": "2.0",
                "form_type": sc10,
            },
        ]
        gen_schedule_c(sch_c_transactions, other_f3x, committee, contact)

    if "d" in schedules:
        sch_d_transactions = [
            {
                "amount": 100,
                "date": "2005-02-01",
                "form_type": "SD9",
            },
            {
                "amount": 220,
                "date": "2005-02-01",
                "form_type": "SD10",
            },
        ]
        gen_schedule_d(sch_d_transactions, f3x, committee, contact)
        sch_d_transactions = [
            {
                "amount": 100,
                "date": "2005-01-01",
                "form_type": "SD9",
            },
            {
                "amount": 100,
                "date": "2004-01-01",
                "form_type": "SD9",
            },
            {
                "amount": 220,
                "date": "2005-02-01",
                "form_type": "SD10",
            },
            {
                "amount": 220,
                "date": "2009-02-01",
                "form_type": "SD10",
            },
        ]
        gen_schedule_d(sch_d_transactions, other_f3x, committee, contact)

    if "e" in schedules:
        candidate = Contact.objects.create(
            committee_account_id=committee.id,
            candidate_office="H",
            candidate_state="MD",
            candidate_district="99",
        )
        sch_e_transactions = [
            {
                "amount": 65,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 76,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 10,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": False,
            },
            {
                "amount": 57,
                "disbursement_date": "2005-01-30",
                "dissemination_date": "2005-01-30",
                "memo_code": True,
            },
        ]
        gen_schedule_e(sch_e_transactions, f3x, committee, contact, candidate)
        sch_e_transactions = [
            {
                "amount": 145,
                "disbursement_date": "2005-01-01",
                "dissemination_date": "2005-01-01",
                "memo_code": False,
            },
            {
                "amount": 77,
                "disbursement_date": "1969-08-01",
                "dissemination_date": "1969-08-01",
                "memo_code": False,
            },
        ]

        gen_schedule_e(sch_e_transactions, other_f3x, committee, contact, candidate)
    return debt


def gen_schedule_a(transaction_data, f3x, committee, contact):
    debt = None
    for data in transaction_data:
        scha = create_schedule_a(
            data["tti"],
            committee,
            contact,
            data["date"],
            data["amount"],
            data["group"],
            data["form_type"],
            data["memo"],
            data["itemized"],
        )
        scha.reports.add(f3x)
        scha.save()
        if data["form_type"] == "SA11AII":
            debt = scha
    return debt


def gen_schedule_b(transaction_data, f3x, committee, contact):
    for data in transaction_data:
        schb = create_schedule_b(
            data["type"],
            committee,
            contact,
            data["date"],
            data["amount"],
            data["group"],
            data["form_type"],
        )

        schb.reports.add(f3x)
        schb.save()


def gen_schedule_c(transaction_data, f3x, committee, contact):
    for data in transaction_data:
        schc = create_loan(
            committee,
            contact,
            data["amount"],
            data["date"],
            data["percent"],
            False,
            "LOAN_RECEIVED_FROM_INDIVIDUAL",
            data["form_type"],
        )
        schc.reports.add(f3x)


def gen_schedule_d(transaction_data, f3x, committee, contact):
    for data in transaction_data:
        schd = create_debt(
            committee,
            contact,
            data["amount"],
            data["form_type"],
        )
        schd.reports.add(f3x)


def gen_schedule_e(transaction_data, f3x, committee, contact, candidate):
    for data in transaction_data:
        sche = create_ie(
            committee,
            contact,
            data["disbursement_date"],
            data["dissemination_date"],
            data["amount"],
            None,
            candidate,
            data["memo_code"],
        )
        sche.reports.add(f3x)
