"""
crypto_utils.py
================
Cryptographic primitives for the Secure Question-Paper Management System.

Design (maps to "Confidentiality", "Integrity" and "Secure Storage" goals):

  1. ENVELOPE ENCRYPTION
     Each question paper is encrypted with a fresh, random AES-256-GCM
     "Data Encryption Key" (DEK). The DEK itself is then encrypted
     ("wrapped") with the RSA public key of a "Key Encryption Key" (KEK)
     holder (conceptually: an HSM / cloud KMS). This means:
       - Compromising the storage layer alone yields only ciphertext.
       - Compromising a single DEK exposes only ONE document, not all of them.
       - The private KEK material never has to touch the document store.

  2. INTEGRITY
     - AES-GCM is an AEAD cipher: it detects any bit-flip / tampering in the
       ciphertext automatically (authentication tag).
     - In addition we keep a SHA-256 hash of the plaintext and an RSA
       digital signature over that hash, so integrity can be verified
       independently of decryption (e.g. by an auditor who only has the
       hash + signature, not the key).

  3. NO HOME-GROWN CRYPTO
     All primitives come from the `cryptography` library (audited,
     industry standard). We never implement our own cipher.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import rsa, padding as asy_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# --------------------------------------------------------------------------
# Key generation (stand-in for a cloud KMS / HSM issuing a Key-Encryption-Key)
# --------------------------------------------------------------------------

def generate_kek_keypair(key_size: int = 3072):
    """Generate the organization's master Key-Encryption-Key (RSA keypair).

    In production this would be generated inside an HSM / cloud KMS
    (e.g. AWS KMS, GCP Cloud HSM) and the private key would never leave it.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    return private_key, private_key.public_key()


# --------------------------------------------------------------------------
# Envelope encryption
# --------------------------------------------------------------------------

@dataclass
class EncryptedPayload:
    ciphertext: bytes          # AES-GCM ciphertext (includes auth tag)
    nonce: bytes                # 96-bit AES-GCM nonce
    wrapped_dek: bytes          # DEK, RSA-OAEP encrypted under the KEK
    plaintext_sha256: str        # hash of the ORIGINAL plaintext (integrity)
    signature: bytes            # RSA signature over plaintext_sha256


def encrypt_document(plaintext: bytes, kek_public_key, signing_private_key) -> EncryptedPayload:
    """Encrypt a question paper (bytes) using fresh envelope encryption.

    Returns everything needed to store the document securely: ciphertext,
    the wrapped per-document key, and an integrity signature.
    """
    # 1. Fresh, random 256-bit data encryption key -- unique per document.
    dek = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(dek)
    nonce = os.urandom(12)  # 96-bit nonce, standard for GCM

    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)

    # 2. Wrap (encrypt) the DEK under the org's RSA public key (KEK).
    wrapped_dek = kek_public_key.encrypt(
        dek,
        asy_padding.OAEP(
            mgf=asy_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # 3. Integrity: hash the plaintext and sign the hash.
    digest = hashlib.sha256(plaintext).hexdigest()
    signature = signing_private_key.sign(
        digest.encode(),
        asy_padding.PSS(
            mgf=asy_padding.MGF1(hashes.SHA256()),
            salt_length=asy_padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return EncryptedPayload(
        ciphertext=ciphertext,
        nonce=nonce,
        wrapped_dek=wrapped_dek,
        plaintext_sha256=digest,
        signature=signature,
    )


def decrypt_document(payload: EncryptedPayload, kek_private_key, signing_public_key) -> bytes:
    """Reverse of encrypt_document. Raises if integrity/signature checks fail."""
    # 1. Unwrap the DEK using the KEK private key (only the KMS/HSM holder can do this).
    dek = kek_private_key.decrypt(
        payload.wrapped_dek,
        asy_padding.OAEP(
            mgf=asy_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # 2. Decrypt. AES-GCM will raise InvalidTag if the ciphertext was tampered with.
    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(payload.nonce, payload.ciphertext, associated_data=None)

    # 3. Verify the digital signature over the stored hash (defence in depth).
    signing_public_key.verify(
        payload.signature,
        payload.plaintext_sha256.encode(),
        asy_padding.PSS(
            mgf=asy_padding.MGF1(hashes.SHA256()),
            salt_length=asy_padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # 4. Verify the hash matches the freshly decrypted plaintext.
    if hashlib.sha256(plaintext).hexdigest() != payload.plaintext_sha256:
        raise ValueError("Integrity check failed: plaintext hash mismatch")

    return plaintext


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# Key (de)serialization helpers, used for demo persistence
# --------------------------------------------------------------------------

def serialize_public_key(pub) -> bytes:
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def serialize_private_key(priv, password: bytes | None = None) -> bytes:
    enc = (
        serialization.BestAvailableEncryption(password)
        if password
        else serialization.NoEncryption()
    )
    return priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=enc,
    )
