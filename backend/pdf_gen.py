# pdf_gen.py
from jinja2 import Template
import subprocess
from pathlib import Path

TEMPLATE = """
<html><body>
<h1>Audit Report: {{audit_id}}</h1>
<p>Client: {{client}}</p>
<h2>Key Findings</h2>
<table border='1' style='border-collapse:collapse'>
{% for row in rows %}
<tr><td>{{row.Timestamp}}</td><td>{{row.User}}</td><td>{{row.Action}}</td><td>{{row.Details}}</td></tr>
{% endfor %}
</table>
<h2>Appendix: Dashboard</h2>
<p>(charts embedded)</p>
<img src="{{qr_path}}" alt="QR"/>
</body></html>
"""

def generate_pdf_from_xlsx(xlsx_path, pdf_path):
    # For prototype: load audit_data JSON and render template
    # In real flow, read excel data or read the app data source
    audit_id = Path(xlsx_path).stem
    # read a "data.json" or pass in structured data. For demo, just create a simple HTML
    html = Template(TEMPLATE).render(audit_id=audit_id, client="Demo Client", rows=[{"Timestamp":"ts","User":"u","Action":"a","Details":"d"}], qr_path=str(Path(xlsx_path).with_suffix(".qr.png")))
    tmphtml = Path(xlsx_path).with_suffix(".html")
    tmphtml.write_text(html, encoding="utf8")
    # requires wkhtmltopdf installed on the host
    subprocess.run(["wkhtmltopdf", str(tmphtml), str(pdf_path)], check=True)
