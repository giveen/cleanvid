class CaselessDictionary(dict):
    """Case-insensitive dictionary that preserves original key case for display."""
    
    def __init__(self, initval=None):
        super().__init__()
        if initval is not None:
            if isinstance(initval, dict):
                for key, value in initval.items():
                    self[key] = value
            elif isinstance(initval, list):
                for key, value in initval:
                    self[key] = value

    def __contains__(self, key):
        return super().__contains__(key.lower())

    def __getitem__(self, key):
        return super().__getitem__(key.lower())['val']

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), {'key': key, 'val': value})

    def get(self, key, default=None):
        try:
            return super().__getitem__(key.lower())['val']
        except KeyError:
            return default

    def items(self):
        for v in super().values():
            yield (v['key'], v['val'])

    def keys(self):
        for v in super().values():
            yield v['key']

    def values(self):
        for v in super().values():
            yield v['val']
            
    def printable(self, sep=', ', key=None):
        if key is None:
            key = self.keys
        try:
            return sep.join(key())
        except TypeError:
            ans = ''
            for v in key():
                ans += str(v)
                ans += sep
            return ans[:-len(sep)]
