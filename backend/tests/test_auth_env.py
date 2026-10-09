import os
import auth


def test_quoted_env_values_are_tolerated(monkeypatch):
    h = auth.hash_password("pw", iterations=1000)
    monkeypatch.setenv("AUTH_USERNAME", "'jesus'")
    monkeypatch.setenv("AUTH_PASSWORD_HASH", f"'{h}'")
    monkeypatch.setenv("SESSION_SECRET", "'" + "x" * 20 + "'")
    user, pw_hash, _, secret = auth._config()
    assert user == "jesus" and secret == "x" * 20
    assert auth._verify_hash("pw", pw_hash)
    assert not auth._verify_hash("wrong", pw_hash)
