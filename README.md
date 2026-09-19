# Nidhi | Loan Application Intelligence

An evidence-first Streamlit prototype for microfinance relationship officers. Nidhi extracts important fields from an Indian loan application, creates a plain-language brief, and flags explainable risk signals with source evidence.

## Run locally

```powershell
python -m pip install -r requirements.txt
python scripts/generate_sample_pdfs.py
streamlit run app.py
```

Open the local URL shown by Streamlit. The app includes six synthetic Andhra Pradesh applications and accepts additional PDF uploads.

## Included

- PDF text ingestion with `pypdf`
- Transparent local field extraction
- Income-to-bank-credit consistency checks
- Unusual-purpose and repayment-load flags
- Missing-field detection and parse confidence
- Downloadable structured JSON brief

This demo deliberately keeps extraction deterministic and inspectable. For production, replace the extractor with a provider-approved document model or LLM call, retain page-level citations, add authentication, and validate outputs against the institution's credit policy before use.

## Streamlit Community Cloud

Create a new app from this repository, set the main file to `app.py`, and deploy. `requirements.txt` is included for dependency installation. No API key is required for this demo.