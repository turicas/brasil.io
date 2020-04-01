def clean_value(value):
    if value == "false":
        return False
    if value == "true":
        return True
    return value

class DynamicModelFilterProcessor:
    def __init__(self, filtering: dict, allowed_filters: list):
        self.filtering = filtering
        self.allowed_filters = allowed_filters

    @property
    def filters(self):
        return {
            k: clean_value(self.filtering[k]) for k in self.filtering
            if k in self.allowed_filters and self.filtering[k] is not None
        }
