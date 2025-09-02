TRANSACTION_MANAGER_PROFILING = [
    {
        "module": "fecfiler.transactions.managers",
        "function": "TransactionManager.transaction_view",
    },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.SCHEDULE_CLAUSE",
    # },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.INCURRED_PRIOR_CLAUSE",
    # },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.PAYMENT_PRIOR_CLAUSE",
    # },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.PAYMENT_AMOUNT_CLAUSE",
    # },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.transaction_view",
    # },
    # {
    #     "module": "fecfiler.transactions.managers",
    #     "function": "TransactionManager.ORDER_KEY_CLAUSE",
    # },
]

TRANSACTION_VIEW_PROFILING = [
    {
        "module": "fecfiler.transactions.views",
        "function": "TransactionViewSet.get_previous",
    }
]

TRANSACTION_UTILS_PROFILING = [
    {
        "module": "fecfiler.transactions.utils",
        "function": "filter_queryset_for_previous_transactions_in_aggregation",
    }
]
