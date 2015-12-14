from django.test import TestCase

from historylinks import shortcuts as historylinks
from historylinks.registration import RegistrationError
from test_historylinks.models import HistoryLinkTestModel


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


class HistoryLinkRedirectTest(TestCase):

    def setUp(self):
        historylinks.register(HistoryLinkTestModel)
        self.obj = HistoryLinkTestModel.objects.create(slug="foo")
        self.obj.slug = "bar"
        self.obj.save()

    def testRedirectsToNewURL(self):
        # Try a redirect.
        response = self.client.get("/foo/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "http://testserver/bar/")
        # Try a 404.
        response = self.client.get("/baz/")
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        historylinks.unregister(HistoryLinkTestModel)
