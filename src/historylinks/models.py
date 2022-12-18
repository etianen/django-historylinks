"""Models used by django-historylinks."""
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models


class HistoryLink(models.Model):

    """A link to a moved / deleted model."""

    permalink_name = models.CharField(
        max_length=255,
    )

    permalink = models.CharField(
        max_length=255,
        unique=True,
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.TextField()

    object = GenericForeignKey()

    def __str__(self):
        """Returns a unicode representation."""
        return self.permalink

    class Meta:
        app_label = "historylinks"
