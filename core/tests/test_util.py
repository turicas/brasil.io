import gzip
import zlib

from core.util import http_get


class FakeResponse:
    def __init__(self, body, content_encoding):
        self._body = body
        self._content_encoding = content_encoding

    def info(self):
        return {"Content-Encoding": self._content_encoding}

    def read(self):
        return self._body


def test_http_get_without_content_encoding(monkeypatch):
    payload = b"some data"
    monkeypatch.setattr("core.util.urlopen", lambda *args, **kwargs: FakeResponse(payload, None))
    assert http_get("https://example.com", timeout=1) == payload


def test_http_get_with_gzip_content_encoding(monkeypatch):
    payload = b'{"foo": "bar"}'
    compressed = gzip.compress(payload)
    monkeypatch.setattr("core.util.urlopen", lambda *args, **kwargs: FakeResponse(compressed, "gzip"))
    assert http_get("https://example.com", timeout=1) == payload


def test_http_get_with_deflate_content_encoding(monkeypatch):
    payload = b'{"foo": "bar"}'

    # deflate = stream zlib (RFC 1950), como definido no RFC 9110
    compressed = zlib.compress(payload)
    monkeypatch.setattr("core.util.urlopen", lambda *args, **kwargs: FakeResponse(compressed, "deflate"))
    assert http_get("https://example.com", timeout=1) == payload

    # alguns servidores enviam deflate "cru" (RFC 1951), sem header zlib
    compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    compressed = compressor.compress(payload) + compressor.flush()
    monkeypatch.setattr("core.util.urlopen", lambda *args, **kwargs: FakeResponse(compressed, "deflate"))
    assert http_get("https://example.com", timeout=1) == payload
