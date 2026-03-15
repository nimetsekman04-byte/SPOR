import sys
import json
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def extract_text_pdf(pdf_path: Path) -> str:
    """Try text-based extraction first; fallback done in process_file."""
    with pdfplumber.open(pdf_path) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    return text


def extract_text_image(img_path: Path, lang: str = "tur") -> str:
    return pytesseract.image_to_string(Image.open(img_path), lang=lang)


def normalize_text(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s:
            lines.append(s)
    # Basic line joining; keep empty lines out
    return "\n".join(lines)


def process_file(file_path: Path, processed_dir: Path, lang: str = "tur"):
    base = file_path.stem
    out_txt = processed_dir / f"{base}.txt"
    meta = {"source_file": str(file_path), "output_text": str(out_txt)}

    if file_path.suffix.lower() == ".pdf":
        text = extract_text_pdf(file_path)
        if not text.strip():
            pages = convert_from_path(file_path)
            text = "\n\n".join(extract_text_image(p, lang=lang) for p in pages)
    else:
        text = extract_text_image(file_path, lang=lang)

    out_txt.write_text(normalize_text(text), encoding="utf-8")
    (processed_dir / f"{base}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_txt


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python scripts/process_articles.py datasets/raw")
        sys.exit(1)

    raw_dir = Path(sys.argv[1])
    if not raw_dir.exists():
        print(f"Bulunamadı: {raw_dir}")
        sys.exit(1)

    processed_dir = Path("datasets/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    files = [p for p in raw_dir.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED]
    if not files:
        print("İşlenecek dosya yok.")
        sys.exit(0)

    for path in files:
        try:
            out = process_file(path, processed_dir)
            print("OK", path, "->", out)
        except Exception as e:
            print("HATA", path, e, file=sys.stderr)


if __name__ == "__main__":
    main()
