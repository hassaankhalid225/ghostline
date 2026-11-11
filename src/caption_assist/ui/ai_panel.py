"""Side panel with an embedded browser for ChatGPT / Claude (or any site) next to the captions."""

from __future__ import annotations

import json
import logging
import os
import re

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QMenu,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import APP_ID, APP_NAME
from ..config import Settings, data_dir
from . import theme
from .theme import Glyph
from .widgets import IconButton

log = logging.getLogger(__name__)

SERVICES: dict[str, str] = {
    "ChatGPT": "https://chatgpt.com/",
    "Claude": "https://claude.ai/new",
}

# Puts text into the chat box of the current page (ChatGPT, Claude and most chat UIs). Returns true on success.
_INSERT_JS = """
(function (text, submit) {
  const selectors = ['#prompt-textarea', 'div.ProseMirror[contenteditable="true"]',
                     '[contenteditable="true"][role="textbox"]', '[contenteditable="true"]', 'textarea'];
  let el = null;
  for (const s of selectors) { el = document.querySelector(s); if (el) break; }
  if (!el) return false;
  if (!text) return true;
  el.focus();
  if (el.tagName === 'TEXTAREA') {
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(el, (el.value ? el.value + '\\n' : '') + text);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  } else {
    const range = document.createRange();
    range.selectNodeContents(el);
    range.collapse(false);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    document.execCommand('insertText', false, text);
  }
  if (submit) {
    // Give the page a moment to register the new text, then press its send button.
    let tries = 0;
    const press = () => {
      const btn = document.querySelector(
        'button[data-testid="send-button"], #composer-submit-button, button[aria-label="Send message"],' +
        ' button[aria-label="Send prompt"], button[aria-label="Send"]');
      if (btn && !btn.disabled) { btn.click(); return; }
      if (++tries < 20) { setTimeout(press, 150); return; }
      el.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
                                                      bubbles: true, cancelable: true }));
    };
    setTimeout(press, 200);
  }
  return true;
})(%s, %s)
"""


def _make_profile() -> QWebEngineProfile:
    """A persistent profile so ChatGPT / Claude stay signed in between runs."""
    profile = QWebEngineProfile(APP_ID, None)
    root = os.path.join(data_dir(), "web")
    profile.setPersistentStoragePath(os.path.join(root, "storage"))
    profile.setCachePath(os.path.join(root, "cache"))
    profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
    profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
    # Present as plain Chrome: some sites refuse "QtWebEngine" user agents.
    profile.setHttpUserAgent(re.sub(r"\s*QtWebEngine/\S+", "", profile.httpUserAgent()))
    s = profile.settings()
    for attr in (QWebEngineSettings.JavascriptCanAccessClipboard, QWebEngineSettings.JavascriptCanPaste,
                 QWebEngineSettings.LocalStorageEnabled, QWebEngineSettings.FullScreenSupportEnabled,
                 QWebEngineSettings.ScrollAnimatorEnabled):
        s.setAttribute(attr, True)
    return profile


class _Page(QWebEnginePage):
    """Opens `window.open` / target=_blank links (e.g. sign-in pop-ups) in a small companion window."""

    popups: list[QWebEngineView] = []

    def javaScriptConsoleMessage(self, level, message, line, source) -> None:
        log.debug("js[%s] %s (%s:%s)", getattr(level, "name", level), message[:300], source[-80:], line)

    def createWindow(self, _type):
        log.info("page opened a pop-up window")
        owner = self.view().window() if self.view() else None
        view = QWebEngineView()
        # Stay above the (always-on-top) main window, otherwise sign-in pop-ups open hidden behind it.
        view.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        if owner is not None:
            center = owner.geometry().center()
            view.move(center.x() - 260, center.y() - 340)
        view.setAttribute(Qt.WA_DeleteOnClose)
        page = _Page(self.profile(), view)
        view.setPage(page)
        page.windowCloseRequested.connect(view.close)
        view.setWindowTitle(APP_NAME)
        view.setWindowIcon(theme.app_icon())
        view.resize(520, 680)
        view.destroyed.connect(lambda *_: _Page.popups.remove(view) if view in _Page.popups else None)
        _Page.popups.append(view)
        view.show()
        return page


