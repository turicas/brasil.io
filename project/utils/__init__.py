def int_or_None(value):
    """
    >>> print(int_or_None(""))
    None
    >>> print(int_or_None("   "))
    None
    >>> print(int_or_None(0))
    0
    >>> type(int_or_None(0)) == type(0)
    True
    >>> type(int_or_None("0")) == type(0)
    True
    >>> print((int_or_None("123"), type(int_or_None("123")) == type(123)))
    (123, True)
    """
    if value is None or isinstance(value, int):
        return value
    value = str(value or "").strip()
    if value == "":
        return None
    return int(value)
