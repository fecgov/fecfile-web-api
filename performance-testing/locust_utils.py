def get_first_individual_receipt_for_report(self, report_id):
    params = {
        "page": 1,
        "ordering": "-created",
        "schedules": "A",
        "report_id": report_id,
    }
    response = self.client_get(
        "/api/v1/transactions/",
        name="get_transactions",
        timeout=TIMEOUT,
        params=params,
    )
    if response and response.status_code == 200:
        results = response.json().get("results", [])
        for transaction in results:
            if transaction["transaction_type_identifier"] == "INDIVIDUAL_RECEIPT":
                return transaction
    return None
