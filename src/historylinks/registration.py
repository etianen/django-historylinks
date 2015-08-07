"""Adapters for registering models with django-HistoryLinks."""
from __future__ import unicode_literals

import sys
from itertools import chain
from threading import local
from functools import wraps

from django.core.signals import request_finished
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.utils import six
from django.utils.encoding import force_text

from historylinks.models import HistoryLink


class HistoryLinkAdapterError(Exception):

    """Something went wrong with a history link adapter."""


class HistoryLinkAdapter(object):

    """An adapter for generating HistoryLinks for a model."""

    # Use to specify the methods that should be used to generate permalinks.
    permalink_methods = ()

    def __init__(self, model):
        """Initializes the history link adapter."""
        self.model = model

    def get_permalinks(self, obj):
        """Returns a dictionary of permalinks for the given obj."""
        permalink_methods = self.permalink_methods or ("get_absolute_url",)
        permalinks = {}
        for permalink_method_name in permalink_methods:
            # Resolve the method.
            try:
                permalink_method = getattr(obj, permalink_method_name)
            except AttributeError:
                raise HistoryLinkAdapterError("Could not find a method called {name!r} on {obj!r}".format(
                    name=permalink_method_name,
                    obj=obj,
                ))
            # Get the permalink.
            if not callable(permalink_method):
                raise HistoryLinkAdapterError("{model}.{method} is not a callable method".format(
                    model=self.model.__name__,
                    method=permalink_method_name,
                ))
            permalink = permalink_method()
            permalinks[permalink_method_name] = permalink
        # Return the resolved permalink.
        return permalinks


class RegistrationError(Exception):

    """Something went wrong when registering a model with a history link manager."""


class HistoryLinkContextError(Exception):

    """Something went wrong with the HistoryLink context management."""


def _bulk_save_history_links(history_links):
    """Creates the given history link data in the most efficient way possible."""
    if history_links:
        if hasattr(HistoryLink.objects, "bulk_create"):
            HistoryLink.objects.bulk_create(history_links)
        else:
            for history_link in history_links:
                history_link.save()


class HistoryLinkContextManager(local):

    """A thread-local context manager used to manage saving history link data."""

    def __init__(self):
        """Initializes the history link context."""
        self._stack = []
        # Connect to the signalling framework.
        request_finished.connect(self._request_finished_receiver)

    def is_active(self):
        """Checks that this history link context is active."""
        return bool(self._stack)

    def _assert_active(self):
        """Ensures that the history link is active."""
        if not self.is_active():
            raise HistoryLinkContextError("The history link context is not active.")

    def start(self):
        """Starts a level in the history link context."""
        self._stack.append((set(), False))

    def add_to_context(self, manager, obj):
        """Adds an object to the current context, if active."""
        self._assert_active()
        objects, _ = self._stack[-1]
        objects.add((manager, obj))

    def invalidate(self):
        """Marks this history link context as broken, so should not be commited."""
        self._assert_active()
        objects, _ = self._stack[-1]
        self._stack[-1] = (objects, True)

    def is_invalid(self):
        """Checks whether this history link context is invalid."""
        self._assert_active()
        _, is_invalid = self._stack[-1]
        return is_invalid

    def end(self):
        """Ends a level in the history link context."""
        self._assert_active()
        # Save all the models.
        tasks, is_invalid = self._stack.pop()
        if not is_invalid:
            _bulk_save_history_links(list(chain.from_iterable(manager._update_obj_history_links_iter(obj) for manager, obj in tasks)))

    # Context management.

    def update_history_links(self):
        """
        Marks up a block of code as requiring the history links to be updated.

        The returned context manager can also be used as a decorator.
        """
        return HistoryLinkContext(self)

    # Signalling hooks.

    def _request_finished_receiver(self, **kwargs):
        """
        Called at the end of a request, ensuring that any open contexts
        are closed. Not closing all active contexts can cause memory leaks
        and weird behaviour.
        """
        while self.is_active():
            self.end()


class HistoryLinkContext(object):

    """An individual context for a history link update."""

    def __init__(self, context_manager):
        """Initializes the history link context."""
        self._context_manager = context_manager

    def __enter__(self):
        """Enters a block of history link management."""
        self._context_manager.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """Leaves a block of history link management."""
        try:
            if exc_type is not None:
                self._context_manager.invalidate()
        finally:
            self._context_manager.end()

    def __call__(self, func):
        """Allows this history link context to be used as a decorator."""
        @wraps(func)
        def do_history_link_context(*args, **kwargs):
            self.__enter__()
            exception = False
            try:
                return func(*args, **kwargs)
            except:
                exception = True
                if not self.__exit__(*sys.exc_info()):
                    raise
            finally:
                if not exception:
                    self.__exit__(None, None, None)
        return do_history_link_context


