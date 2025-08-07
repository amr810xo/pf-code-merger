# PF Code PDF Merger (Clean + Print-Ready)

This Streamlit app lets you:
- Upload a CSV of PF Codes (must contain a column named **PF Code**)
- Upload the corresponding PDFs (named by PF Code, like PF01.pdf, PF02.pdf, etc.)
- Automatically clean them to be print-ready
- Merge them in batches of 100 pages
- Download a ZIP file of merged PDF batches

## How to Run

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run the app:
```
streamlit run merge_pf_codes_cleaned.py
```

3. Upload your CSV and PDFs, then download the final ZIP.