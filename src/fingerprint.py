from pathlib import Path
from typing import Tuple
from PIL import Image, ImageOps, ImageFilter
import imagehash

def _normalize_gray(img: Image.Image) -> Image.Image:
    """
    Normalisasi untuk hashing supaya lebih stabil terhadap perubahan brightness/contrast.
    """
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=2)
    # Samakan ukuran agar konsisten (mengurangi efek scaling/anti-alias)
    g = g.resize((512, 512))
    return g

def _edge_image(img: Image.Image) -> Image.Image:
    """
    Buat edge-map (struktur) biar tahan beda warna/brightness.
    """
    g = _normalize_gray(img)
    e = g.filter(ImageFilter.FIND_EDGES)
    e = ImageOps.autocontrast(e, cutoff=2)
    return e

def compute_hashes(image_path: Path) -> Tuple[str, str, str, int, int]:
    """
    return: (phash_hex, dhash_hex, ehash_hex, width, height)
    """
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    g = _normalize_gray(img)
    e = _edge_image(img)

    ph = imagehash.phash(g)
    dh = imagehash.dhash(g)
    eh = imagehash.phash(e)  # edge-hash

    return str(ph), str(dh), str(eh), w, h

def hamming_hex(hash1: str, hash2: str) -> int:
    return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)
