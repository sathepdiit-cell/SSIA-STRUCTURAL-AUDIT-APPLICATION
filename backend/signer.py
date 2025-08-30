# signer.py
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding
import base64

def load_private_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def load_public_key(path):
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())

def sign_bytes(priv_key, data_bytes) -> str:
    # Using ECDSA P-256
    if isinstance(priv_key, ec.EllipticCurvePrivateKey):
        sig = priv_key.sign(data_bytes, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(sig).decode()
    # fallback to RSA
    else:
        sig = priv_key.sign(data_bytes, padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(sig).decode()

def verify_signature(pub_key, data_bytes, signature_b64):
    sig = base64.b64decode(signature_b64)
    try:
        if hasattr(pub_key, "verifier"):
            # older API
            pub_key.verify(sig, data_bytes, padding.PKCS1v15(), hashes.SHA256())
        else:
            # try ECDSA
            pub_key.verify(sig, data_bytes, ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False
