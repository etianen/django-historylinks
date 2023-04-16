def raise_exception(request):
    # Regression test: make sure getting HTTP headers does not throw an
    # exception.
    request.headers.get('dontfail')
    raise AssertionError('historylinks test')
