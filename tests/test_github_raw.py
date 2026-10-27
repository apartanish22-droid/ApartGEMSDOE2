import hashlib
import io
from urllib.error import HTTPError
from urllib.request import Request

import pytest

import fetch_audit_data
from github_raw import SameHostRedirect, stream_raw, validate_target


def test_streams_binary_without_utf8_conversion(monkeypatch):
    payload = b'\x00\xff\xfe\xc3\x00binary\x80'
    observed = {}
    class Opener:
        def open(self, request, timeout):
            observed['url'] = request.full_url
            observed['accept'] = request.get_header('Accept')
            observed['authorization'] = request.get_header('Authorization')
            observed['timeout'] = timeout
            return io.BytesIO(payload)
    monkeypatch.setenv('GH_TOKEN', 'test-token')
    out = io.BytesIO()
    stream_raw('owner/repo', 'a' * 40, 'a path/b.tif', out, opener=Opener())
    assert out.getvalue() == payload
    assert observed['url'] == 'https://api.github.com/repos/owner/repo/contents/a%20path/b.tif?ref=' + 'a' * 40
    assert observed['accept'] == 'application/vnd.github.raw+json'
    assert observed['authorization'] == 'Bearer test-token'
    assert observed['timeout'] == 300


def test_redirect_never_leaks_authorization_to_another_host():
    handler = SameHostRedirect()
    request = Request('https://api.github.com/start', headers={'Authorization': 'Bearer test-token'})
    for target in ('https://example.com/steal', 'http://api.github.com/insecure'):
        with pytest.raises(HTTPError, match='Refusing'):
            handler.redirect_request(request, None, 302, 'redirect', {}, target)
    safe = handler.redirect_request(request, None, 302, 'redirect', {}, 'https://api.github.com/other')
    assert safe.full_url == 'https://api.github.com/other'


def test_rejects_unpinned_or_unsafe_sources():
    for repo, ref, path in [
        ('owner/repo', 'main', 'x'), ('owner/repo', 'a'*40, '../x'),
        ('owner/repo', 'a'*40, 'x?ref=evil'), ('owner/repo', 'a'*40, '/x'),
        ('owner/repo', 'a'*40, 'a\\b'), ('evil/owner/repo', 'a'*40, 'x'),
        ('../repo', 'a'*40, 'x'),
    ]:
        with pytest.raises(ValueError):
            validate_target(repo, ref, path)


def test_hash_mismatch_preserves_old_file_and_removes_temp(tmp_path, monkeypatch):
    destination = tmp_path / 'file.tif'
    destination.write_bytes(b'previous')
    pin = {'id': 'test', 'repo': 'owner/repo', 'ref': 'a'*40, 'path': 'file.tif',
           'sha256': hashlib.sha256(b'correct').hexdigest()}
    monkeypatch.setattr(fetch_audit_data, 'stream_raw', lambda repo, ref, path, out: out.write(b'wrong'))
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        fetch_audit_data.fetch_one(pin, destination)
    assert destination.read_bytes() == b'previous'
    assert list(tmp_path.iterdir()) == [destination]
    monkeypatch.setattr(fetch_audit_data, 'stream_raw', lambda repo, ref, path, out: out.write(b'correct'))
    assert fetch_audit_data.fetch_one(pin, destination) == 'downloaded and verified'
    assert destination.read_bytes() == b'correct'
