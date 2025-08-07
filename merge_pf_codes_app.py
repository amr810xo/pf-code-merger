import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import os

st.title("📄 PF Code PDF Merger (Clean + Print-Ready, 50 pages per download)")

# Upload inputs
csv_file = st.file_uploader("Upload PF Code CSV (must contain a 'PF Code' column)", type=["csv"])
pdf_files = st.file_uploader("Upload PF PDF files (named like PF01.pdf, PF02.pdf, etc.)", type=["pdf"], accept_multiple_files=True)

batch_size = 50  # pages per output

# Clean PDFs by reconstructing with PyPDF2 (no image rendering)
def clean_pdf(input_path, output_path):
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except Exception as e:
        raise RuntimeError(f"Error cleaning {input_path}: {e}")

# Process and clean all uploaded PDFs
def process_uploaded_pdfs(uploaded_files, cleaned_dir):
    os.makedirs(cleaned_dir, exist_ok=True)
    cleaned_paths = {}
    total_files = len(uploaded_files)
    progress = st.progress(0, text="Cleaning uploaded PDFs...")

    for i, uploaded_file in enumerate(uploaded_files):
        input_path = os.path.join(cleaned_dir, "original_" + uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.read())

        output_path = os.path.join(cleaned_dir, uploaded_file.name)
        try:
            clean_pdf(input_path, output_path)
            cleaned_paths[os.path.splitext(uploaded_file.name)[0]] = output_path
        except Exception as e:
            st.error(f"❌ Failed to clean {uploaded_file.name}: {e}")

        progress.progress((i + 1) / total_files, text=f"Cleaning PDF {i + 1} of {total_files}...")

    return cleaned_paths

# Main merge logic
if csv_file and pdf_files and st.button("🔄 Clean & Merge PDFs"):
    with st.spinner("Reading input and preparing..."):
        df = pd.read_csv(csv_file)
        if "PF Code" not in df.columns:
            st.error("CSV must contain a column named 'PF Code'.")
        else:
            pf_codes = df["PF Code"].tolist()
            temp_dir = tempfile.mkdtemp()
            cleaned_pdfs = process_uploaded_pdfs(pdf_files, temp_dir)

            total_pages = len(pf_codes)
            batch_count = (total_pages + batch_size - 1) // batch_size
            page_progress = st.progress(0, text="Merging cleaned pages...")

            for batch_num in range(batch_count):
                writer = PdfWriter()
                start = batch_num * batch_size
                end = min(start + batch_size, total_pages)
                batch_codes = pf_codes[start:end]

                for idx, code in enumerate(batch_codes):
                    pdf_path = cleaned_pdfs.get(code)
                    if pdf_path and os.path.exists(pdf_path):
                        try:
                            reader = PdfReader(pdf_path)
                            if reader.pages:
                                writer.add_page(reader.pages[0])
                            else:
                                st.warning(f"⚠ PDF for code {code} has no pages.")
                        except Exception as e:
                            st.warning(f"⚠ Error reading PDF for code {code}: {e}")
                    else:
                        st.warning(f"⚠ Missing PDF for code: {code}")

                    # Update batch progress
                    page_progress.progress((start + idx + 1) / total_pages, text=f"Merging page {start + idx + 1} of {total_pages}...")

                out_path = os.path.join(temp_dir, f"batch_{batch_num + 1}.pdf")
                with open(out_path, "wb") as f:
                    writer.write(f)

                # ✅ Avoid crash by keeping file in memory
                with open(out_path, "rb") as f:
                    file_bytes = f.read()

                st.download_button(
                    label=f"📥 Download Batch {batch_num + 1} ({len(batch_codes)} pages)",
                    data=file_bytes,
                    file_name=f"batch_{batch_num + 1}.pdf",
                    mime="application/pdf"
                )

    st.success("✅ All done! Download each batch above.")
