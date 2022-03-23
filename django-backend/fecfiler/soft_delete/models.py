from datetime import datetime
from django.db import models
from .managers import SoftDeleteManager


class SoftDeleteModel(models.Model):
    """Abstract SoftDeleteModel
    Inherit this model to add soft delete functionality to a model
    Implementation from
    https://adriennedomingus.com/blog/soft-deletion-in-django
    """

    deleted = models.DateTimeField(blank=True, null=True)
    # objects will only return results that have not been deleted
    objects = SoftDeleteManager()
    # all_objects will return results even if they have been deleted
    all_objects = SoftDeleteManager(include_deleted=True)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted = datetime.now()
        self.save()

    def hard_delete(self):
        super(SoftDeleteModel, self).delete()
