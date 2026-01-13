import sqlite3
from pathlib import Path
from typing import Iterable, Optional, Tuple, List
from src.config import DB_PATH, STORAGE_DIR

def get_conn() -> sqlite3.Connection:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # WAL lebih aman untuk akses bersamaan ringan
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pdf_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        uploaded_at TEXT DEFAULT (datetime('now'))
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_id INTEGER NOT NULL,
        page INTEGER NOT NULL,
        source TEXT NOT NULL,             -- 'embedded' atau 'render'
        img_index INTEGER NOT NULL,        -- index di halaman / hasil render
        img_path TEXT NOT NULL,
        width INTEGER,
        height INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(pdf_id) REFERENCES pdf_files(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fingerprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER NOT NULL,
        phash TEXT NOT NULL,
        dhash TEXT NOT NULL,
        ehash TEXT NOT NULL,
        FOREIGN KEY(image_id) REFERENCES images(id)
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_ehash ON fingerprints(ehash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_phash ON fingerprints(phash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fingerprints_dhash ON fingerprints(dhash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_images_pdf_id ON images(pdf_id)")

    conn.commit()
    conn.close()

def insert_pdf(filename: str, stored_path: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO pdf_files(filename, stored_path) VALUES(?, ?)", (filename, stored_path))
    conn.commit()
    pdf_id = cur.lastrowid
    conn.close()
    return pdf_id

def insert_image(pdf_id: int, page: int, source: str, img_index: int, img_path: str, w: int, h: int) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO images(pdf_id, page, source, img_index, img_path, width, height)
        VALUES(?,?,?,?,?,?,?)
    """, (pdf_id, page, source, img_index, img_path, w, h))
    conn.commit()
    image_id = cur.lastrowid
    conn.close()
    return image_id

def insert_fingerprint(image_id: int, phash: str, dhash: str, ehash: str) -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fingerprints(image_id, phash, dhash, ehash)
        VALUES(?,?,?,?)
    """, (image_id, phash, dhash, ehash))
    conn.commit()
    conn.close()

def fetch_all_fingerprints() -> List[Tuple[int, int, str, str]]:
    """
    return: list of (fingerprint_id, image_id, phash, dhash)
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, image_id, phash, dhash, ehash FROM fingerprints")
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_image_info(image_id: int) -> Optional[Tuple]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT images.id, images.pdf_id, images.page, images.source, images.img_index, images.img_path,
               pdf_files.filename
        FROM images
        JOIN pdf_files ON pdf_files.id = images.pdf_id
        WHERE images.id = ?
    """, (image_id,))
    row = cur.fetchone()
    conn.close()
    return row
