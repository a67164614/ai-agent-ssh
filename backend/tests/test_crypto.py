import pytest

from app.core.crypto import CredentialCipher


def test_encrypts_and_decrypts_secret() -> None:
    cipher = CredentialCipher("test-secret")

    encrypted = cipher.encrypt("sk-demo")

    assert encrypted != "sk-demo"
    assert cipher.decrypt(encrypted) == "sk-demo"


def test_rejects_wrong_secret() -> None:
    encrypted = CredentialCipher("first-secret").encrypt("ssh-password")

    with pytest.raises(ValueError):
        CredentialCipher("second-secret").decrypt(encrypted)


def test_masks_secret_without_revealing_full_value() -> None:
    cipher = CredentialCipher("test-secret")

    assert cipher.mask("sk-1234567890abcdef") == "sk-1********cdef"
    assert cipher.mask("") == ""
