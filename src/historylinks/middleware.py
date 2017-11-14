"""Middleware used by the history links service."""
from __future__ import unicode_literals

from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

from historylinks.registration import history_link_context_manager, default_history_link_manager


HISTORYLINK_MIDDLEWARE_FLAG = "historylinks.history_link_fallback_middleware_active"


class HistoryLinkFallbackMiddleware(MiddlewareMixin):

    """Middleware that attempts to rescue 404 responses with a redirect to it's new location."""

    def process_request(self, request):
        """Starts a new history link context."""
        request.META[(HISTORYLINK_MIDDLEWARE_FLAG, self)] = True
        history_link_context_manager.start()

    def _close_history_link_context(self, request):
        """Closes the history link context."""
        if request.META.get((HISTORYLINK_MIDDLEWARE_FLAG, self), False):
            del request.META[(HISTORYLINK_MIDDLEWARE_FLAG, self)]
            history_link_context_manager.end()

    def process_response(self, request, response):
        """Attempts to rescue 404 responses and closes the history link context."""
        # Close the history link context.
        self._close_history_link_context(request)
        # Attempt to rescue a 404 error.
        if response.status_code == 404:
            redirect_url = default_history_link_manager.get_current_url(request.path)
            if redirect_url and redirect_url != request.path:
                response = redirect(redirect_url, permanent=True)
                add_never_cache_headers(response)
                return response
        # Return the original response.
        return response

    def process_exception(self, request, exception):
        """Closes the history link context."""
        history_link_context_manager.invalidate()
        self._close_history_link_context(request)
