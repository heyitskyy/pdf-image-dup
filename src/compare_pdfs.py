from __future__ import annotations

from pathlib import Path
from uuid import uuid4
from typing import Dict, Any, List, Tuple

from src.config import MIN_EMBEDDED_IMAGES_TO_SKIP_RENDER
from src.pdf_extract import extract_embedded_images, render_pages_to_images
from src.fingerprint import compute_hashes
from src.matcher import find_best_match


def _extract_images_for_compare(pdf_path: Path, out_dir: Path) -> List[Tuple[str, int, int, Path]]:
    out_dir.mkdir(parents=True, exist_ok=True)

    embedded = extract_embedded_images(pdf_path, out_dir)
    if len(embedded) >= MIN_EMBEDDED_IMAGES_TO_SKIP_RENDER:
        return [("embedded", p, idx, path) for (p, idx, path) in embedded]

    rendered = render_pages_to_images(pdf_path, out_dir)
    return [("render", p, idx, path) for (p, idx, path) in rendered]


def compare_pdfs(pdf_a_path: Path, pdf_b_path: Path) -> Dict[str, Any]:
    if not pdf_a_path.exists():
        raise FileNotFoundError(f"PDF A tidak ditemukan: {pdf_a_path}")
    if not pdf_b_path.exists():
        raise FileNotFoundError(f"PDF B tidak ditemukan: {pdf_b_path}")

    run_id = uuid4().hex
    base_dir = Path("storage/compare") / f"run_{run_id}"
    out_a = base_dir / "A"
    out_b = base_dir / "B"

    extracted_a = _extract_images_for_compare(pdf_a_path, out_a)
    extracted_b = _extract_images_for_compare(pdf_b_path, out_b)

    # existing_fps format: (fingerprint_id, image_id, phash, dhash, ehash)
    b_items: List[Dict[str, Any]] = []
    existing_fps: List[Tuple[int, int, str, str, str]] = []

    for j, (source, page, img_index, img_path) in enumerate(extracted_b, start=1):
        ph, dh, eh, w, h = compute_hashes(img_path)
        image_id_fake = j
        fp_id_fake = j
        b_items.append({
            "image_id": image_id_fake,
            "page": int(page),
            "source": source,
            "img_index": int(img_index),
            "img_path": str(img_path),
        })
        existing_fps.append((fp_id_fake, image_id_fake, ph, dh, eh))

    b_lookup = {it["image_id"]: it for it in b_items}

    results: List[Dict[str, Any]] = []
    for i, (source, page, img_index, img_path) in enumerate(extracted_a, start=1):
        ph, dh, eh, w, h = compute_hashes(img_path)

        match = find_best_match(ph, dh, eh, existing_fps)

        item: Dict[str, Any] = {
            "page": int(page),
            "source": source,
            "img_index": int(img_index),
            "img_path": str(img_path),
            "is_match": match is not None,
            "match": None
        }

        if match is not None:
            binfo = b_lookup.get(match["image_id"])
            item["match"] = {
                "score": int(match["score"]),
                "phash_dist": int(match["phash_dist"]),
                "dhash_dist": int(match["dhash_dist"]),
                "ehash_dist": int(match["ehash_dist"]),
                "b_page": int(binfo["page"]) if binfo else None,
                "b_source": binfo["source"] if binfo else None,
                "b_img_index": int(binfo["img_index"]) if binfo else None,
                "b_img_path": binfo["img_path"] if binfo else None,
            }

        results.append(item)

    return {
        "run_id": run_id,
        "pdf_a": str(pdf_a_path),
        "pdf_b": str(pdf_b_path),
        "num_images_a": len(extracted_a),
        "num_images_b": len(extracted_b),
        "results": results,
        "compare_output_dir": str(base_dir),
    }
