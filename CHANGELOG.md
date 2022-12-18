django-historylinks changelog
=============================

1.1.2 - 18/12/2022
------------------

* Django 3.2 compatibility (@lewiscollard).


1.1.1 - 14/11/2017
------------------

* Django 1.11 compatibility (@etianen).


1.1.0 - 14/12/2015
------------------

* Added Django 1.9 compatibility (@etianen).
* **Breaking:** Updated the location of [registration](https://github.com/etianen/django-historylinks/wiki/Registering-models) methods.
    Prior to this change, you could access the these methjods using the following import:

    ```py
    # Old-style import for accessing the registration methods.
    import historylinks

    # Use register methods from the historylinks namespace.
    historylinks.register(YourModel)
    ```

    In order to support Django 1.9, the registration
    methods have been moved to the following import:

    ```py
    # New-style import for accesssing the registration methods.
    from historylinks import shortcuts as historylinks

    # Use register methods from the historylinks namespace.
    historylinks.register(YourModel)
    ```


1.0.6 - 06/08/2015
------------------

* Added Django 1.8 compatibility (@etianen).


1.0.5 - 05/06/2015
------------------

* Added Python 3 compatibility (@danielsamuels).


1.0.4 - 15/04/2015
------------------

* Added Django 1.7 migrations (@jamesfoley).


1.0.3 - 05/02/2014
------------------

* historylinks not updated on fixture loading, fixing issues with multi-table inheritance.


1.0.2 - 31/01/2013
------------------

* Bugfix release - fixing an issue that prevented the HistoryLinkFallbackMiddleware from returning a redirect response.


1.0.1 - 28/01/2013
------------------

* Setting historylinks to never cache, to prevent infinite redirect loops.


1.0.0 - 24/07/2012
------------------

* First production release.
