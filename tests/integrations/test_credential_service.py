import pytest
from integrations.crypto import CredentialService


class TestCredentialService:
    def test_encrypt_and_decrypt_secret(self):
        original_secret = "https://hooks.slack.com/services/T00/B00/X00"
        encrypted = CredentialService.encrypt(original_secret)
        assert encrypted is not None
        assert encrypted != original_secret

        decrypted = CredentialService.decrypt(encrypted)
        assert decrypted == original_secret

    def test_encrypt_none_returns_none(self):
        assert CredentialService.encrypt(None) is None
        assert CredentialService.decrypt(None) is None

    def test_decrypt_invalid_ciphertext_raises_value_error(self):
        with pytest.raises(ValueError, match="Decryption failed"):
            CredentialService.decrypt("invalid_cipher_text_12345")
