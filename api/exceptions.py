class ApiEndpointFromOldVersionException(Exception):
    def __init__(self, url):
        self.url = url
