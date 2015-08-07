from django.db import models


class HistoryLinkTestModel(models.Model):

    slug = models.SlugField(
        unique=True,
    )

    def get_absolute_url(self):
        return u"/{slug}/".format(slug=self.slug)
