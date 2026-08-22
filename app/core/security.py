import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from jose import JWTError, jwt

from app.config import get_settings


def create_jwt_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=24)

    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_jwt_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None


def _derive_aes_key(secret: str) -> bytes:
    """Derive 256-bit encryption key using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=b"signal-fabric-credential-salt-v1",
        info=b"oauth-token-encryption",
    )
    return hkdf.derive(secret.encode("utf-8"))


def encrypt_credential(plaintext: Optional[str], secret_key: Optional[str] = None) -> Optional[str]:
    """
    Encrypts a sensitive OAuth token using AES-256-GCM authenticated encryption.
    Returns format: 'enc:v1:<base64(nonce + ciphertext + tag)>'.
    """
    if not plaintext:
        return plaintext

    # If already encrypted, return as is
    if plaintext.startswith("enc:v1:"):
        return plaintext

    key_src = secret_key or get_settings().jwt_secret
    aes_key = _derive_aes_key(key_src)
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)  # 96-bit standard GCM nonce
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    encoded = base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")
    return f"enc:v1:{encoded}"


def decrypt_credential(ciphertext: Optional[str], secret_key: Optional[str] = None) -> Optional[str]:
    """
    Decrypts an AES-256-GCM encrypted OAuth token.
    Gracefully handles unencrypted legacy tokens if prefix is absent.
    """
    if not ciphertext:
        return ciphertext

    if not ciphertext.startswith("enc:v1:"):
        # Legacy/plaintext fallback
        return ciphertext

    try:
        raw_b64 = ciphertext[len("enc:v1:"):]
        payload = base64.urlsafe_b64decode(raw_b64.encode("utf-8"))
        nonce = payload[:12]
        encrypted_data = payload[12:]
        key_src = secret_key or get_settings().jwt_secret
        aes_key = _derive_aes_key(key_src)
        aesgcm = AESGCM(aes_key)
        decrypted = aesgcm.decrypt(nonce, encrypted_data, None)
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential: {e}")

