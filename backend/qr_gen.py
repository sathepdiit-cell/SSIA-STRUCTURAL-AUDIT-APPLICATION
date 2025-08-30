# qr_gen.py
import qrcode
from pathlib import Path

def make_qr_image(b64payload: str, out: Path):
    qr = qrcode.QRCode(version=None, box_size=6, border=4)
    qr.add_data(b64payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(out)
