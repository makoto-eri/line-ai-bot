"""Vertically stitch LINE conversation screenshots into single images per Q&A.

Run once from repo root:
    .venv/Scripts/python.exe scripts/stitch_screenshots.py
"""

from pathlib import Path

from PIL import Image

SOURCE_DIR = Path("C:/Users/えりっぺ/OneDrive/画像/スクリーンショット")
DEST_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


GROUPS = {
    "q1_excel_lookup.png": [
        "スクリーンショット 2026-04-24 105016.png",
        "スクリーンショット 2026-04-24 105103.png",
        "スクリーンショット 2026-04-24 105251.png",
        "スクリーンショット 2026-04-24 105334.png",
    ],
    "q2_team_leader.png": [
        "スクリーンショット 2026-04-24 105454.png",
        "スクリーンショット 2026-04-24 105541.png",
        "スクリーンショット 2026-04-24 105708.png",
        "スクリーンショット 2026-04-24 105743.png",
    ],
    "q3_apology_email.png": [
        "スクリーンショット 2026-04-24 105851.png",
        "スクリーンショット 2026-04-24 105942.png",
        "スクリーンショット 2026-04-24 110017.png",
        "スクリーンショット 2026-04-24 110047.png",
    ],
}


def stitch(paths: list[Path]) -> Image.Image:
    images = [Image.open(p).convert("RGB") for p in paths]
    width = max(img.width for img in images)
    normalized = []
    for img in images:
        if img.width != width:
            ratio = width / img.width
            new_size = (width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        normalized.append(img)
    total_height = sum(img.height for img in normalized)
    canvas = Image.new("RGB", (width, total_height), (28, 28, 28))
    y = 0
    for img in normalized:
        canvas.paste(img, (0, y))
        y += img.height
    return canvas


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for out_name, src_names in GROUPS.items():
        src_paths = [SOURCE_DIR / name for name in src_names]
        missing = [p for p in src_paths if not p.exists()]
        if missing:
            raise FileNotFoundError(f"missing: {missing}")
        combined = stitch(src_paths)
        out_path = DEST_DIR / out_name
        combined.save(out_path, "PNG", optimize=True)
        print(f"wrote {out_path} ({combined.size[0]}x{combined.size[1]})")


if __name__ == "__main__":
    main()
