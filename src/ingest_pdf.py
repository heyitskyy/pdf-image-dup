from pathlib import Path
import shutil
import json
from typing import Dict, Any, List

from src.config import PDF_DIR, IMAGES_DIR, MIN_EMBEDDED_IMAGES_TO_SKIP_RENDER
from src.db import (
    init_db,
    insert_pdf,
    insert_image,
    insert_fingerprint,
    fetch_all_fingerprints,
    fetch_image_info
)
from src.pdf_extract import extract_embedded_images, render_pages_to_images
from src.fingerprint import compute_hashes
from src.matcher import find_best_match


def ingest_pdf(pdf_input_path: Path) -> Dict[str, Any]:
    init_db()

    if not pdf_input_path.exists():
        raise FileNotFoundError(f"PDF tidak ditemukan: {pdf_input_path}")

    PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Simpan file PDF ke storage/pdfs
    stored_pdf_path = PDF_DIR / pdf_input_path.name
    shutil.copy2(pdf_input_path, stored_pdf_path)

    pdf_id = insert_pdf(pdf_input_path.name, str(stored_pdf_path))

    # Output folder image untuk PDF ini
    out_dir = IMAGES_DIR / f"pdf_{pdf_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) coba embedded images
    embedded = extract_embedded_images(stored_pdf_path, out_dir)

    # 2) kalau embedded kosong/kurang, fallback render pages
    if len(embedded) >= MIN_EMBEDDED_IMAGES_TO_SKIP_RENDER:
        extracted = [("embedded", p, idx, path) for (p, idx, path) in embedded]
    else:
        rendered = render_pages_to_images(stored_pdf_path, out_dir)
        extracted = [("render", p, idx, path) for (p, idx, path) in rendered]

    # Ambil semua fingerprint yang sudah ada di DB (sebelum PDF ini dimasukkan)
    existing_fps = fetch_all_fingerprints()

    results: List[Dict[str, Any]] = []

    for source, page, img_index, img_path in extracted:
        # UPDATED: compute_hashes sekarang return (phash, dhash, ehash, w, h)
        phash, dhash, ehash, w, h = compute_hashes(img_path)

        # UPDATED: matcher menerima ehash juga
        match = find_best_match(phash, dhash, ehash, existing_fps)

        # Simpan image + fingerprint untuk PDF baru ke DB (jadi referensi ke depannya)
        image_id = insert_image(pdf_id, page, source, img_index, str(img_path), w, h)
        insert_fingerprint(image_id, phash, dhash, ehash)

        item: Dict[str, Any] = {
            "page": int(page),
            "source": source,
            "img_index": int(img_index),
            "img_path": str(img_path),
            "phash": phash,
            "dhash": dhash,
            "ehash": ehash,
            "is_duplicate": match is not None,
            "match": None
        }

        if match:
            info = fetch_image_info(match["image_id"])
            # info: (images.id, pdf_id, page, source, img_index, img_path, pdf_filename)
            if info:
                item["match"] = {
                    "score": int(match["score"]),
                    "phash_dist": int(match["phash_dist"]),
                    "dhash_dist": int(match["dhash_dist"]),
                    "ehash_dist": int(match["ehash_dist"]),
                    "old_pdf_id": int(info[1]),
                    "old_pdf_filename": info[6],
                    "old_page": int(info[2]),
                    "old_source": info[3],
                    "old_img_index": int(info[4]),
                    "old_img_path": info[5],
                }

        results.append(item)

    report = {
        "pdf_id": int(pdf_id),
        "pdf_filename": pdf_input_path.name,
        "stored_pdf_path": str(stored_pdf_path),
        "num_images_processed": len(results),
        "results": results
    }

    # simpan report json biar gampang dicek
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


def print_report(report: Dict[str, Any]) -> None:
    print(f"\nPDF: {report['pdf_filename']} (pdf_id={report['pdf_id']})")
    print(f"Images processed: {report['num_images_processed']}")
    print("-" * 60)

    for r in report["results"]:
        if r["is_duplicate"]:
            m = r["match"]
            print(f"[DUP] page {r['page']} ({r['source']}) -> {Path(r['img_path']).name}")
            print(
                f"     score={m['score']} "
                f"(ph={m['phash_dist']}, dh={m['dhash_dist']}, eh={m['ehash_dist']})"
            )
            print(
                f"     pernah ada di: {m['old_pdf_filename']} "
                f"(pdf_id={m['old_pdf_id']}), page {m['old_page']}, img {m['old_img_index']}"
            )
        else:
            print(f"[NEW] page {r['page']} ({r['source']}) -> {Path(r['img_path']).name}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print('Usage: py src\\ingest_pdf.py "D:\\path\\file.pdf"')
        raise SystemExit(1)

    pdf_path = Path(sys.argv[1])
    rep = ingest_pdf(pdf_path)
    print_report(rep)
    print("\nReport JSON tersimpan di folder storage/images/pdf_<id>/report.json")
