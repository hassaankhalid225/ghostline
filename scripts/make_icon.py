"""Render the Ghostline logo: assets/icon.ico (PyInstaller), docs/logo.png and docs/logo.svg (README).

The drawing lives in ``ui/theme.py`` (``paint_logo``) so the window, tray icon, .ico and README
logo always match.

    python scripts/make_icon.py
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402

from ghostline.ui import theme  # noqa: E402

ICO = ROOT / "assets" / "icon.ico"
PNG = ROOT / "docs" / "logo.png"
SVG = ROOT / "docs" / "logo.svg"
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def render(size: int, tile: bool = True) -> Image.Image:
    img = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    inset = 0 if size >= 32 else 0.5           # keep the tile edge crisp at tiny sizes
    theme.paint_logo(p, QRectF(inset, inset, size - 2 * inset, size - 2 * inset), tile)
    p.end()
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


def svg(size: int = 256) -> str:
    s = size
    hx, hy, d = theme.GHOST_HEAD
    left, right, r = hx * s, (hx + d) * s, d * s / 2
    step = d * s / 3
    tail = "".join(f" Q{right - i * step - step / 2:.2f},{theme.GHOST_NOTCH * s:.2f}"
                   f" {right - (i + 1) * step:.2f},{theme.GHOST_BOTTOM * s:.2f}" for i in range(3))
    ghost = (f"M{left:.2f},{(hy + d / 2) * s:.2f} A{r:.2f},{r:.2f} 0 0 1 {right:.2f},{(hy + d / 2) * s:.2f}"
             f" L{right:.2f},{theme.GHOST_BOTTOM * s:.2f}{tail} Z")
    lines = "".join(f'<line x1="{x * s:.2f}" y1="{y * s:.2f}" x2="{(x + n) * s:.2f}" y2="{y * s:.2f}"/>'
                    for x, y, n in theme.CAPTION_LINES)
    rad = s * 0.26
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 {s} {s}">
  <title>Ghostline</title>
  <defs>
    <linearGradient id="tile" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{theme.LOGO_TILE[0]}"/><stop offset="1" stop-color="{theme.LOGO_TILE[1]}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{theme.ACCENT}" stop-opacity="0.24"/><stop offset="1" stop-color="{theme.ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="ghost" x1="0" y1="0" x2="{s}" y2="{s}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{theme.ACCENT}"/><stop offset="1" stop-color="{theme.ACCENT_2}"/>
    </linearGradient>
  </defs>
  <rect width="{s}" height="{s}" rx="{rad:.2f}" fill="url(#tile)"/>
  <rect width="{s}" height="{s}" rx="{rad:.2f}" fill="url(#glow)"/>
  <path d="{ghost}" fill="url(#ghost)"/>
  <g stroke="{theme.LOGO_INK}" stroke-width="{theme.LINE_W * s:.2f}" stroke-linecap="round">{lines}</g>
</svg>
"""


def main() -> int:
    QGuiApplication(sys.argv[:1])
    ICO.parent.mkdir(parents=True, exist_ok=True)
    PNG.parent.mkdir(parents=True, exist_ok=True)
    frames = [render(n) for n in SIZES]
    frames[-1].save(ICO, sizes=[(n, n) for n in SIZES], append_images=frames[:-1])
    render(512).save(PNG)
    SVG.write_text(svg(), encoding="utf-8")
    for path in (ICO, PNG, SVG):
        print("wrote", path)
    if "--preview" in sys.argv:                 # strip of all sizes on light and dark backgrounds
        sheet = Image.new("RGBA", (sum(SIZES) + 20 * len(SIZES) + 20, 2 * 256 + 60), (255, 255, 255, 255))
        sheet.paste((24, 24, 30, 255), (0, 256 + 30, sheet.width, sheet.height))
        x = 20
        for n, im in zip(SIZES, frames, strict=True):
            sheet.alpha_composite(im, (x, 15 + (256 - n)))
            sheet.alpha_composite(im, (x, 256 + 45 + (256 - n)))
            x += n + 20
        out = Path(sys.argv[sys.argv.index("--preview") + 1])
        sheet.save(out)
        print("preview", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
