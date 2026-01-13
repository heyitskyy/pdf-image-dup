from PIL import Image
from pathlib import Path

def open_image_rgb(path: Path) -> Image.Image:
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img

def safe_save_jpg(img: Image.Image, out_path: Path, quality: int = 92) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="JPEG", quality=quality, optimize=True)
