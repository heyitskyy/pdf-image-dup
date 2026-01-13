from pathlib import Path
import fitz  # PyMuPDF
from typing import List, Tuple
from src.config import RENDER_DPI
from src.image_utils import safe_save_jpg

def extract_embedded_images(pdf_path: Path, out_dir: Path) -> List[Tuple[int, int, Path]]:
    """
    Return list: (page_number_1based, img_index_1based, saved_path)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved = []

    for page_i in range(len(doc)):
        page = doc[page_i]
        image_list = page.get_images(full=True)
        for img_i, img in enumerate(image_list):
            xref = img[0]
            base = doc.extract_image(xref)
            img_bytes = base["image"]
            ext = base.get("ext", "png")
            out_path = out_dir / f"embedded_p{page_i+1}_img{img_i+1}.{ext}"
            out_path.write_bytes(img_bytes)
            saved.append((page_i + 1, img_i + 1, out_path))

    doc.close()
    return saved

def render_pages_to_images(pdf_path: Path, out_dir: Path, dpi: int = RENDER_DPI) -> List[Tuple[int, int, Path]]:
    """
    Render each page as one image.
    Return list: (page_number_1based, img_index_1based(always 1), saved_path)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    saved = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for page_i in range(len(doc)):
        page = doc[page_i]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        # simpan sebagai JPG via PIL (lebih kecil daripada PNG)
        tmp_png = out_dir / f"_tmp_render_p{page_i+1}.png"
        pix.save(str(tmp_png))

        from PIL import Image
        img = Image.open(tmp_png).convert("RGB")
        out_path = out_dir / f"render_p{page_i+1}.jpg"
        safe_save_jpg(img, out_path, quality=92)
        tmp_png.unlink(missing_ok=True)

        saved.append((page_i + 1, 1, out_path))

    doc.close()
    return saved
