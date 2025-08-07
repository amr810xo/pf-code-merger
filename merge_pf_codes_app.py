import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os
import fitz  # PyMuPDF for cleaning PDFs

st.title("📄 PF Code PDF Merger (Clean + Print-Ready, 50 pages per download)")

# Upload CSV
csv_file = st.file_uploader("Upload PF Code CSV (e.g. pf_codes_verified_complete.csv)", type=["csv"])

# Upload PDFs
pdf_files = st.file_uploader("Upload PF PDF files (e.g. PF01.pdf to PF26.pdf)", type=["pdf"], accept_multiple_files=True)

# Batch size
batch_size = 50

def clean_pdf(input_path, output_path):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    for page in doc:
        pix = page.get_pixmap(dpi=150)  # lower DPI to save memory
        img_page = new_doc.new_page(width=pix.width, height=pix.height)
        img_page.insert_image(img_page.rect, pixmap=pix)
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
        df = pd.read_csv(csv_file)
        if "PF Code" not in df.columns:
            st.error("CSV must contain a 'PF Code' column.")
        else:
            pf_codes = df["PF Code"].tolist()
            temp_dir = tempfile.mkdtemp()
            cleaned_pdfs = process_uploaded_pdfs(pdf_files, temp_dir)
            total_pages = len(pf_codes)
            batch_count = (total_pages + batch_size - 1) // batch_size

            for batch_num in range(batch_count):
                writer = PdfWriter()
                start = batch_num * batch_size
                end = min(start + batch_size, total_pages)
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

                out_path = os.path.join(temp_dir, f"batch_{batch_num + 1}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)

                with open(out_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download Batch {batch_num + 1} ({len(batch_codes)} pages)",
                        data=f,
                        file_name=f"batch_{batch_num + 1}.pdf",
                        mime="application/pdf"
                    )

    st.success("All done! Download each batch above.")
