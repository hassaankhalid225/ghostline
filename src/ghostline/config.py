"""User settings (persisted with QSettings in the registry) and standard paths."""

from __future__ import annotations

import os
from dataclasses import dataclass, fields

from PySide6.QtCore import QSettings

from . import APP_ID, APP_NAME


def documents_dir() -> str:
    try:
        from PySide6.QtCore import QStandardPaths
        path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        if path:
            return path
    except Exception:  # pragma: no cover
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def default_transcripts_dir() -> str:
    return os.path.join(documents_dir(), APP_NAME)


LEGACY_IDS = (("CaptionAssist", "Caption Assist"),)   # (APP_ID, APP_NAME) used by earlier builds


def migrate_legacy() -> None:
    """One-time move of data from the app's earlier name, so sign-ins, settings and transcripts survive."""
    local = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    for old_id, old_name in LEGACY_IDS:
        for old, new in ((os.path.join(local, old_id), os.path.join(local, APP_ID)),
                         (os.path.join(documents_dir(), old_name), default_transcripts_dir())):
            if os.path.isdir(old) and not os.path.exists(new):
                try:
                    os.rename(old, new)
                except OSError:
                    pass
        old_qs, new_qs = QSettings(old_id, "app"), QSettings(APP_ID, "app")
        if old_qs.allKeys() and not new_qs.allKeys():
            for key in old_qs.allKeys():
                new_qs.setValue(key, old_qs.value(key))
            new_qs.sync()


def data_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_ID)
    os.makedirs(path, exist_ok=True)
    return path


def log_dir() -> str:
    path = os.path.join(data_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


@dataclass
class Settings:
    font_px: int = 24
    always_on_top: bool = True
    private_mode: bool = True           # hide every window from screenshots / screen sharing
    glass_blur: bool = True             # only possible in private mode
    timestamps: bool = False
    autosave: bool = True
    start_on_launch: bool = False
    transcripts_dir: str = ""
    window_geometry: str = ""           # "x,y,w" of the compact bar
    ai_service: str = "ChatGPT"         # last tab used in the AI side panel
    ai_split: str = ""                  # "captions,panel" splitter sizes
    ai_auto_send: bool = True           # press the chat's send button after pasting captions
    ai_prefix: str = ""                 # optional instruction sent before the captions

    @property
    def effective_transcripts_dir(self) -> str:
        return self.transcripts_dir or default_transcripts_dir()

    # ------------------------------------------------------------------ persistence
    @classmethod
    def load(cls) -> Settings:
        qs = QSettings(APP_ID, "app")
        s = cls()
        for f in fields(cls):
            raw = qs.value(f.name)
            if raw is None:
                continue
            default = getattr(s, f.name)
            try:
                if isinstance(default, bool):
                    value = raw if isinstance(raw, bool) else str(raw).lower() in ("1", "true", "yes")
                elif isinstance(default, int):
                    value = int(raw)
                else:
                    value = str(raw)
            except (TypeError, ValueError):
                continue
            setattr(s, f.name, value)
        s.font_px = max(12, min(56, s.font_px))
        return s

    def save(self) -> None:
        qs = QSettings(APP_ID, "app")
        names = {f.name for f in fields(self)}
        for key in qs.allKeys():          # drop settings from older versions
            if key not in names:
                qs.remove(key)
        for name in names:
            qs.setValue(name, getattr(self, name))
        qs.sync()
