class NavableKwargMapping(object):
    def __init__(self, to_name, conversion=None):
        if conversion is None:
            conversion = lambda value : value
        self.to_name = to_name
        self.conversion = conversion

    def convert(self, value):
        try:
            return self.conversion(value)
        except Exception:
            return value


class NavableView(object):
    def __init__(self, name, description, kwarg_mappings=None):
        if kwarg_mappings is None:
            kwarg_mappings = {}
        else:
            kwarg_mappings = kwarg_mappings.copy()
        self.name = name
        self.description = description
        self.kwarg_mappings = kwarg_mappings

    def map_kwargs(self, kwargs):
        result = {}
        for name, mapping in self.kwarg_mappings.iteritems():
            if kwargs.has_key(name):
                result[mapping.to_name] = mapping.convert(kwargs[name])
        return result


class NavableRegistry(object):

    # view -> NavableView
    _registrations = {}

    def __iter__(self):
        for view in self._registrations.values():
            yield view

    def __len__(self):
        return len(self._registrations)

    def __getitem__(self, key):
        return self._registrations[key]

    def register(self, name, description, kwarg_mappings=None):
        view = NavableView(name, description, kwarg_mappings=kwarg_mappings)
        self._registrations[name] = view

def kwarg(to_name, conversion=None):
    return NavableKwargMapping(to_name, conversion)


registry = NavableRegistry()
