from pathlib import Path
from typing import List, Dict, Any
import sys
import traceback

from ingest_pdf import ingest_pdf, print_report


def find_pdfs(folder: Path, recursive: bool = True) -> List[Path]:
    if recursive:
        return sorted(folder.rglob("*.pdf"))
    return sorted(folder.glob("*.pdf"))


def summarize_report(report: Dict[str, Any]) -> Dict[str, int]:
    """
    Mengembalikan ringkasan sederhana dari 1 report ingest:
    - num_images: total images diproses
    - num_dup: berapa yang duplicate
    - num_new: berapa yang new
    """
    results = report.get("results", [])
    num_images = len(results)
    num_dup = sum(1 for r in results if r.get("is_duplicate"))
    num_new = num_images - num_dup
    return {"num_images": num_images, "num_dup": num_dup, "num_new": num_new}


def main():
    if len(sys.argv) < 2:
        print('Usage: py src\\ingest_folder.py "D:\\DatasetPDF" [--no-recursive]')
        raise SystemExit(1)

    folder = Path(sys.argv[1])
    recursive = True
    if len(sys.argv) >= 3 and sys.argv[2].strip().lower() == "--no-recursive":
        recursive = False

    if not folder.exists() or not folder.is_dir():
        print(f"Folder tidak ditemukan / bukan folder: {folder}")
        raise SystemExit(1)

    pdfs = find_pdfs(folder, recursive=recursive)
    if not pdfs:
        print(f"Tidak ada file .pdf di folder: {folder}")
        return

    print(f"Menemukan {len(pdfs)} PDF di: {folder} (recursive={recursive})")
    print("=" * 70)

    success = 0
    failed = 0
    total_images = 0
    total_dup = 0
    total_new = 0

    failed_files: List[str] = []

    for i, pdf_path in enumerate(pdfs, start=1):
        print(f"\n[{i}/{len(pdfs)}] Ingest: {pdf_path}")
        try:
            report = ingest_pdf(pdf_path)
            # Optional: tampilkan report per file (bisa kamu matikan kalau kebanyakan output)
            print_report(report)

            s = summarize_report(report)
            success += 1
            total_images += s["num_images"]
            total_dup += s["num_dup"]
            total_new += s["num_new"]

        except Exception as e:
            failed += 1
            failed_files.append(str(pdf_path))
            print("!! GAGAL ingest PDF ini:")
            print(f"   {e}")
            # supaya tetap stable, kita lanjut file berikutnya
            # kalau mau log detail stacktrace:
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("RINGKASAN INGEST FOLDER")
    print(f"Folder          : {folder}")
    print(f"Total PDF        : {len(pdfs)}")
    print(f"Sukses           : {success}")
    print(f"Gagal            : {failed}")
    print(f"Total images     : {total_images}")
    print(f"Total DUP        : {total_dup}")
    print(f"Total NEW        : {total_new}")

    if failed_files:
        print("\nDaftar PDF yang gagal:")
        for f in failed_files:
            print(f"- {f}")


if __name__ == "__main__":
    main()
