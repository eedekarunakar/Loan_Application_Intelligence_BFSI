import io
import json
import re
from pathlib import Path

import streamlit as st

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

st.set_page_config(page_title="Nidhi | Loan Intelligence", page_icon="✦", layout="wide", initial_sidebar_state="expanded")
ROOT = Path(__file__).parent
SAMPLE_DIR = ROOT / "data" / "sample_applications"

SAMPLE_TEXT = {
    "LA-2026-014": """LOAN APPLICATION | LA-2026-014
Applicant name: Meena Devi
Village / district: Kuppam, Chittoor, Andhra Pradesh
Requested loan amount: INR 85,000
Loan tenure: 24 months
Purpose of loan: Purchase of two milch buffaloes and cattle feed for the dairy activity.
Occupation: Dairy and agriculture
Declared monthly household income: INR 28,500
Average monthly bank credits (last 6 months): INR 27,800
Existing monthly EMI obligations: INR 4,200
Number of dependents: 3
Co-applicant: Ravi Kumar (spouse), self-employed electrician
Documents submitted: Aadhaar, bank statement, milk collection receipts, address proof
""",
    "LA-2026-019": """LOAN APPLICATION | LA-2026-019
Applicant name: Suresh Babu
Village / district: Madanapalle, Annamayya, Andhra Pradesh
Requested loan amount: INR 1,50,000
Loan tenure: 18 months
Purpose of loan: Working capital for a mobile repair and accessories shop.
Occupation: Small business owner
Declared monthly household income: INR 42,000
Average monthly bank credits (last 6 months): INR 11,500
Existing monthly EMI obligations: INR 18,000
Number of dependents: 5
Co-applicant: Lakshmi Babu (spouse), homemaker
Documents submitted: Aadhaar, voter ID, partial bank statement
""",
    "LA-2026-023": """LOAN APPLICATION | LA-2026-023
Applicant name: Farzana Begum
Village / district: Kurnool, Andhra Pradesh
Requested loan amount: INR 60,000
Loan tenure: 12 months
Purpose of loan: Purchase sewing machine and fabric for tailoring orders.
Occupation: Tailor
Declared monthly household income: INR 21,000
Average monthly bank credits (last 6 months): INR 20,400
Existing monthly EMI obligations: INR 2,000
Number of dependents: 2
Co-applicant: Imran Khan (brother), driver
Documents submitted: Aadhaar, bank statement, tailoring order book, address proof
""",
}


def money(value):
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None


