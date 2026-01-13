import sys
from pathlib import Path
import subprocess

def usage():
    print("""
Usage:
  py run.py file   "C:\\path\\to\\file.pdf"
  py run.py folder "D:\\DatasetPDF" [--no-recursive]
  py run.py ui

Commands:
  file    Ingest 1 PDF
  folder  Ingest semua PDF dalam folder
  ui      Jalankan Streamlit dashboard
""".strip())

def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "file":
        if len(sys.argv) < 3:
            usage(); sys.exit(1)
        pdf = sys.argv[2]
        subprocess.check_call([sys.executable, str(Path("src") / "ingest_pdf.py"), pdf])

    elif cmd == "folder":
        if len(sys.argv) < 3:
            usage(); sys.exit(1)
        folder = sys.argv[2]
        extra = sys.argv[3:]  # bisa berisi --no-recursive
        subprocess.check_call([sys.executable, str(Path("src") / "ingest_folder.py"), folder, *extra])

    elif cmd in ("ui", "streamlit"):
        subprocess.check_call([sys.executable, "-m", "streamlit", "run", str(Path("src") / "streamlit_app.py")])

    else:
        usage()
        sys.exit(1)

if __name__ == "__main__":
    main()
