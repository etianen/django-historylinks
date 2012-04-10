from django.db import models
from django.test import TestCase

import historylinks
from historylinks.registration import RegistrationError


class HistoryLinkTestModel(models.Model):
    
    slug = models.SlugField(
        unique = True,
    )
    
    def get_absolute_url(self):
        return u"/{slug}/".format(pk=self.slug)


class RegistrationTest(TestCase):
    
    def testRegistration(self):
        # Register the model and test.
        historylinks.register(HistoryLinkTestModel)
        self.assertTrue(historylinks.is_registered(HistoryLinkTestModel))
        self.assertRaises(RegistrationError, lambda: historylinks.register(HistoryLinkTestModel))
        self.assertTrue(HistoryLinkTestModel in historylinks.get_registered_models())
        self.assertTrue(isinstance(historylinks.get_adapter(HistoryLinkTestModel), historylinks.HistoryLinkAdapter))
        # Unregister the model and text.
        historylinks.unregister(HistoryLinkTestModel)
        self.assertFalse(historylinks.is_registered(HistoryLinkTestModel))
        self.assertRaises(RegistrationError, lambda: historylinks.unregister(HistoryLinkTestModel))
        self.assertTrue(HistoryLinkTestModel not in historylinks.get_registered_models())
        self.assertRaises(RegistrationError, lambda: isinstance(historylinks.get_adapter(HistoryLinkTestModel)))