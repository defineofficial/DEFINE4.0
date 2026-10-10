"""Private storage and signed links. Needs no database and no FastAPI."""
import pytest

from app import storage
from app.storage import (EmptyFile, FileMissing, FileTooLarge, LinkExpired, LinkInvalid, UnsupportedFile)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
PDF = b"%PDF-1.7\n" + b"\x00" * 32
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32
MP3 = b"ID3\x04\x00" + b"\x00" * 32
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 32
M4A = b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 32
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
NOW = 1_800_000_000.0


@pytest.fixture(autouse=True)
def private_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("SECRET_KEY", "k" * 40)
    monkeypatch.delenv("STORAGE_LINK_TTL_SECONDS", raising=False)
    monkeypatch.delenv("PUBLIC_API_URL", raising=False)


def query(link: str) -> dict:
    return dict(p.split("=", 1) for p in link.split("?", 1)[1].split("&"))


# ---------- saving ----------

@pytest.mark.parametrize("kind,data,ext", [
    ("poster", PNG, "png"), ("poster", JPEG, "jpg"), ("poster", PDF, "pdf"),
    ("voice_note", WAV, "wav"), ("voice_note", MP3, "mp3"), ("voice_note", WEBM, "webm"), ("voice_note", M4A, "m4a"),
])
def test_accepted_files_are_saved_under_a_random_name(kind, data, ext):
    stored = storage.save(kind, "cmp_001", data)
    assert stored.key.endswith("." + ext) and stored.size == len(data)
    assert storage.read_bytes(stored.key) == data
    assert stored.key.startswith(("posters/cmp_001/", "voice-notes/cmp_001/"))


def test_type_is_decided_by_content_not_by_name_or_header():
    with pytest.raises(UnsupportedFile):
        storage.save("poster", "cmp_001", b"just some text pretending to be a picture.png")


def test_svg_is_refused_because_it_can_carry_script():
    with pytest.raises(UnsupportedFile):
        storage.save("poster", "cmp_001", SVG)


def test_audio_is_not_accepted_as_a_poster_and_the_reverse():
    with pytest.raises(UnsupportedFile):
        storage.save("poster", "cmp_001", WAV)
    with pytest.raises(UnsupportedFile):
        storage.save("voice_note", "cmp_001", PNG)


def test_empty_file_is_refused():
    with pytest.raises(EmptyFile):
        storage.save("poster", "cmp_001", b"")


def test_poster_over_10_mb_is_refused_but_exactly_10_mb_is_fine():
    limit = storage.RULES["poster"].max_bytes
    assert storage.save("poster", "cmp_001", PNG + b"\x00" * (limit - len(PNG))).size == limit
    with pytest.raises(FileTooLarge):
        storage.save("poster", "cmp_001", PNG + b"\x00" * (limit - len(PNG) + 1))


@pytest.mark.parametrize("bad_id", ["../etc", "a/b", "", "x" * 65, "a b", "..", "cmp\x00", "cmp_001\n"])
def test_campaign_id_cannot_steer_the_path(bad_id):
    with pytest.raises(storage.StorageError):
        storage.save("poster", bad_id, PNG)


def test_nothing_is_written_outside_the_storage_folder(tmp_path):
    storage.save("poster", "cmp_001", PNG)
    outside = [p for p in tmp_path.rglob("*") if p.is_file() and "store" not in p.parts]
    assert outside == []


def test_two_uploads_never_share_a_key():
    assert storage.save("poster", "cmp_001", PNG).key != storage.save("poster", "cmp_001", PNG).key


# ---------- keys ----------

@pytest.mark.parametrize("key", [
    "../../etc/passwd", "posters/../../x.png", "/etc/passwd", "posters/cmp_001/notarandomname.png",
    "other/cmp_001/" + "a" * 32 + ".png", "posters/cmp_001/" + "a" * 32 + ".png\n", "posters/cmp_001/" + "a" * 32 + ".exe", "posters\\cmp_001\\x",
])
def test_keys_that_this_module_did_not_make_are_not_found_or_signed(key):
    with pytest.raises(FileMissing):
        storage.locate(key)
    with pytest.raises(FileMissing):
        storage.signed_path(key)


def test_delete_removes_the_file_and_ignores_junk():
    stored = storage.save("poster", "cmp_001", PNG)
    storage.delete(stored.key)
    with pytest.raises(FileMissing):
        storage.locate(stored.key)
    storage.delete(stored.key)        # already gone
    storage.delete(None)
    storage.delete("../../etc/passwd")


# ---------- signed links ----------

