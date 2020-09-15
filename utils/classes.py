def subclasses(cls):
    children = set(cls.__subclasses__())
    return children | set(grandchildren for child in children for grandchildren in subclasses(child))
