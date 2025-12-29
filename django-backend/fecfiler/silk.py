def should_silk_record(request):
    if not request.path.startswith("/api/"):
        return False
    if request.path.startswith("/api/v1/reports/e2e-delete-all-reports"):
        return False
    return request.headers.get("x-silk-profile") == "1"
