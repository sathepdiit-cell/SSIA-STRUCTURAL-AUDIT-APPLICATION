# app.py
from flask import Flask, request, jsonify, send_file
from pathlib import Path
import json, datetime, base64
from excel_gen import build_workbook  # implemented below
from signer import load_private_key, sign_bytes, load_public_key, verify_signature
from qr_gen import make_qr_image
from apscheduler.schedulers.background import BackgroundScheduler

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)
AUDIT_SOURCE = Path("data/audit_data.json")  # central data source (sample)

app = Flask(__name__)
privkey = load_private_key("keys/private_key.pem")
pubkey = load_public_key("keys/public_key.pem")

def compute_and_generate(audit_id="SSIA-AUDIT-0001", save_versioned=True):
    # 1) read audit source
    data = json.loads(AUDIT_SOURCE.read_text(encoding="utf8"))
    # 2) build workbook object and save workbook (retains formulas & conditional formatting)
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    prefix = f"{audit_id}_{timestamp}"
    xlsx_path = REPORT_DIR / (prefix + ".xlsx")
    build_workbook(data, xlsx_path)  # creates workbook and writes AuditTrail sheet (we'll sign below)
    # 3) compute rolling final hash by deterministic reading of audit log rows
    #   (we compute from data rather than re-parsing the workbook for deterministic behavior)
    from hashlib import sha256
    prev = b"GENESIS"
    for row in data["rows"]:
        # deterministic concatenation (user must keep same CSV/JSON ordering)
        row_str = "|".join([str(row.get(c,"")) for c in data["columns"]])
        h = sha256(prev + row_str.encode("utf8")).digest()
        prev = h
    final_hash = prev.hex()
    # 4) sign final_hash bytes
    signature = sign_bytes(privkey, bytes.fromhex(final_hash))  # returns base64
    # 5) append signature info to audit trail sheet
    #    (we will update xlsx to include FinalHash + signature in locked AuditTrail area)
    from excel_gen import append_audit_footer
    append_audit_footer(xlsx_path, final_hash, signature, timestamp)
    # 6) generate PDF with embedded appendix charts pulled from the workbook (we produce an image snapshot)
    pdf_path = REPORT_DIR / (prefix + ".pdf")
    # pdf_gen will create a PDF using the Excel data (e.g., render HTML template + wkhtmltopdf)
    from pdf_gen import generate_pdf_from_xlsx
    generate_pdf_from_xlsx(xlsx_path, pdf_path)
    # 7) create compact QR payload (base64 of JSON)
    payload = {"audit_id": audit_id, "final_hash": final_hash, "signature": signature, "ts": timestamp}
    payload_text = json.dumps(payload, separators=(",", ":"))
    b64 = base64.b64encode(payload_text.encode()).decode()
    qr_path = REPORT_DIR / (prefix + ".qr.png")
    make_qr_image(b64, qr_path)
    # 8) optionally embed QR into PDF (pdf_gen does that)
    # done
    return {"xlsx": str(xlsx_path), "pdf": str(pdf_path), "qr": str(qr_path), "payload": payload}

@app.route("/regenerate", methods=["POST"])
def regenerate_route():
    body = request.json or {}
    audit_id = body.get("audit_id", "SSIA-AUDIT-0001")
    result = compute_and_generate(audit_id=audit_id)
    return jsonify({"status":"ok", "result": result})

@app.route("/reports/<path:fname>")
def download(fname):
    filep = REPORT_DIR / fname
    if not filep.exists():
        return ("Not found", 404)
    return send_file(filep, as_attachment=True)

# Scheduled auto-regeneration (example: weekly)
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: compute_and_generate("SSIA-AUDIT-0001"), trigger="cron", day_of_week="fri", hour=17, minute=0)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
