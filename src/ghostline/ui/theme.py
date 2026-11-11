"""Colours, fonts, icon glyphs and the app icon."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

ACCENT = "#7cd2ff"
ACCENT_2 = "#a99bff"
TEXT = "#f5f5f7"
REC = "#ff4d5e"
WARN = "#ffbe46"
RADIUS = 16

UI_FONT = "Segoe UI"
DISPLAY_FONTS = ["Segoe UI Variable Display", "Segoe UI"]

# Segoe Fluent Icons / Segoe MDL2 Assets code points
class Glyph:
    COPY = ""
    SAVE = ""
    DELETE = ""
    PIN = ""
    CHEVRON_DOWN = ""
    CHEVRON_UP = ""
    MINIMIZE = ""
    CLOSE = ""
    MORE = ""
    BACK = ""
    REFRESH = ""
    OPEN_EXTERNAL = ""
    CHAT = ""
    SHIELD = ""


@lru_cache(maxsize=1)
def icon_font_family() -> str:
    families = set(QFontDatabase.families())
    for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets"):
        if name in families:
            return name
    return "Segoe UI Symbol"


def ui_font(px: int, weight: QFont.Weight = QFont.Normal) -> QFont:
    f = QFont(UI_FONT)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


def display_font(px: int, weight: QFont.Weight = QFont.Medium) -> QFont:
    f = QFont(DISPLAY_FONTS[0])
    f.setFamilies(DISPLAY_FONTS)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


LOGO_TILE = ("#20223a", "#0e0f17")
LOGO_INK = "#10111a"

# The Ghostline mark in a 1×1 box: a ghost (hidden from screen capture) whose "eyes" are two caption
# lines. scripts/make_icon.py renders the same geometry to assets/icon.ico and docs/logo.svg.
GHOST_HEAD = (0.24, 0.17, 0.52)                       # x, y, diameter of the round head
GHOST_BOTTOM, GHOST_NOTCH = 0.83, 0.68                # tips of the tail, control point of each notch
CAPTION_LINES = ((0.35, 0.43, 0.30), (0.35, 0.555, 0.20))   # x, y, length
LINE_W = 0.075


def ghost_path(rect: QRectF) -> QPainterPath:
    x0, y0, s = rect.x(), rect.y(), rect.width()

    def pt(x: float, y: float) -> tuple[float, float]:
        return x0 + x * s, y0 + y * s

    hx, hy, d = GHOST_HEAD
    left, right = hx, hx + d
    path = QPainterPath()
    path.moveTo(*pt(left, hy + d / 2))
    path.arcTo(QRectF(*pt(hx, hy), d * s, d * s), 180, -180)
    path.lineTo(*pt(right, GHOST_BOTTOM))
    step = d / 3
    for i in range(3):                                   # three scallops along the tail
        a = right - i * step
        path.quadTo(*pt(a - step / 2, GHOST_NOTCH), *pt(a - step, GHOST_BOTTOM))
    path.closeSubpath()
    return path


def paint_logo(p: QPainter, rect: QRectF, tile: bool = True) -> None:
    s = rect.width()
    p.save()
    p.setPen(Qt.NoPen)
    if tile:
        bg = QLinearGradient(rect.topLeft(), rect.bottomRight())
        bg.setColorAt(0, QColor(LOGO_TILE[0]))
        bg.setColorAt(1, QColor(LOGO_TILE[1]))
        p.setBrush(bg)
        p.drawRoundedRect(rect, s * 0.26, s * 0.26)
        glow = QRadialGradient(rect.center(), s * 0.5)
        glow.setColorAt(0, QColor(124, 210, 255, 60))
        glow.setColorAt(1, QColor(124, 210, 255, 0))
        p.setBrush(glow)
        p.drawRoundedRect(rect, s * 0.26, s * 0.26)
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0, QColor(ACCENT))
    g.setColorAt(1, QColor(ACCENT_2))
    p.setBrush(g)
    p.drawPath(ghost_path(rect))
    pen = QPen(QColor(LOGO_INK), max(1.2, LINE_W * s))
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    for x, y, length in CAPTION_LINES:
        p.drawLine(QPointF(rect.x() + x * s, rect.y() + y * s), QPointF(rect.x() + (x + length) * s, rect.y() + y * s))
    p.restore()


def app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        paint_logo(p, QRectF(0, 0, size, size))
        p.end()
        icon.addPixmap(pm)
    return icon


APP_STYLESHEET = f"""
QToolTip {{ background: #24242b; color: #eee; border: 1px solid rgba(255,255,255,0.15);
            padding: 5px 8px; border-radius: 6px; font: 12px '{UI_FONT}'; }}
QMenu {{ background: #23232a; color: #eee; border: 1px solid rgba(255,255,255,0.12);
         border-radius: 10px; padding: 6px; font: 13px '{UI_FONT}'; }}
QMenu::item {{ padding: 7px 28px 7px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: rgba(255,255,255,0.09); }}
QMenu::item:disabled {{ color: rgba(255,255,255,0.35); }}
QMenu::separator {{ height: 1px; background: rgba(255,255,255,0.1); margin: 5px 8px; }}
QMenu::indicator {{ width: 14px; height: 14px; margin-left: 6px; }}
QMenu::indicator:checked {{ image: none; background: {ACCENT}; border-radius: 4px; }}
QMenu::indicator:unchecked {{ image: none; border: 1px solid rgba(255,255,255,0.3); border-radius: 4px; }}
"""