# The shared, thread-safe history link context manager.
history_link_context_manager = HistoryLinkContextManager()


class HistoryLinkManager(object):

    """A history link manager."""

    def __init__(self, history_link_context_manager=history_link_context_manager):
        """Initializes the history link manager."""
        # Initialize the manager.
        self._registered_models = {}
        # Store the history link context.
        self._history_link_context_manager = history_link_context_manager

    def is_registered(self, model):
        """Checks whether the given model is registered with this history link manager."""
        return model in self._registered_models

    def register(self, model, adapter_cls=HistoryLinkAdapter, **field_overrides):
        """
        Registers the given model with this history link manager.

        If the given model is already registered with this history link manager, a
        RegistrationError will be raised.
        """
        # Check for existing registration.
        if self.is_registered(model):
            raise RegistrationError("{model!r} is already registered with this history link manager".format(
                model=model,
            ))
        # Perform any customization.
        if field_overrides:
            adapter_cls = type(model.__name__ + adapter_cls.__name__, (adapter_cls,), field_overrides)
        # Perform the registration.
        adapter_obj = adapter_cls(model)
        self._registered_models[model] = adapter_obj
        # Connect to the signalling framework.
        post_save.connect(self._post_save_receiver, model)
        # Return the model, allowing this to be used as a class decorator.
        return model

    def unregister(self, model):
        """
        Unregisters the given model with this history link manager.

        If the given model is not registered with this history link manager, a RegistrationError
        will be raised.
        """
        # Check for registration.
        if not self.is_registered(model):
            raise RegistrationError("{model!r} is not registered with this history link manager".format(
                model=model,
            ))
        # Perform the unregistration.
        del self._registered_models[model]
        # Disconnect from the signalling framework.
        post_save.disconnect(self._post_save_receiver, model)

    def get_registered_models(self):
        """Returns a sequence of models that have been registered with this history link manager."""
        return self._registered_models.keys()

    def get_adapter(self, model):
        """Returns the adapter associated with the given model."""
        if self.is_registered(model):
            return self._registered_models[model]
        raise RegistrationError("{model!r} is not registered with this history link manager".format(
            model=model,
        ))

    def _update_obj_history_links_iter(self, obj):
        """Either updates the given object's history links, or yields one or more unsaved history links."""
        model = obj.__class__
        adapter = self.get_adapter(model)
        content_type = ContentType.objects.get_for_model(model)
        object_id = force_text(obj.pk)
        # Create the history link data.
        for permalink_name, permalink_value in six.iteritems(adapter.get_permalinks(obj)):
            history_link_data = {
                "permalink": permalink_value,
                "permalink_name": permalink_name,
                "object_id": object_id,
                "content_type": content_type,
            }
            update_count = HistoryLink.objects.filter(
                permalink=permalink_value,
            ).update(**history_link_data)
            if update_count == 0:
                yield HistoryLink(**history_link_data)

    def update_obj_history_links(self, obj):
        """Updates the history links for the given obj."""
        _bulk_save_history_links(list(self._update_obj_history_links_iter(obj)))

    # Signalling hooks.

    def _post_save_receiver(self, instance, raw=False, **kwargs):
        """Signal handler for when a registered model has been saved."""
        if not raw:
            if self._history_link_context_manager.is_active():
                self._history_link_context_manager.add_to_context(self, instance)
            else:
                self.update_obj_history_links(instance)

    # Accessing current URLs.

    def get_current_url(self, path):
        """Returns the current URL for whatever used to exist at the given path."""
        # Get the history links.
        try:
            history_link = HistoryLink.objects.get(permalink=path)
        except HistoryLink.DoesNotExist:
            return None
        # Resolve the model.
        model = ContentType.objects.get_for_id(id=history_link.content_type_id).model_class()
        # Resolve the adapter.
        try:
            adapter = self.get_adapter(model)
        except RegistrationError:
            return None
        # Resolve the object.
        try:
            obj = model._default_manager.get(pk=history_link.object_id)
        except model.DoesNotExist:
            return None
        # Resolve the permalinks.
        permalinks = adapter.get_permalinks(obj)
        # Resolve the specific permalink.
        return permalinks.get(history_link.permalink_name, None)


# The default history link manager.
default_history_link_manager = HistoryLinkManager()
