from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).parents[1] / "data" / "sample_applications"
OUT.mkdir(parents=True, exist_ok=True)

APPLICATIONS = {
    "LA-2026-014": ("Meena Devi", "Kuppam, Chittoor, Andhra Pradesh", "85,000", "24 months", "Purchase of two milch buffaloes and cattle feed for the dairy activity.", "Dairy and agriculture", "28,500", "27,800", "4,200", "3", "Ravi Kumar (spouse), self-employed electrician", "Aadhaar, bank statement, milk collection receipts, address proof"),
    "LA-2026-019": ("Suresh Babu", "Madanapalle, Annamayya, Andhra Pradesh", "1,50,000", "18 months", "Working capital for a mobile repair and accessories shop.", "Small business owner", "42,000", "11,500", "18,000", "5", "Lakshmi Babu (spouse), homemaker", "Aadhaar, voter ID, partial bank statement"),
    "LA-2026-023": ("Farzana Begum", "Kurnool, Andhra Pradesh", "60,000", "12 months", "Purchase sewing machine and fabric for tailoring orders.", "Tailor", "21,000", "20,400", "2,000", "2", "Imran Khan (brother), driver", "Aadhaar, bank statement, tailoring order book, address proof"),
    "LA-2026-031": ("Anitha Reddy", "Nandyal, Andhra Pradesh", "1,20,000", "24 months", "Purchase of drip irrigation equipment and seeds for chilli cultivation.", "Farmer", "35,000", "34,200", "5,000", "4", "Mahesh Reddy (spouse), farmer", "Aadhaar, bank statement, land passbook, quotation"),
    "LA-2026-037": ("Basha Shaik", "Kadapa, Andhra Pradesh", "75,000", "18 months", "Expand a small tiffin and breakfast food stall near the bus stand.", "Food vendor", "24,000", "22,600", "3,500", "3", "Noorjahan Begum (spouse), homemaker", "Aadhaar, bank statement, municipal vendor receipt"),
    "LA-2026-042": ("Padma Kumari", "Srikakulam, Andhra Pradesh", "90,000", "12 months", "Purchase stock for a home-based handicraft and saree resale business.", "Micro-entrepreneur", "30,000", "29,100", "16,000", "2", "Ramesh Kumar (spouse), construction worker", "Aadhaar, bank statement, supplier invoices, address proof"),
}

labels = ["Applicant name", "Village / district", "Requested loan amount", "Loan tenure", "Purpose of loan", "Occupation", "Declared monthly household income", "Average monthly bank credits (last 6 months)", "Existing monthly EMI obligations", "Number of dependents", "Co-applicant", "Documents submitted"]
styles = getSampleStyleSheet()
body = styles["BodyText"]
body.fontName, body.fontSize, body.leading = "Helvetica", 10, 16

for app_id, record in APPLICATIONS.items():
    destination = OUT / f"{app_id}.pdf"
    document = SimpleDocTemplate(str(destination), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=20 * mm, bottomMargin=20 * mm)
    story = [Paragraph(f"<b>LOAN APPLICATION | {app_id}</b>", styles["Title"]), Spacer(1, 8)]
    for label, value in zip(labels, record):
        story.extend([Paragraph(f"<b>{label}:</b> {value}", body), Spacer(1, 3)])
    document.build(story)

print(f"Generated {len(APPLICATIONS)} PDFs in {OUT}")