def test_fresh_link_is_accepted_and_serves_the_right_type():
    stored = storage.save("poster", "cmp_001", PNG)
    link = storage.signed_path(stored.key, now=NOW)
    q = query(link)
    storage.verify(stored.key, q["exp"], q["sig"], now=NOW + 60)
    assert storage.locate(stored.key)[1] == "image/png"
    assert link.startswith("/files/" + stored.key + "?exp=")


def test_default_lifetime_is_15_minutes_and_can_be_set():
    key = storage.save("poster", "cmp_001", PNG).key
    assert int(query(storage.signed_path(key, now=NOW))["exp"]) == NOW + 900
    assert int(query(storage.signed_path(key, ttl=120, now=NOW))["exp"]) == NOW + 120


def test_lifetime_is_clamped():
    key = storage.save("poster", "cmp_001", PNG).key
    assert int(query(storage.signed_path(key, ttl=1, now=NOW))["exp"]) == NOW + 30
    assert int(query(storage.signed_path(key, ttl=10**9, now=NOW))["exp"]) == NOW + 7 * 24 * 3600


def test_env_lifetime_is_used_and_junk_falls_back(monkeypatch):
    key = storage.save("poster", "cmp_001", PNG).key
    monkeypatch.setenv("STORAGE_LINK_TTL_SECONDS", "300")
    assert int(query(storage.signed_path(key, now=NOW))["exp"]) == NOW + 300
    monkeypatch.setenv("STORAGE_LINK_TTL_SECONDS", "soon")
    assert int(query(storage.signed_path(key, now=NOW))["exp"]) == NOW + 900


def test_expired_link_is_refused_at_and_after_the_expiry_second():
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    storage.verify(key, q["exp"], q["sig"], now=NOW + 899)
    with pytest.raises(LinkExpired):
        storage.verify(key, q["exp"], q["sig"], now=NOW + 900)
    with pytest.raises(LinkExpired):
        storage.verify(key, q["exp"], q["sig"], now=NOW + 10**6)


def test_changing_the_expiry_breaks_the_link():
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    with pytest.raises(LinkInvalid):
        storage.verify(key, str(int(q["exp"]) + 86400), q["sig"], now=NOW)


def test_a_link_cannot_be_used_for_a_different_file():
    a = storage.save("poster", "cmp_001", PNG).key
    b = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(a, now=NOW))
    with pytest.raises(LinkInvalid):
        storage.verify(b, q["exp"], q["sig"], now=NOW)


@pytest.mark.parametrize("sig", ["", "0" * 64, "zzz", "A" * 10])
def test_bad_signatures_are_refused(sig):
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    with pytest.raises(LinkInvalid):
        storage.verify(key, q["exp"], sig, now=NOW)


@pytest.mark.parametrize("exp", ["", "abc", "1.5", None])
def test_bad_expiry_values_are_refused(exp):
    key = storage.save("poster", "cmp_001", PNG).key
    with pytest.raises(LinkInvalid):
        storage.verify(key, exp, "0" * 64, now=NOW)


def test_forged_link_gets_invalid_not_expired():
    """A forger must not learn whether a guessed expiry was in the past."""
    key = storage.save("poster", "cmp_001", PNG).key
    with pytest.raises(LinkInvalid):
        storage.verify(key, str(int(NOW) - 5000), "0" * 64, now=NOW)


def test_links_stop_working_when_the_secret_changes(monkeypatch):
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    monkeypatch.setenv("SECRET_KEY", "z" * 40)
    with pytest.raises(LinkInvalid):
        storage.verify(key, q["exp"], q["sig"], now=NOW)


def test_signing_key_is_not_the_raw_secret():
    import hashlib
    import hmac
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    naive = hmac.new(b"k" * 40, f"{key}\n{q['exp']}".encode(), hashlib.sha256).hexdigest()
    assert q["sig"] != naive   # a login-token key cannot be turned into a file link


def test_short_secret_still_works_for_this_run_only(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "short")
    key = storage.save("poster", "cmp_001", PNG).key
    q = query(storage.signed_path(key, now=NOW))
    storage.verify(key, q["exp"], q["sig"], now=NOW)


def test_signed_url_adds_the_public_base_when_set(monkeypatch):
    key = storage.save("poster", "cmp_001", PNG).key
    assert storage.signed_url(key, now=NOW).startswith("/files/")
    monkeypatch.setenv("PUBLIC_API_URL", "https://api.example.org/")
    assert storage.signed_url(key, now=NOW).startswith("https://api.example.org/files/posters/")
