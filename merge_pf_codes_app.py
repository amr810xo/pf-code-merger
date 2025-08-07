
import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os
import zipfile

st.title("📄 PF Code PDF Merger")

# Upload CSV
csv_file = st.file_uploader("Upload PF Code CSV (e.g. pf_codes_verified_complete.csv)", type=["csv"])

# Upload PDFs
pdf_files = st.file_uploader("Upload PF PDF files (e.g. PF01.pdf to PF26.pdf)", type=["pdf"], accept_multiple_files=True)

# Batch size selector
pages_per_batch = 100

# Run button
if csv_file and pdf_files and st.button("🔄 Merge PDFs"):
    with st.spinner("Processing..."):
        progress = st.progress(0)

        # Load CSV
        df = pd.read_csv(csv_file)
        pf_codes = df["PF Code"].tolist()

        # Save uploaded PDFs to temp folder
        temp_dir = tempfile.mkdtemp()
        pdf_map = {}
        for pdf in pdf_files:
            name = os.path.splitext(pdf.name)[0]
            path = os.path.join(temp_dir, pdf.name)
            with open(path, "wb") as f:
                f.write(pdf.read())
            pdf_map[name] = path

        # Build batches
        total_pages = len(pf_codes)
        batch_count = (total_pages + pages_per_batch - 1) // pages_per_batch
        output_paths = []

        for batch_num in range(batch_count):
            writer = PdfWriter()
            start = batch_num * pages_per_batch
            end = min(start + pages_per_batch, total_pages)
            batch_codes = pf_codes[start:end]

            for code in batch_codes:
                pdf_path = pdf_map.get(code)
                if pdf_path and os.path.exists(pdf_path):
                    reader = PdfReader(pdf_path)
                    writer.add_page(reader.pages[0])
                else:
                    st.warning(f"Missing PDF for code: {code}")

            out_path = os.path.join(temp_dir, f"compiled_batch_{batch_num + 1}.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            output_paths.append(out_path)

            progress.progress((batch_num + 1) / batch_count)

        # Zip output
        zip_path = os.path.join(temp_dir, "compiled_batches.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for path in output_paths:
                zipf.write(path, arcname=os.path.basename(path))

        # Download link
        with open(zip_path, "rb") as f:
            st.download_button("📥 Download ZIP of Batches", data=f, file_name="compiled_batches.zip", mime="application/zip")

    st.success("Done!")
