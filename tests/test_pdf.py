import subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent


def test_pdf_builds_from_markdown():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_pdf.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    pdf = ROOT / "output" / "FORGE_STAR_Strategy.pdf"
    assert pdf.stat().st_size > 50_000
