from pathlib import Path
from uuid import uuid4
from typing import Any, Dict

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse

# pakai fungsi ingest yang sudah kamu punya
from src.ingest_pdf import ingest_pdf

app = FastAPI(title="PDF Image Duplicate Checker")

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _html_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;")
             .replace("'", "&#39;"))


@app.get("/", response_class=HTMLResponse)
def home():
    # Upload form sederhana
    return """
    <html>
      <head>
        <title>PDF Image Duplicate Checker</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; }
          .box { max-width: 720px; padding: 16px; border: 1px solid #ddd; border-radius: 10px; }
          button { padding: 10px 16px; cursor: pointer; }
          input { padding: 8px; width: 100%; }
          .hint { color: #666; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="box">
          <h2>Upload PDF</h2>
          <p class="hint">Upload PDF baru untuk dicek apakah gambar di dalamnya sudah pernah ada.</p>
          <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="pdf" accept="application/pdf" required />
            <br/><br/>
            <button type="submit">Proses</button>
          </form>
          <hr/>
          <p class="hint">Kalau mau hasil JSON: POST ke <code>/api/upload</code></p>
        </div>
      </body>
    </html>
    """


@app.post("/api/upload")
async def api_upload(pdf: UploadFile = File(...)) -> JSONResponse:
    if not pdf.filename.lower().endswith(".pdf"):
        return JSONResponse({"error": "File harus .pdf"}, status_code=400)

    # simpan file upload sementara
    safe_name = f"{uuid4().hex}_{Path(pdf.filename).name}"
    tmp_path = UPLOAD_DIR / safe_name

    content = await pdf.read()
    tmp_path.write_bytes(content)

    # proses pakai pipeline kamu
    report: Dict[str, Any] = ingest_pdf(tmp_path)

    return JSONResponse(report)


@app.post("/upload", response_class=HTMLResponse)
async def upload(pdf: UploadFile = File(...)) -> HTMLResponse:
    if not pdf.filename.lower().endswith(".pdf"):
        return HTMLResponse("<h3>Error: File harus PDF</h3>", status_code=400)

    # simpan file upload sementara
    safe_name = f"{uuid4().hex}_{Path(pdf.filename).name}"
    tmp_path = UPLOAD_DIR / safe_name

    content = await pdf.read()
    tmp_path.write_bytes(content)

    # proses pipeline
    report: Dict[str, Any] = ingest_pdf(tmp_path)

    # render hasil ke HTML
    pdf_name = _html_escape(report.get("pdf_filename", ""))
    pdf_id = report.get("pdf_id", "")
    num_images = report.get("num_images_processed", 0)

    results = report.get("results", [])

    # hitung ringkasan
    num_dup = sum(1 for r in results if r.get("is_duplicate"))
    num_new = num_images - num_dup

    rows = []
    for r in results:
        img_name = _html_escape(Path(r["img_path"]).name)
        page = r.get("page")
        src = _html_escape(r.get("source", ""))

        if r.get("is_duplicate"):
            m = r.get("match") or {}
            old_pdf = _html_escape(m.get("old_pdf_filename", ""))
            old_page = m.get("old_page", "")
            score = m.get("score", "")
            ph = m.get("phash_dist", "")
            dh = m.get("dhash_dist", "")
            eh = m.get("ehash_dist", "")

            rows.append(f"""
            <tr>
              <td>DUP</td>
              <td>{page}</td>
              <td>{src}</td>
              <td>{img_name}</td>
              <td>{old_pdf} (page {old_page})</td>
              <td>score={score} | ph={ph} dh={dh} eh={eh}</td>
            </tr>
            """)
        else:
            rows.append(f"""
            <tr>
              <td>NEW</td>
              <td>{page}</td>
              <td>{src}</td>
              <td>{img_name}</td>
              <td>-</td>
              <td>-</td>
            </tr>
            """)

    table_html = "\n".join(rows)

    return HTMLResponse(f"""
    <html>
      <head>
        <title>Hasil - {pdf_name}</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 40px; }}
          .box {{ max-width: 1100px; padding: 16px; border: 1px solid #ddd; border-radius: 10px; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 14px; }}
          th {{ background: #f7f7f7; text-align: left; }}
          .meta {{ color: #333; }}
          a {{ text-decoration: none; }}
        </style>
      </head>
      <body>
        <div class="box">
          <h2>Hasil Deteksi</h2>
          <p class="meta">
            PDF: <b>{pdf_name}</b> | pdf_id={pdf_id} <br/>
            Total images: <b>{num_images}</b> | DUP: <b>{num_dup}</b> | NEW: <b>{num_new}</b>
          </p>
          <p>
            <a href="/">← Upload lagi</a>
          </p>
          <table>
            <thead>
              <tr>
                <th>Status</th>
                <th>Page</th>
                <th>Source</th>
                <th>Image</th>
                <th>Matched To</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {table_html}
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """)
