from typing import Optional, Dict, Any, List, Tuple
from src.fingerprint import hamming_hex
from src.config import PHASH_THRESHOLD, DHASH_THRESHOLD

EHASH_THRESHOLD = 10  # bisa kamu tuning

def find_best_match(new_phash, new_dhash, new_ehash, existing):
    """
    existing: list of (fp_id, image_id, phash, dhash, ehash)
    """
    best = None

    for fp_id, img_id, ph, dh, eh in existing:
        d_ph = hamming_hex(new_phash, ph)
        d_dh = hamming_hex(new_dhash, dh)
        d_eh = hamming_hex(new_ehash, eh)

        # Aturan: kalau edge mirip, anggap kandidat kuat
        ok = (d_eh <= EHASH_THRESHOLD) or ((d_ph <= PHASH_THRESHOLD) and (d_dh <= DHASH_THRESHOLD))
        if not ok:
            continue

        score = min(d_eh, d_ph + d_dh)  # pakai yang “lebih meyakinkan”
        if best is None or score < best["score"]:
            best = {
                "fingerprint_id": fp_id,
                "image_id": img_id,
                "phash_dist": d_ph,
                "dhash_dist": d_dh,
                "ehash_dist": d_eh,
                "score": score
            }

    return best
