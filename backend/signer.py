from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

KEY_DIR = Path("keys")
KEY_DIR.mkdir(exist_ok=True)

def generate_keys():
    """Generate RSA private/public key pair in correct PEM format (PKCS#8)."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()

    # Save private key in PKCS#8 format
    priv_bytes = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    (KEY_DIR / "private_key.pem").write_bytes(priv_bytes)

    # Save public key in SubjectPublicKeyInfo format
    pub_bytes = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    (KEY_DIR / "public_key.pem").write_bytes(pub_bytes)

    return priv, pub

def load_private_key(path="keys/private_key.pem"):
    """Load private key or auto-generate if missing/invalid."""
    p = Path(path)
    try:
        return serialization.load_pem_private_key(p.read_bytes(), password=None)
    except Exception:
        # If file missing or invalid → regenerate
        priv, _ = generate_keys()
        return priv

def load_public_key(path="keys/public_key.pem"):
    """Load public key or auto-generate if missing/invalid."""
    p = Path(path)
    try:
        return serialization.load_pem_public_key(p.read_bytes())
    except Exception:
        _, pub = generate_keys()
        return pub

