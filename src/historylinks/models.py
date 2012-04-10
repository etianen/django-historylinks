"""Models used by django-historylinks."""

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey
from django.db import models


class HistoryLink(models.Model):
    
    """A link to a moved / deleted model."""
    
    permalink_method = models.CharField(
        max_length = 255,
    )
    
    permalink = models.CharField(
        max_length = 255,
        unique = True,
    )
    
    content_type = models.ForeignKey(ContentType)
    
    object_id = models.TextField()
    
    object = GenericForeignKey()
    
    def __unicode__(self):
        """Returns a unicode representation."""
        return self.permalink