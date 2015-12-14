from historylinks.registration import HistoryLinkAdapter, history_link_context_manager, default_history_link_manager


# URL resolution.
get_current_url = default_history_link_manager.get_current_url


# Easy registration.
register = default_history_link_manager.register
unregister = default_history_link_manager.unregister
is_registered = default_history_link_manager.is_registered
get_registered_models = default_history_link_manager.get_registered_models
get_adapter = default_history_link_manager.get_adapter


# Easy context management.
update_history_links = history_link_context_manager.update_history_links
