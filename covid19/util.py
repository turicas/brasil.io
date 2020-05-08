def row_to_column(data):
    """
    Strategy used to save some space

    >>> row_to_column([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
    {'a': [1, 3], 'b': [2, 4]}
    """
    keys = None
    for row in data:
        if keys is None:
            keys = {key: [] for key in row.keys()}
        for key in row.keys():
            if key not in keys:
                raise ValueError(f"Key {repr(key)}")
            keys[key].append(row[key])
    return keys
