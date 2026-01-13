from pathlib import Path
from uuid import uuid4
import json

import pandas as pd
import streamlit as st

from src.ingest_pdf import ingest_pdf

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="PDF Image Duplicate Checker",
    layout="wide"
)

st.title("📄🖼️ PDF Image Duplicate Checker")
st.caption("Upload PDF → extract gambar → cek duplicate vs database PDF sebelumnya (SQLite + folder lokal).")

# Sidebar controls
st.sidebar.header("⚙️ Pengaturan Tampilan")
show_only_dup = st.sidebar.checkbox("Tampilkan hanya DUP", value=False)
show_previews = st.sidebar.checkbox("Tampilkan preview gambar", value=True)
max_preview_rows = st.sidebar.slider("Maks baris preview", min_value=1, max_value=50, value=10)

st.sidebar.divider()
st.sidebar.caption("Catatan: Proses bisa agak lama jika PDF scan (render halaman).")

uploaded = st.file_uploader("Upload file PDF", type=["pdf"])

def safe_image_show(path: str, caption: str):
    try:
        p = Path(path)
        if p.exists():
            st.image(str(p), caption=caption, use_container_width=True)
        else:
            st.warning(f"Gambar tidak ditemukan: {p}")
    except Exception as e:
        st.warning(f"Gagal menampilkan gambar: {e}")

if uploaded is None:
    st.info("Silakan upload PDF untuk mulai.")
    st.stop()

# Save uploaded file
tmp_name = f"{uuid4().hex}_{Path(uploaded.name).name}"
tmp_path = UPLOAD_DIR / tmp_name
tmp_path.write_bytes(uploaded.getbuffer())

st.success(f"File diterima: {uploaded.name}")
with st.spinner("Memproses PDF... (extract + hashing + matching)"):
    report = ingest_pdf(tmp_path)

# Summary
pdf_id = report.get("pdf_id")
pdf_name = report.get("pdf_filename")
num_images = report.get("num_images_processed", 0)
results = report.get("results", [])

num_dup = sum(1 for r in results if r.get("is_duplicate"))
num_new = num_images - num_dup

c1, c2, c3, c4 = st.columns(4)
c1.metric("PDF ID", pdf_id)
c2.metric("Total Images", num_images)
c3.metric("Duplicate (DUP)", num_dup)
c4.metric("New", num_new)

st.divider()

# Build table
rows = []
for r in results:
    m = r.get("match") or {}
    rows.append({
        "status": "DUP" if r.get("is_duplicate") else "NEW",
        "page": r.get("page"),
        "source": r.get("source"),
        "img_path": r.get("img_path"),
        "old_pdf": m.get("old_pdf_filename"),
        "old_page": m.get("old_page"),
        "score": m.get("score"),
        "phash_dist": m.get("phash_dist"),
        "dhash_dist": m.get("dhash_dist"),
        "ehash_dist": m.get("ehash_dist"),
        "old_img_path": m.get("old_img_path"),
    })

df = pd.DataFrame(rows)

if show_only_dup:
    df_view = df[df["status"] == "DUP"].copy()
else:
    df_view = df.copy()

st.subheader("📋 Hasil Deteksi")
st.dataframe(df_view, use_container_width=True)

# Download JSON report
st.download_button(
    label="⬇️ Download report.json",
    data=json.dumps(report, indent=2).encode("utf-8"),
    file_name=f"report_pdf_{pdf_id}.json",
    mime="application/json"
)

# Preview section
if show_previews:
    st.divider()
    st.subheader("🖼️ Preview (contoh)")

    # limit number of preview rows
    preview_df = df_view.head(max_preview_rows)

    if len(preview_df) == 0:
        st.info("Tidak ada data untuk dipreview (coba matikan filter hanya DUP).")
    else:
        for _, row in preview_df.iterrows():
            status = row["status"]
            page = row["page"]
            src = row["source"]
            img_path = row["img_path"]

            st.markdown(f"**{status}** | page **{page}** | source **{src}** | `{Path(img_path).name}`")

            if status == "DUP":
                old_pdf = row["old_pdf"]
                old_page = row["old_page"]
                score = row["score"]
                ph = row["phash_dist"]
                dh = row["dhash_dist"]
                eh = row["ehash_dist"]
                old_img_path = row["old_img_path"]

                st.caption(f"Match ke: {old_pdf} (page {old_page}) | score={score} | ph={ph}, dh={dh}, eh={eh}")

                colA, colB = st.columns(2)
                with colA:
                    safe_image_show(img_path, "Gambar (PDF baru)")
                with colB:
                    if old_img_path:
                        safe_image_show(old_img_path, "Gambar referensi (PDF lama)")
                    else:
                        st.info("Tidak ada path gambar referensi.")
            else:
                safe_image_show(img_path, "Gambar (PDF baru)")

            st.markdown("---")
