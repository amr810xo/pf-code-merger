import streamlit as st
import fitz  # PyMuPDF
import os
import tempfile
from PyPDF2 import PdfReader, PdfWriter
import pandas as pd
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="PF Code PDF Merger", layout="centered")

st.title("📄 PF Code PDF Merger (Print-Safe)")
st.markdown("Upload your CSV of PF codes and matching PDFs. The app will generate a merged, printer-friendly PDF in 100-page batches.")

# Function to clean PDFs for printing
def clean_pdf(input_path, output_path):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)
        temp_img_path = f"{output_path}_page{i}.png"
        pix.save(temp_img_path)
        img_rect = fitz.Rect(0, 0, pix.width, pix.height)
        img_pdf = fitz.open()
        img_page = img_pdf.new_page(width=pix.width, height=pix.height)
        img_page.insert_image(img_rect, filename=temp_img_path)
        new_doc.insert_pdf(img_pdf)
        os.remove(temp_img_path)
    new_doc.save(output_path)
    new_doc.close()
    doc.close()

# Process uploaded PDFs and clean them
def process_uploaded_pdfs(uploaded_pdfs, temp_dir):
    cleaned_paths = {}
    for uploaded_file in uploaded_pdfs:
        filename = uploaded_file.name
        pf_code = os.path.splitext(filename)[0]
        input_path = os.path.join(temp_dir, filename)
        output_path = os.path.join(temp_dir, f"{pf_code}_cleaned.pdf")

        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        clean_pdf(input_path, output_path)
        cleaned_paths[pf_code] = output_path
    return cleaned_paths

# Merge PDFs based on CSV order
def merge_pdfs_by_csv(csv_file, cleaned_pdf_paths):
    csv_codes = pd.read_csv(csv_file, header=None)[0].tolist()

    batches = []
    current_batch = PdfWriter()
    batch_counter = 1
    files_output = []

    for idx, pf_code in enumerate(csv_codes):
        if pf_code not in cleaned_pdf_paths:
            continue  # skip missing codes

        pdf_path = cleaned_pdf_paths[pf_code]
        reader = PdfReader(pdf_path)
        current_batch.add_page(reader.pages[0])

        if (idx + 1) % 100 == 0 or idx == len(csv_codes) - 1:
            output_pdf = BytesIO()
            current_batch.write(output_pdf)
            output_pdf.seek(0)
            batches.append((f"Batch_{batch_counter}.pdf", output_pdf))
            batch_counter += 1
            current_batch = PdfWriter()

    return batches

# --- Streamlit UI ---
csv_file = st.file_uploader("Upload PF Code CSV", type=["csv"])
pdf_files = st.file_uploader("Upload PF Code PDFs", type=["pdf"], accept_multiple_files=True)

if csv_file and pdf_files:
    with st.spinner("Processing PDFs..."):
        with tempfile.TemporaryDirectory() as temp_dir:
            cleaned_pdfs = process_uploaded_pdfs(pdf_files, temp_dir)
            merged_batches = merge_pdfs_by_csv(csv_file, cleaned_pdfs)

            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for filename, batch in merged_batches:
                    zip_file.writestr(filename, batch.getvalue())
            zip_buffer.seek(0)

            st.success("PDFs merged and cleaned successfully!")
            st.download_button(
                label="📦 Download ZIP of Merged Batches",
                data=zip_buffer,
                file_name="merged_pf_batches.zip",
                mime="application/zip"
            )
