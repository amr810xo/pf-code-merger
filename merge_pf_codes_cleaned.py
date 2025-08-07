
import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os
import zipfile
import fitz  # PyMuPDF for cleaning PDFs

st.title("📄 PF Code PDF Merger (Clean + Print-Ready)")

csv_file = st.file_uploader("Upload PF Code CSV (e.g. pf_codes_verified_complete.csv)", type=["csv"])
pdf_files = st.file_uploader("Upload PF PDF files (e.g. PF01.pdf to PF26.pdf)", type=["pdf"], accept_multiple_files=True)

pages_per_batch = 100

def clean_pdf(input_path, output_path):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_pdf = fitz.open("pdf", fitz.Pixmap(pix).tobytes("pdf"))
        new_doc.insert_pdf(img_pdf)
    new_doc.save(output_path)
    new_doc.close()
    doc.close()

def process_uploaded_pdfs(uploaded_files, cleaned_dir):
    os.makedirs(cleaned_dir, exist_ok=True)
    cleaned_paths = {}
    for uploaded_file in uploaded_files:
        input_path = os.path.join(cleaned_dir, "original_" + uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())
        output_path = os.path.join(cleaned_dir, uploaded_file.name)
        try:
            clean_pdf(input_path, output_path)
            cleaned_paths[os.path.splitext(uploaded_file.name)[0]] = output_path
        except Exception as e:
            st.error(f"Failed to clean PDF: {uploaded_file.name} — {e}")
    return cleaned_paths

if csv_file and pdf_files and st.button("🔄 Clean & Merge PDFs"):
    with st.spinner("Processing PDFs and cleaning fonts..."):
        progress = st.progress(0)
        df = pd.read_csv(csv_file)
        if "PF Code" not in df.columns:
            st.error("CSV must contain a 'PF Code' column.")
        else:
            pf_codes = df["PF Code"].tolist()
            temp_dir = tempfile.mkdtemp()
            cleaned_pdfs = process_uploaded_pdfs(pdf_files, temp_dir)
            total_pages = len(pf_codes)
            batch_count = (total_pages + pages_per_batch - 1) // pages_per_batch
            output_paths = []

            for batch_num in range(batch_count):
                writer = PdfWriter()
                start = batch_num * pages_per_batch
                end = min(start + pages_per_batch, total_pages)
                batch_codes = pf_codes[start:end]

                for code in batch_codes:
                    pdf_path = cleaned_pdfs.get(code)
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            reader = PdfReader(pdf_path)
                            if reader.pages:
                                writer.add_page(reader.pages[0])
                            else:
                                st.warning(f"PDF for code {code} has no pages.")
                        except Exception as e:
                            st.warning(f"Error reading PDF for code {code}: {e}")
                    else:
                        st.warning(f"Missing PDF for code: {code}")

                out_path = os.path.join(temp_dir, f"compiled_batch_{batch_num + 1}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)
                output_paths.append(out_path)
                progress.progress((batch_num + 1) / batch_count)

            zip_path = os.path.join(temp_dir, "compiled_batches.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for path in output_paths:
                    zipf.write(path, arcname=os.path.basename(path))

            with open(zip_path, "rb") as f:
                st.download_button("📥 Download ZIP of Batches", data=f, file_name="compiled_batches.zip", mime="application/zip")

    st.success("Done! Your PDFs are cleaned and ready to print.")
