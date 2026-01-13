from pathlib import Path

# Folder storage
STORAGE_DIR = Path("storage")
PDF_DIR = STORAGE_DIR / "pdfs"
IMAGES_DIR = STORAGE_DIR / "images"
DB_PATH = STORAGE_DIR / "app.db"

# Extract/render settings
RENDER_DPI = 200  # naikkan ke 300 kalau butuh lebih detail (lebih berat)
MIN_EMBEDDED_IMAGES_TO_SKIP_RENDER = 1  # kalau embedded >= ini, kita tidak render halaman

# Matching thresholds (awal, nanti tuning)
PHASH_THRESHOLD = 8   # 0 = identik, makin besar makin longgar
DHASH_THRESHOLD = 10  # tambahan untuk bantu robustness ringan
