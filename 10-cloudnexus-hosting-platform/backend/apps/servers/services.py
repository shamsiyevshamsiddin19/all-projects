"""SSH keypair generation.

The private key is never written to the database: it is handed to the user
once, right after generation, and only the public half is persisted.
"""
import base64
import hashlib
from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass(frozen=True)
class GeneratedKey:
    private_key: str
    public_key: str
    fingerprint: str


def generate_keypair(comment: str) -> GeneratedKey:
    """Create an Ed25519 keypair in OpenSSH format."""
    private = ed25519.Ed25519PrivateKey.generate()

    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_openssh = private.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()

    safe_comment = comment.replace("\n", " ").replace("\r", " ").strip()[:120]
    public_with_comment = f"{public_openssh} {safe_comment}".strip()

    return GeneratedKey(
        private_key=private_pem,
        public_key=public_with_comment,
        fingerprint=fingerprint_for(public_openssh),
    )


def fingerprint_for(public_key: str) -> str:
    """OpenSSH-style SHA256 fingerprint (`SHA256:base64`)."""
    parts = public_key.split()
    if len(parts) < 2:
        raise ValueError("Ochiq kalit formati noto'g'ri")
    blob = base64.b64decode(parts[1])
    digest = hashlib.sha256(blob).digest()
    encoded = base64.b64encode(digest).decode().rstrip("=")
    return f"SHA256:{encoded}"