class AIPanel(QWidget):
    """Toolbar (service switch, back, reload, address, send captions) above a stack of web views."""

    toast = Signal(str)
    send_requested = Signal(str)   # "new" | "last5" | "all" — the window answers with insert_text()

    def __init__(self, settings: Settings, parent: QWidget | None = None):
        super().__init__(parent)
        self.settings = settings
        start_service = settings.ai_service
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("AIPanel")
        self.setStyleSheet("#AIPanel { background: rgba(10,10,14,0.55); border-radius: 12px; }")
        self.profile = _make_profile()
        self.views: dict[str, QWebEngineView] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        bar = QWidget(self)
        bar.setFixedHeight(44)
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(4)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        seg_css = (f"QPushButton {{ color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.06);"
                   f" border: 1px solid rgba(255,255,255,0.1); border-radius: 13px; padding: 0 12px;"
                   f" font: 600 12px '{theme.UI_FONT}'; }}"
                   " QPushButton:hover { background: rgba(255,255,255,0.12); color: white; }"
                   f" QPushButton:checked {{ color: #0b0b12; border: none; background: qlineargradient(x1:0,y1:0,"
                   f"x2:1,y2:1, stop:0 {theme.ACCENT}, stop:1 {theme.ACCENT_2}); }}")
        self.service_btns: dict[str, QPushButton] = {}
        for name in [*SERVICES, "Web"]:
            b = QPushButton(name, bar)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            b.setFixedHeight(28)
            b.setStyleSheet(seg_css)
            b.clicked.connect(lambda _=False, n=name: self.show_service(n))
            self.group.addButton(b)
            self.service_btns[name] = b
            h.addWidget(b)
        h.addSpacing(6)

        small = 30
        self.back_btn = IconButton(Glyph.BACK, "Back", size=small)
        self.back_btn.clicked.connect(lambda: self.current_view() and self.current_view().back())
        h.addWidget(self.back_btn)
        self.reload_btn = IconButton(Glyph.REFRESH, "Reload", size=small)
        self.reload_btn.clicked.connect(lambda: self.current_view() and self.current_view().reload())
        h.addWidget(self.reload_btn)

        self.address = QLineEdit(bar)
        self.address.setPlaceholderText("Search or enter address")
        self.address.setFixedHeight(28)
        self.address.setStyleSheet(
            f"QLineEdit {{ background: rgba(255,255,255,0.07); color: rgba(255,255,255,0.88);"
            f" border: 1px solid rgba(255,255,255,0.1); border-radius: 13px; padding: 0 10px;"
            f" font: 12px '{theme.UI_FONT}'; selection-background-color: rgba(124,210,255,0.35); }}"
            f" QLineEdit:focus {{ border: 1px solid {theme.ACCENT}; }}")
        self.address.returnPressed.connect(self._go_address)
        h.addWidget(self.address, 1)

        self.send_btn = QToolButton(bar)
        self.send_btn.setText("  Send")
        self.send_btn.setToolTip("Send the captions you haven't sent yet to the AI and get the answer   Ctrl+Enter")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setFocusPolicy(Qt.NoFocus)
        self.send_btn.setFixedHeight(28)
        self.send_btn.setFont(theme.ui_font(12, QFont.DemiBold))
        self.send_btn.setPopupMode(QToolButton.MenuButtonPopup)
        self.send_btn.setStyleSheet(
            f"QToolButton {{ color: {theme.ACCENT}; background: rgba(124,210,255,0.12);"
            " border: 1px solid rgba(124,210,255,0.35); border-radius: 13px; padding: 0 22px 0 10px; }"
            " QToolButton:hover { background: rgba(124,210,255,0.22); }"
            " QToolButton::menu-button { border: none; width: 18px; }"
            " QToolButton::menu-arrow { image: none; }")
        menu = QMenu(self.send_btn)
        menu.addAction("New captions since last send", lambda: self.send_requested.emit("new"))
        menu.addAction("Last 5 sentences", lambda: self.send_requested.emit("last5"))
        menu.addAction("Whole transcript", lambda: self.send_requested.emit("all"))
        menu.addSeparator()
        auto = menu.addAction("Press send automatically (get the answer right away)")
        auto.setCheckable(True)
        auto.setChecked(settings.ai_auto_send)
        auto.toggled.connect(self._set_auto_send)
        menu.addAction("Instruction before captions…", self._edit_prefix)
        self.send_btn.setMenu(menu)
        self.send_btn.clicked.connect(lambda: self.send_requested.emit("new"))
        h.addWidget(self.send_btn)

        ext = IconButton(Glyph.OPEN_EXTERNAL, "Open this page in your normal browser", size=small)
        ext.clicked.connect(self._open_external)
        h.addWidget(ext)
        lay.addWidget(bar)

        self.stack = QStackedWidget(self)
        lay.addWidget(self.stack, 1)

        self.show_service(start_service if start_service in self.service_btns else "ChatGPT")

    # ------------------------------------------------------------------ views
    def current_view(self) -> QWebEngineView | None:
        return self.stack.currentWidget()

    @property
    def current_service(self) -> str:
        for name, view in self.views.items():
            if view is self.stack.currentWidget():
                return name
        return "ChatGPT"

    def _view_for(self, name: str) -> QWebEngineView:
        view = self.views.get(name)
        if view is None:
            view = QWebEngineView(self.stack)
            view.setPage(_Page(self.profile, view))
            view.page().setBackgroundColor(Qt.white)
            view.urlChanged.connect(lambda url, v=view: self._on_url(v, url))
            view.page().fullScreenRequested.connect(lambda req: req.reject())
            view.load(QUrl(SERVICES.get(name, "https://www.google.com/")))
            self.stack.addWidget(view)
            self.views[name] = view
        return view

    def show_service(self, name: str) -> None:
        view = self._view_for(name)
        self.stack.setCurrentWidget(view)
        self.service_btns[name].setChecked(True)
        self._on_url(view, view.url())

    def _on_url(self, view: QWebEngineView, url: QUrl) -> None:
        if view is self.stack.currentWidget() and not self.address.hasFocus():
            self.address.setText(url.toString())
            self.address.setCursorPosition(0)

    def _go_address(self) -> None:
        text = self.address.text().strip()
        if not text:
            return
        if " " in text or "." not in text:
            url = QUrl("https://www.google.com/search?q=" + QUrl.toPercentEncoding(text).data().decode())
        else:
            url = QUrl.fromUserInput(text)
        view = self.current_view()
        if view is not None:
            view.load(url)
            view.setFocus()

    def _open_external(self) -> None:
        view = self.current_view()
        if view is not None and view.url().isValid():
            QDesktopServices.openUrl(view.url())

    # ------------------------------------------------------------------ send captions
    def _set_auto_send(self, on: bool) -> None:
        self.settings.ai_auto_send = bool(on)
        self.settings.save()

    def _edit_prefix(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self, "Instruction before captions",
            "Sent in front of the captions (leave empty to send only the captions):",
            self.settings.ai_prefix)
        if ok:
            self.settings.ai_prefix = text.strip()
            self.settings.save()
            self.toast.emit("✓  Instruction saved" if text.strip() else "Instruction removed")

    def insert_text(self, text: str) -> None:
        view = self.current_view()
        if view is None or not text.strip():
            return
        if self.settings.ai_prefix:
            text = f"{self.settings.ai_prefix}\n\n{text}"
        submit = self.settings.ai_auto_send

        def done(ok) -> None:
            if ok:
                view.setFocus()
                self.toast.emit("✓  Sent — answer is coming in the panel" if submit
                                else "✓  Captions pasted into the chat box")
            else:
                from PySide6.QtWidgets import QApplication
                QApplication.clipboard().setText(text)
                self.toast.emit("Chat box not found — captions copied, press Ctrl+V")

        view.page().runJavaScript(_INSERT_JS % (json.dumps(text), json.dumps(submit)), 0, done)

    def shutdown(self) -> None:
        for view in list(_Page.popups):
            view.close()
        for view in self.views.values():   # pages must go before the profile they use
            view.page().deleteLater()
            view.deleteLater()
        self.views.clear()
