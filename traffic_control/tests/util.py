from django.test.client import Client


class TrafficControlClient(Client):
    def generic(self, *args, **kwargs):
        if "HTTP_USER_AGENT" not in kwargs:
            kwargs["HTTP_USER_AGENT"] = "test-client"
        return super().generic(*args, **kwargs)
