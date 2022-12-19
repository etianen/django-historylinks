from io import StringIO

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from historylinks import shortcuts as historylinks
from historylinks.models import HistoryLink
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

    def testRaisesException(self):
        # Ensure coverage of handle_exception in the middleware.
        with self.assertRaises(AssertionError) as e:
            self.client.get(reverse('raise_exception'))
        self.assertEqual(str(e.exception), 'historylinks test')

    def testRedirectsToNewURL(self):
        # Try a redirect.
        response = self.client.get("/foo/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/bar/")
        # Try a 404.
        response = self.client.get("/baz/")
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        historylinks.unregister(HistoryLinkTestModel)


class HistoryLinkManagementTestCase(TestCase):
    def test_buildhistorylinks(self):
        obj = HistoryLinkTestModel.objects.create(slug="foo")

        def assert_historylink_is_sane():
            self.assertEqual(HistoryLink.objects.all().count(), 1)
            history_link = HistoryLink.objects.get()
            self.assertEqual(history_link.content_type, ContentType.objects.get_for_model(HistoryLinkTestModel))
            self.assertEqual(history_link.object, obj)
            self.assertEqual(history_link.object_id, str(obj.id))
            self.assertEqual(history_link.permalink, "/foo/")

        historylinks.register(HistoryLinkTestModel)
        # sanity check
        self.assertEqual(HistoryLink.objects.all().count(), 0)

        stdout = StringIO()
        call_command("buildhistorylinks", stdout=stdout)
        assert_historylink_is_sane()
        self.assertEqual(stdout.getvalue(), "Refreshed 1 history links.\n")

        # Ensure the various branches for --verbosity=X are covered.
        stdout = StringIO()
        call_command("buildhistorylinks", stdout=stdout, verbosity=2)
        assert_historylink_is_sane()
        self.assertEqual(stdout.getvalue(), "Refreshed 1 history link(s) for history link test model.\n")

        stdout = StringIO()
        call_command("buildhistorylinks", stdout=stdout, verbosity=3)
        assert_historylink_is_sane()
        self.assertEqual(stdout.getvalue(), f"Refreshed history link for HistoryLinkTestModel object ({obj.pk}).\n")

    def tearDown(self):
        historylinks.unregister(HistoryLinkTestModel)
