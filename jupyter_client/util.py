def inherit_docstring(cls):
    def decorator(func):
        doc = getattr(cls, func.__name__).__doc__
        func.__doc__ = doc
        return func
    return decorator
