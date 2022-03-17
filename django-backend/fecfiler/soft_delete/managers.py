from datetime import datetime
from django.db import models

"""Manager to add soft delete functionality
implementation from https://adriennedomingus.com/blog/soft-deletion-in-django

This manager provides a delete function that only soft deletes (sets a
deleted field to `datetime.now()`) and a hard_delete function that truly
removes the record from the db

This manager uses a queryset that excludes soft-deleted records by default
passing in the argument 'include_deleted' uses a query set that returns all
records, but still provides soft and hard delete functions
"""


class SoftDeleteManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.include_deleted = kwargs.pop("include_deleted", False)
        super(SoftDeleteManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.include_deleted:
            return SoftDeleteQuerySet(self.model)
        else:
            return SoftDeleteQuerySet(self.model).get_alive()

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeleteQuerySet(models.QuerySet):
    """Soft Delete QuerySet to provide soft delete, hard delete, and
    deleted filter
    """

    def delete(self):
        return super(SoftDeleteQuerySet, self).update(deleted=datetime.now())

    def hard_delete(self):
        return super(SoftDeleteQuerySet, self).delete()

    def get_alive(self):
        return self.filter(deleted=None)
