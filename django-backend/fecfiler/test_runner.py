from django.test.runner import DiscoverRunner


class CustomTestRunner(DiscoverRunner):
    def __init__(self, *args, **kwargs):
        # Automatically exclude "performance" tagged tickets unless specifically invoked
        if (
            "tags" not in kwargs.keys()
            or kwargs["tags"] is None
            or "performance" not in kwargs["tags"]
        ):
            exclude = kwargs["exclude_tags"]
            if exclude is None:
                exclude = []
            exclude.append("performance")
            kwargs["exclude_tags"] = exclude

        super().__init__(*args, **kwargs)
