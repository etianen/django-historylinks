from __future__ import unicode_literals

from django.core.management.base import NoArgsCommand
from django.db import transaction

from historylinks.registration import default_history_link_manager, _bulk_save_history_links


class Command(NoArgsCommand):

    help = "Builds the history links for all registered models."

    @transaction.atomic()
    def handle_noargs(self, **options):
        verbosity = int(options.get("verbosity", 1))
        link_count = 0
        # Create links.
        links_to_create = []
        for model in default_history_link_manager.get_registered_models():
            local_link_count = 0
            for obj in model._default_manager.all().iterator():
                local_link_count += 1
                links_to_create.extend(default_history_link_manager._update_obj_history_links_iter(obj))
                if verbosity == 3:
                    self.stdout.write("Refreshed history link for {obj}.\n".format(
                        obj=obj,
                    ))
            if verbosity == 2:
                self.stdout.write("Refreshed {local_link_count} history link(s) for {model}.\n".format(
                    local_link_count=local_link_count,
                    model=model._meta.verbose_name,
                ))
            link_count += local_link_count
        _bulk_save_history_links(links_to_create)
        if verbosity == 1:
            self.stdout.write("Refreshed {link_count} history links.\n".format(
                link_count=link_count,
            ))