def find_value(text, label, pattern=r"[^\n]+"):
    match = re.search(rf"{re.escape(label)}\s*:\s*({pattern})", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_application(text, filename):
    income_text = find_value(text, "Declared monthly household income")
    credits_text = find_value(text, "Average monthly bank credits (last 6 months)")
    loan_text = find_value(text, "Requested loan amount")
    fields = {
        "Application ID": find_value(text, "LOAN APPLICATION", r"[A-Z]{2}-[0-9-]+") or Path(filename).stem,
        "Applicant": find_value(text, "Applicant name"),
        "Location": find_value(text, "Village / district"),
        "Loan amount": money(loan_text),
        "Tenure": find_value(text, "Loan tenure"),
        "Purpose": find_value(text, "Purpose of loan"),
        "Occupation": find_value(text, "Occupation"),
        "Declared monthly income": money(income_text),
        "Average monthly credits": money(credits_text),
        "Existing monthly EMI": money(find_value(text, "Existing monthly EMI obligations")),
        "Dependents": find_value(text, "Number of dependents"),
        "Co-applicant": find_value(text, "Co-applicant"),
        "Documents": find_value(text, "Documents submitted"),
    }
    risks = []
    declared, credits = fields["Declared monthly income"], fields["Average monthly credits"]
    if declared and credits:
        variance = abs(declared - credits) / declared
        if variance >= 0.25:
            risks.append({"severity": "High" if variance >= 0.50 else "Medium", "title": "Income-credit mismatch", "detail": f"Declared income is INR {declared:,}, while average bank credits are INR {credits:,} ({variance:.0%} variance).", "evidence": f"Declared monthly household income: {income_text}; Average monthly bank credits: {credits_text}"})
    elif not declared or not credits:
        risks.append({"severity": "Medium", "title": "Income evidence incomplete", "detail": "Declared income and bank-credit evidence could not both be verified from the document.", "evidence": "Missing one or both income fields"})

    purpose = (fields["Purpose"] or "").lower()
    matched_term = next((term for term in ["crypto", "betting", "gambling", "speculation", "luxury car", "foreign exchange"] if term in purpose), None)
    if matched_term:
        risks.append({"severity": "High", "title": "Purpose requires enhanced review", "detail": f"The purpose statement contains '{matched_term}', outside the standard microfinance purpose list.", "evidence": fields["Purpose"]})

    required = ["Applicant", "Location", "Loan amount", "Purpose", "Occupation", "Declared monthly income", "Co-applicant", "Documents"]
    missing = [label for label in required if not fields[label]]
    if missing:
        risks.append({"severity": "Medium", "title": f"{len(missing)} required field(s) missing", "detail": "Complete the application before a final decision.", "evidence": ", ".join(missing)})
    emi, income = fields["Existing monthly EMI"], fields["Declared monthly income"]
    if emi and income and emi / income > 0.40:
        risks.append({"severity": "High", "title": "High existing repayment load", "detail": f"Existing EMI is {emi / income:.0%} of declared monthly income.", "evidence": f"Existing monthly EMI obligations: {emi:,}"})

    confidence = round((len(fields) - len(missing)) / len(fields) * 100)
    high_count = sum(risk["severity"] == "High" for risk in risks)
    decision = "Enhanced review" if high_count else ("Review missing fields" if missing else "Ready for officer review")
    if fields["Loan amount"] and fields["Declared monthly income"]:
        summary = f"{fields['Applicant']} is requesting INR {fields['Loan amount']:,} for {(fields['Purpose'] or 'an unspecified purpose').lower()} The application reports monthly household income of INR {fields['Declared monthly income']:,} and has {len(risks)} detected signal(s)."
    else:
        summary = "The application was partially parsed. Confirm the extracted fields against the source document before proceeding."
    return {"fields": fields, "risks": risks, "confidence": confidence, "decision": decision, "summary": summary, "source_text": text}


def read_pdf(uploaded_file):
    if PdfReader is None:
        raise RuntimeError("PDF support is unavailable. Install the packages in requirements.txt.")
    reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def render_risk(risk):
    css_class = risk["severity"].lower()
    st.markdown(f'<div class="risk {css_class}"><div class="risk-top"><span class="risk-pill {css_class}">{risk["severity"]}</span><strong>{risk["title"]}</strong></div><p>{risk["detail"]}</p><small>Evidence: {risk["evidence"]}</small></div>', unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root { --ink:#1d302f; --muted:#687875; --paper:#f3f5f1; --card:#fffefa; --line:#d8e1dc; --teal:#0e625d; --teal-dark:#173d3a; --sage:#dcebe4; --coral:#d77b69; --gold:#d7a84d; --red:#f3d8d1; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); } .stApp { background:var(--paper); background-image:radial-gradient(#d9e2dc 0.7px, transparent 0.7px); background-size:18px 18px; } .stApp h1, .stApp h2, .stApp h3, .stApp strong, .stApp .stat-value, .stApp .field-value { color:var(--ink) !important; }
[data-testid="stSidebar"] { background:var(--teal-dark); border-right:0; } [data-testid="stSidebar"] * { color:#f4f7f3 !important; } [data-testid="stSidebar"] .stCaption { color:#abc2b7 !important; } [data-testid="stSidebar"] hr { border-color:#37615c; }
.hero { padding:2.4rem 0 2rem; border-bottom:1px solid var(--line); animation:fade-in .55s ease both; } .eyebrow,.section-label { font-family:'IBM Plex Mono',monospace; color:var(--teal); letter-spacing:.09em; font-size:.7rem; text-transform:uppercase; font-weight:500; }
h1 { font-family:'Fraunces',serif !important; font-size:clamp(2.7rem,5.5vw,5.1rem) !important; font-weight:500 !important; line-height:.96 !important; letter-spacing:-.055em !important; margin:.55rem 0 .85rem !important; max-width:850px; color:var(--ink) !important; } .hero p { color:var(--muted) !important; max-width:610px; font-size:1rem; line-height:1.65; } .hero-kicker { display:inline-block; color:var(--teal); font:500 .7rem 'IBM Plex Mono',monospace; letter-spacing:.08em; }
.block-container { max-width:1380px; padding-top:3rem; padding-bottom:4rem; }
.stat { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:1.1rem 1.2rem; min-height:112px; transition:transform .2s ease, border-color .2s ease; } .stat:hover { transform:translateY(-3px); border-color:var(--teal); } .stat-label { color:var(--muted) !important; font:500 .69rem 'IBM Plex Mono',monospace; text-transform:uppercase; letter-spacing:.04em; } .stat-value { color:var(--ink) !important; font-size:1.46rem; font-weight:700; margin-top:.65rem; letter-spacing:-.045em; overflow-wrap:anywhere; }
.section-label { margin:2.25rem 0 .7rem; } .summary { background:var(--teal-dark); color:#f3f7f2; padding:1.45rem 1.55rem; font-size:1.03rem; line-height:1.65; border-radius:8px; border-left:6px solid var(--coral); }
.risk { background:var(--card); border:1px solid var(--line); border-left:5px solid var(--teal); border-radius:6px; padding:1rem 1.1rem; margin:.75rem 0; animation:fade-in .4s ease both; } .risk.high { border-left-color:var(--coral); background:#fffaf8; } .risk.medium { border-left-color:var(--gold); background:#fffdf6; } .risk-top { display:flex; align-items:center; gap:.65rem; } .risk p { margin:.5rem 0 .35rem; color:#40504d; } .risk small { color:var(--muted); font:.68rem 'IBM Plex Mono',monospace; }
.risk-pill { padding:.22rem .5rem; border-radius:3px; font:500 .62rem 'IBM Plex Mono',monospace; text-transform:uppercase; background:var(--sage); } .risk-pill.high { background:var(--red); color:#863e32 !important; } .risk-pill.medium { background:#f8e8bf; color:#765316 !important; }
.field { border-bottom:1px solid var(--line); padding:.72rem 0; display:flex; justify-content:space-between; gap:1rem; } .field-label { color:var(--muted) !important; font:.76rem 'IBM Plex Mono',monospace; } .field-value { color:var(--ink) !important; text-align:right; font-weight:600; max-width:60%; overflow-wrap:anywhere; }
.source { white-space:pre-wrap; background:#203d3a; border:0; border-radius:6px; padding:1rem; font:.72rem/1.65 'IBM Plex Mono',monospace; color:#e1eee7; max-height:310px; overflow:auto; } .stButton button { border-radius:6px; border:1px solid var(--line); font-weight:600; } .stDownloadButton button { border-radius:6px; background:var(--teal); color:#fff; border:0; font-weight:700; }
@keyframes fade-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } } @media (max-width:700px) { h1 { font-size:3.25rem !important; } }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("## ✦ NIDHI")
st.sidebar.caption("loan application intelligence")
st.sidebar.markdown("### Workspace")
source_mode = st.sidebar.radio("Choose input", ["Synthetic demo files", "Upload a PDF"], label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.caption("Grounding mode")
st.sidebar.markdown("**extract → verify → flag**")
st.sidebar.caption("Every signal includes source evidence. Decision support only.")
st.markdown('<div class="hero"><span class="hero-kicker">MICROFINANCE / INTAKE DESK</span><h1>A clearer view<br>of every application.</h1><p>Nidhi turns a loan application into a clear, evidence-backed brief so relationship officers can focus on the human conversation.</p></div>', unsafe_allow_html=True)

selected_name = None
text = None
if source_mode == "Synthetic demo files":
    samples = sorted(SAMPLE_DIR.glob("*.pdf")) if SAMPLE_DIR.exists() else []
    options = [path.stem for path in samples] or list(SAMPLE_TEXT)
    selected_name = st.sidebar.selectbox("Application", options)
    selected_path = next((path for path in samples if path.stem == selected_name), None)
    text = read_pdf(type("Upload", (), {"getvalue": lambda self: selected_path.read_bytes()})()) if selected_path else SAMPLE_TEXT[selected_name]
else:
    uploaded = st.sidebar.file_uploader("Upload loan application PDF", type=["pdf"])
    if uploaded:
        selected_name = uploaded.name
        try: text = read_pdf(uploaded)
        except Exception as exc: st.error(str(exc))

if not text:
    st.info("Select a synthetic application or upload a PDF to create a grounded brief.")
    st.stop()

application = extract_application(text, selected_name or "application")
fields, risk_count = application["fields"], len(application["risks"])
high_count = sum(risk["severity"] == "High" for risk in application["risks"])
col1, col2, col3, col4 = st.columns(4)
for column, label, value in [(col1, "Parse confidence", f"{application['confidence']}%"), (col2, "Signals detected", str(risk_count)), (col3, "High priority", str(high_count)), (col4, "Officer route", application["decision"])]:
    with column: st.markdown(f'<div class="stat"><div class="stat-label">{label}</div><div class="stat-value">{value}</div></div>', unsafe_allow_html=True)
st.markdown('<div class="section-label">01 / Officer brief</div>', unsafe_allow_html=True)
st.markdown(f'<div class="summary">{application["summary"]}</div>', unsafe_allow_html=True)
left, right = st.columns([1.1, .9], gap="large")
with left:
    st.markdown('<div class="section-label">02 / Risk signals</div>', unsafe_allow_html=True)
    if application["risks"]:
        for risk in application["risks"]: render_risk(risk)
    else: st.success("No rule-based risk signals detected. Continue with standard verification.")
with right:
    st.markdown('<div class="section-label">03 / Extracted fields</div>', unsafe_allow_html=True)
    for label, value in fields.items():
        if label == "Application ID": continue
        display = "Not found" if value in (None, "") else (f"INR {value:,}" if isinstance(value, int) else value)
        st.markdown(f'<div class="field"><span class="field-label">{label}</span><span class="field-value">{display}</span></div>', unsafe_allow_html=True)
st.markdown('<div class="section-label">04 / Source evidence</div>', unsafe_allow_html=True)
with st.expander("View extracted document text"): st.markdown(f'<div class="source">{text}</div>', unsafe_allow_html=True)
export = {key: value for key, value in application.items() if key != "source_text"}
st.download_button("Download structured brief (JSON)", json.dumps(export, indent=2), file_name=f"{fields['Application ID'] or 'loan-brief'}.json", mime="application/json")