# -*- coding: utf-8 -*-
"""
NaroEditor - PyQt6 Japanese text editor
UI theme : dark mode
Kinsoku  : Qt/ICU UAX#14 (WrapAtWordBoundaryOrAnywhere)
"""

import sys
import os
import re
import json
import time
import shutil
import ctypes
import ctypes.wintypes
import chardet

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPlainTextEdit, QTextEdit,
    QSplitter, QLabel, QDialog, QLineEdit, QCheckBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QFileDialog, QMessageBox, QFrame, QTreeView, QTabWidget, QTabBar,
    QTextBrowser, QComboBox, QInputDialog, QMenu,
    QGraphicsView, QGraphicsScene, QProgressDialog,
)
from PyQt6.QtCore import Qt, QRect, QRectF, QSize, QModelIndex, pyqtSignal, QTimer, QPoint, QEvent, QByteArray, QFileSystemWatcher, QObject, QSizeF, QPointF, QThread
from PyQt6.QtGui import QTransform
from PyQt6.QtGui import (
    QFont, QFontMetrics, QFontMetricsF, QPainter, QColor, QTextCursor, QKeySequence,
    QTextOption, QStandardItemModel, QStandardItem,
    QTextFormat, QTextFrameFormat, QTextCharFormat, QTextBlockFormat,
    QTextObjectInterface, QPalette, QPen, QPolygon, QCursor, QPixmap, QIcon,
)


APP_VERSION = "1.2.9"
_GITHUB_API_LATEST = "https://api.github.com/repos/s1675dis/NaroEditor/releases/latest"

# アップデータのパス（AppData\Roaming\NaroEditor\NaroEditorUpdater.exe）
_UPDATER_DIR  = os.path.join(os.environ.get("APPDATA", ""), "NaroEditor")
_UPDATER_NAME = "NaroEditorUpdater.exe"
_UPDATER_PATH = os.path.join(_UPDATER_DIR, _UPDATER_NAME)


def _ensure_updater() -> None:
    """バンドル済み NaroEditorUpdater.exe を AppData へ展開する（frozen 時のみ）。"""
    if not getattr(sys, "frozen", False):
        return
    src = os.path.join(getattr(sys, "_MEIPASS", ""), _UPDATER_NAME)
    if not os.path.isfile(src):
        return
    os.makedirs(_UPDATER_DIR, exist_ok=True)
    try:
        # サイズ比較は廃止。バージョンアップ時に古いアップデータが残らないよう常に上書き。
        import shutil as _shutil
        _shutil.copy2(src, _UPDATER_PATH)
    except OSError:
        pass

# ---------------------------------------------------------------------------
# One Dark / Pulsar Night colour palette
# ---------------------------------------------------------------------------
C = {
    "bg":        "#282c34",
    "bg_panel":  "#21252b",
    "bg_bar":    "#1d2126",
    "bg_hi":     "#2c313c",
    "border":    "#181a1f",
    "select":    "#3e4451",
    "fg":        "#abb2bf",
    "fg_dim":    "#636d83",
    "fg_subtle": "#4b5263",
    "accent":    "#61afef",
    "green":     "#98c379",
    "red":       "#e06c75",
    "yellow":    "#e5c07b",
    "btn":       "#3a3f4b",
    "btn_hi":    "#4a5060",
    "input":     "#1d2126",
    "scroll":    "#3e4451",
    "scroll_hi": "#636d83",
}

# ---------------------------------------------------------------------------
# Application-wide Qt stylesheet
# ---------------------------------------------------------------------------
APP_QSS = f"""
QMainWindow, QDialog {{
    background: {C['bg_panel']};
    color: {C['fg']};
}}

/* ── Menu ─────────────────────────────────────────────── */
QMenuBar {{
    background: {C['bg_bar']};
    color: {C['fg']};
    border-bottom: 1px solid {C['border']};
    padding: 2px 0;
}}
QMenuBar::item {{ background: transparent; padding: 4px 12px; border-radius: 3px; }}
QMenuBar::item:selected {{ background: {C['select']}; }}

QMenu {{
    background: {C['bg_panel']};
    color: {C['fg']};
    border: 1px solid {C['border']};
    padding: 4px 0;
}}
QMenu::item {{ padding: 6px 24px 6px 12px; }}
QMenu::item:selected {{ background: {C['select']}; }}
QMenu::item:disabled {{ color: {C['fg_dim']}; }}
QMenu::separator {{ height: 1px; background: {C['select']}; margin: 4px 0; }}

/* ── Status bar ───────────────────────────────────────── */
QStatusBar {{
    background: {C['bg_bar']};
    color: {C['fg_dim']};
    border-top: 1px solid {C['border']};
    font-size: 12px;
}}
QStatusBar QLabel {{ padding: 0 8px; color: {C['fg_dim']}; background: transparent; }}

/* ── Splitter ─────────────────────────────────────────── */
QSplitter::handle {{ background: {C['border']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical   {{ height: 1px; }}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton {{
    background: {C['btn']};
    color: {C['fg']};
    border: 1px solid {C['border']};
    border-radius: 4px;
    padding: 3px 12px;
    font-size: 12px;
    min-height: 22px;
}}
QPushButton:hover   {{ background: {C['btn_hi']}; border-color: {C['fg_dim']}; }}
QPushButton:pressed {{ background: {C['bg_hi']}; }}

/* ── Inputs ───────────────────────────────────────────── */
QLineEdit {{
    background: {C['input']};
    color: {C['fg']};
    border: 1px solid {C['select']};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {C['select']};
    selection-color: {C['fg']};
}}
QLineEdit:focus {{ border-color: {C['accent']}; }}

/* ── Checkboxes ───────────────────────────────────────── */
QCheckBox {{ color: {C['fg']}; spacing: 6px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {C['select']};
    border-radius: 3px;
    background: {C['input']};
}}
QCheckBox::indicator:checked {{ background: {C['accent']}; border-color: {C['accent']}; }}

/* ── Labels ───────────────────────────────────────────── */
QLabel {{ color: {C['fg']}; background: transparent; }}

/* ── Tab widget ───────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: {C['bg']};
}}
QTabBar {{
    background: {C['bg_bar']};
}}
QTabBar::tab {{
    background: {C['bg_bar']};
    color: {C['fg_dim']};
    padding: 7px 14px 7px 14px;
    border-right: 1px solid {C['border']};
    border-top: 2px solid transparent;
    min-width: 80px;
    max-width: 220px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background: {C['bg']};
    color: {C['fg']};
    border-top-color: {C['accent']};
}}
QTabBar::tab:hover:!selected {{
    background: {C['bg_hi']};
    color: {C['fg']};
}}
QTabBar::scroller {{
    width: 20px;
}}

/* ── Tree view ────────────────────────────────────────── */
QTreeView {{
    background: {C['bg_panel']};
    color: {C['fg']};
    border: none;
    outline: none;
    show-decoration-selected: 1;
}}
QTreeView::item {{ padding: 3px 4px; }}
QTreeView::item:hover    {{ background: {C['bg_hi']}; }}
QTreeView::item:selected {{ background: {C['select']}; color: {C['fg']}; }}
QTreeView::branch {{
    background: {C['bg_panel']};
    image: none;
    border-image: none;
}}
QTreeView::branch:selected {{ background: {C['select']}; image: none; border-image: none; }}

/* ── Scrollbars ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: {C['bg_panel']}; width: 10px; border: none; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['scroll']}; border-radius: 5px; min-height: 28px; margin: 2px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['scroll_hi']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background: {C['bg_panel']}; height: 10px; border: none; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {C['scroll']}; border-radius: 5px; min-width: 28px; margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C['scroll_hi']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Frame / separator ────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {C['border']}; background: {C['border']};
}}
"""


# ---------------------------------------------------------------------------
# Config persistence
# ---------------------------------------------------------------------------
_APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NaroEditor")
os.makedirs(_APP_DIR, exist_ok=True)
_CONFIG_PATH = os.path.join(_APP_DIR, "config.json")

# onefile 展開キャッシュ用ディレクトリを初回起動時に作成する
# （2回目以降の起動で PyInstaller がここを再利用し高速化される）
_LOCAL_APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", _APP_DIR), "NaroEditor")
os.makedirs(_LOCAL_APP_DIR, exist_ok=True)

# クラッシュリカバリー用パス
_RECOVERY_DIR  = os.path.join(_APP_DIR, "recovery")
_LOCK_PATH     = os.path.join(_APP_DIR, "session.lock")
os.makedirs(_RECOVERY_DIR, exist_ok=True)


def _load_cfg() -> dict:
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cfg(cfg: dict) -> None:
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# File lock manager (Windows)
# 開いているファイルを FILE_SHARE_DELETE なしで保持し、
# エクスプローラーからの移動・名前変更を防ぐ。
# ---------------------------------------------------------------------------
class FileLockManager:
    _GENERIC_READ        = 0x80000000
    _FILE_SHARE_READ     = 0x00000001
    _FILE_SHARE_WRITE    = 0x00000002
    _OPEN_EXISTING       = 3
    _FILE_ATTRIBUTE_NORMAL = 0x00000080
    _INVALID_HANDLE      = ctypes.wintypes.HANDLE(-1).value

    def __init__(self) -> None:
        self._handles: dict[str, int] = {}   # normalized path → HANDLE
        self._counts:  dict[str, int] = {}   # normalized path → open tab count

    def _norm(self, path: str) -> str:
        return os.path.normcase(os.path.normpath(path))

    def lock(self, path: str) -> None:
        key = self._norm(path)
        self._counts[key] = self._counts.get(key, 0) + 1
        if key in self._handles:
            return
        h = ctypes.windll.kernel32.CreateFileW(
            path,
            self._GENERIC_READ,
            self._FILE_SHARE_READ | self._FILE_SHARE_WRITE,   # DELETE なし
            None,
            self._OPEN_EXISTING,
            self._FILE_ATTRIBUTE_NORMAL,
            None,
        )
        if h != self._INVALID_HANDLE:
            self._handles[key] = h

    def unlock(self, path: str) -> None:
        if not path:
            return
        key = self._norm(path)
        count = self._counts.get(key, 0) - 1
        if count > 0:
            self._counts[key] = count
            return
        self._counts.pop(key, None)
        h = self._handles.pop(key, None)
        if h is not None:
            ctypes.windll.kernel32.CloseHandle(h)

    def unlock_all(self) -> None:
        for h in self._handles.values():
            ctypes.windll.kernel32.CloseHandle(h)
        self._handles.clear()
        self._counts.clear()

    def temp_unlock(self, path: str) -> bool:
        """リネーム前にOSハンドルだけ解放する（参照カウントは維持）。
        ロックされていた場合 True を返す。"""
        key = self._norm(path)
        h = self._handles.pop(key, None)
        if h is not None:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False

    def restore_lock(self, path: str) -> None:
        """temp_unlock 後にリネームが失敗した場合、ハンドルを再取得する。"""
        key = self._norm(path)
        if self._counts.get(key, 0) > 0 and key not in self._handles:
            h = ctypes.windll.kernel32.CreateFileW(
                path,
                self._GENERIC_READ,
                self._FILE_SHARE_READ | self._FILE_SHARE_WRITE,
                None, self._OPEN_EXISTING, self._FILE_ATTRIBUTE_NORMAL, None,
            )
            if h != self._INVALID_HANDLE:
                self._handles[key] = h

    def on_rename(self, old_path: str, new_path: str) -> None:
        """リネーム成功後、ロックを旧パスから新パスへ移す。"""
        old_key = self._norm(old_path)
        new_key = self._norm(new_path)
        count = self._counts.pop(old_key, 0)
        if count == 0:
            return
        self._counts[new_key] = count
        h = ctypes.windll.kernel32.CreateFileW(
            new_path,
            self._GENERIC_READ,
            self._FILE_SHARE_READ | self._FILE_SHARE_WRITE,
            None, self._OPEN_EXISTING, self._FILE_ATTRIBUTE_NORMAL, None,
        )
        if h != self._INVALID_HANDLE:
            self._handles[new_key] = h


# ---------------------------------------------------------------------------
# Encoding detection
# ---------------------------------------------------------------------------
_ENC_TRY = ["utf-8-sig", "utf-8", "shift_jis", "cp932", "euc_jp", "iso2022_jp", "latin-1"]
_ENC_MAP = {
    "shift_jis": "shift_jis", "shift-jis": "shift_jis",
    "windows-1252": "cp1252", "euc-jp": "euc_jp",
    "iso-2022-jp": "iso2022_jp", "utf-8-sig": "utf-8-sig",
    "utf-8": "utf-8", "ascii": "utf-8",
}


def detect_encoding(data: bytes) -> str:
    raw_name = (chardet.detect(data).get("encoding") or "").lower()
    candidate = _ENC_MAP.get(raw_name, raw_name)
    for enc in ([candidate] if candidate else []) + _ENC_TRY:
        try:
            if enc:
                data.decode(enc)
                return enc
        except Exception:
            continue
    return "utf-8"


# ---------------------------------------------------------------------------
# Narou / Pixiv format — 正規表現（プレビュー描画と共用）
# ---------------------------------------------------------------------------
_RE_EMPH           = re.compile(r'《《([^《》\n]+?)》》')
_RE_RUBY1          = re.compile(r'\|([^|《》\n]+?)《([^《》\n]+?)》')
_RE_RUBY2          = re.compile(r'([一-鿿㐀-䶿々ヶ豈-﩯]+)《([^《》\n]+?)》')
_RE_RUBY_PIXIV_RAW = re.compile(r'\[\[rb:([^\]\n]+?)\s*>\s*([^\]\n]+?)\]\]')
_RE_EMPH_PIXIV_RAW = re.compile(r'\[\[emphasismark:([^\]\n]+?)\s*>\s*([^\]]*)\]\]')
_RE_HR_LINE        = re.compile(r'^[─━ー＝－\-=]{3,}$')

# ---------------------------------------------------------------------------
# Preview themes（QTextBrowser 用）
# ---------------------------------------------------------------------------
_RUBY_RT_PX    = 8
_RUBY_OBJ_TYPE = int(QTextFormat.ObjectTypes.UserObject) + 1
_PROP_BASE     = int(QTextFormat.Property.UserProperty)  + 1
_PROP_READING  = int(QTextFormat.Property.UserProperty)  + 2

_THEMES: dict[str, dict] = {
    "narou": {
        "label":        "小説家になろう",
        "ruby_nudge":   5,
        "font_qt":      "Meiryo",
        "font_px":      16,
        "line_height":  1.8,
        "bg":           "#ffffff",
        "fg":           "#444444",
        "title_px":     27.2,
        "title_weight": "bold",
        "title_align":  "center",
        "title_fg":     "#444444",
        "title_lh":     1.5,
        "title_mt":     50,
        "title_mb":     20,
        "content_w":    592,
    },
    "kakuyomu": {
        "label":        "カクヨム",
        "ruby_nudge":   3,
        "font_qt":      "游明朝",
        "font_px":      17.5,
        "line_height":  1.8,
        "bg":           "#ffffff",
        "fg":           "#222222",
        "title_px":     26.25,
        "title_weight": "normal",
        "title_align":  "center",
        "title_fg":     "#222222",
        "title_lh":     1.5,
        "title_mt":     35,
        "title_mb":     60,
        "content_w":    665,
    },
    "pixiv_mincho": {
        "label":        "Pixiv小説（游明朝）",
        "ruby_nudge":   3,
        "font_qt":      "游明朝",
        "font_px":      16,
        "line_height":  1.75,
        "bg":           "#ffffff",
        "fg":           "#1f1f1f",
        "title_px":     24,
        "title_weight": "bold",
        "title_align":  "left",
        "title_fg":     "#1f1f1f",
        "title_lh":     1.5,
        "title_mt":     60,
        "title_mb":     24,
        "content_w":    680,
    },
    "pixiv_gothic": {
        "label":        "Pixiv小説（游ゴシック）",
        "ruby_nudge":   3,
        "font_qt":      "游ゴシック",
        "font_px":      16,
        "line_height":  1.75,
        "bg":           "#ffffff",
        "fg":           "#1f1f1f",
        "title_px":     24,
        "title_weight": "bold",
        "title_align":  "left",
        "title_fg":     "#1f1f1f",
        "title_lh":     1.5,
        "title_mt":     60,
        "title_mb":     24,
        "content_w":    680,
    },
    "fanbox": {
        "label":        "Pixiv Fanbox",
        "ruby_nudge":   5,
        "font_qt":      "Meiryo",
        "font_px":      16,
        "line_height":  36 / 16,
        "bg":           "#ffffff",
        "fg":           "#202020",
        "title_px":     30,
        "title_weight": "bold",
        "title_align":  "left",
        "title_fg":     "#333333",
        "title_lh":     36 / 30,
        "title_mt":     0,
        "title_mb":     24,
        "content_w":    680,
    },
}
_THEME_ORDER = ["narou", "kakuyomu", "pixiv_mincho", "pixiv_gothic", "fanbox"]
_PREVIEW_MIN_W = 880


# ---------------------------------------------------------------------------
# Search / Replace dialog
# ---------------------------------------------------------------------------
class SearchReplaceDialog(QDialog):
    def __init__(self, parent: QWidget, editor: QPlainTextEdit, mode: str = "search"):
        super().__init__(parent)
        self._editor = editor
        self._mode = mode
        self._matches: list[tuple[int, int]] = []
        self._current = -1
        self.setWindowTitle("置換" if mode == "replace" else "検索")
        self.setModal(False)
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet(f"QDialog {{ background: {C['bg_panel']}; }}")
        g = QGridLayout(self)
        g.setContentsMargins(16, 16, 16, 16)
        g.setSpacing(10)

        g.addWidget(QLabel("検索:"), 0, 0)
        self._search = QLineEdit()
        self._search.returnPressed.connect(self._find_next)
        g.addWidget(self._search, 0, 1, 1, 3)

        if self._mode == "replace":
            g.addWidget(QLabel("置換後:"), 1, 0)
            self._replace = QLineEdit()
            g.addWidget(self._replace, 1, 1, 1, 3)
        else:
            self._replace = QLineEdit()

        self._re_cb = QCheckBox("正規表現")
        self._case_cb = QCheckBox("大文字小文字を区別")
        g.addWidget(self._re_cb, 2, 0, 1, 2)
        g.addWidget(self._case_cb, 2, 2, 1, 2)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{C['border']}; max-height:1px; margin:2px 0;")
        g.addWidget(sep, 3, 0, 1, 4)

        btn_next = QPushButton("次を検索")
        btn_next.clicked.connect(self._find_next)
        g.addWidget(btn_next, 4, 0)

        if self._mode == "replace":
            b_repl = QPushButton("置換")
            b_repl.clicked.connect(self._replace_one)
            g.addWidget(b_repl, 4, 1)
            b_all = QPushButton("すべて置換")
            b_all.clicked.connect(self._replace_all)
            g.addWidget(b_all, 4, 2)
        else:
            b_prev = QPushButton("前を検索")
            b_prev.clicked.connect(self._find_prev)
            g.addWidget(b_prev, 4, 1)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{C['fg_dim']}; font-size:12px;")
        g.addWidget(self._status, 5, 0, 1, 4)
        self._search.setFocus()

    @staticmethod
    def _unescape(s: str) -> str:
        return s.replace("\\n", "\n").replace("\\t", "\t")

    def _pattern(self):
        raw = self._unescape(self._search.text())
        if not raw:
            return None
        if not self._re_cb.isChecked():
            raw = re.escape(raw)
        flags = 0 if self._case_cb.isChecked() else re.IGNORECASE
        try:
            return re.compile(raw, flags | re.DOTALL)
        except re.error as e:
            QMessageBox.critical(self, "正規表現エラー", str(e))
            return None

    def _collect(self) -> list[tuple[int, int]]:
        pat = self._pattern()
        if pat is None:
            return []
        return [(m.start(), m.end()) for m in pat.finditer(self._editor.toPlainText())]

    def _jump(self, start: int, end: int) -> None:
        cur = self._editor.textCursor()
        cur.setPosition(start)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self._editor.setTextCursor(cur)
        self._editor.ensureCursorVisible()

    def _set_status(self, text: str, ok: bool = True) -> None:
        self._status.setStyleSheet(
            f"color:{ C['fg_dim'] if ok else C['red'] }; font-size:12px;"
        )
        self._status.setText(text)

    def _find_next(self) -> None:
        self._matches = self._collect()
        if not self._matches:
            self._set_status("見つかりませんでした", ok=False)
            return
        self._current = (self._current + 1) % len(self._matches)
        self._jump(*self._matches[self._current])
        self._set_status(f"{self._current + 1} / {len(self._matches)} 件")

    def _find_prev(self) -> None:
        self._matches = self._collect()
        if not self._matches:
            self._set_status("見つかりませんでした", ok=False)
            return
        self._current = (self._current - 1) % len(self._matches)
        self._jump(*self._matches[self._current])
        self._set_status(f"{self._current + 1} / {len(self._matches)} 件")

    def _replace_one(self) -> None:
        pat = self._pattern()
        if pat is None:
            return
        cur = self._editor.textCursor()
        if cur.hasSelection():
            selected = cur.selectedText().replace(" ", "\n")
            if pat.fullmatch(selected):
                cur.insertText(self._unescape(self._replace.text()))
        self._find_next()

    def _replace_all(self) -> None:
        pat = self._pattern()
        if pat is None:
            return
        content = self._editor.toPlainText()
        new_content, count = pat.subn(self._unescape(self._replace.text()), content)
        if count:
            cursor = self._editor.textCursor()
            cursor.beginEditBlock()
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(new_content)
            cursor.endEditBlock()
            self._editor.setTextCursor(cursor)
        self._set_status(
            f"{count} 件置換しました" if count else "対象が見つかりませんでした",
            ok=bool(count),
        )


# ---------------------------------------------------------------------------
# Line number gutter
# ---------------------------------------------------------------------------
class _Gutter(QWidget):
    def __init__(self, editor: "CodeEditor"):
        super().__init__(editor)
        self._editor = editor
        self._drag_anchor: int = -1
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def sizeHint(self) -> QSize:
        return QSize(self._editor.gutter_width(), 0)

    def paintEvent(self, event):
        self._editor.paint_gutter(event)

    def _block_at_y(self, y: int):
        blk = self._editor.firstVisibleBlock()
        geo = self._editor.blockBoundingGeometry(blk).translated(self._editor.contentOffset())
        top = round(geo.top())
        while blk.isValid():
            h = round(self._editor.blockBoundingRect(blk).height())
            if top <= y < top + h:
                return blk
            top += h
            blk = blk.next()
        return None

    def _select_lines(self, b1, b2) -> None:
        if b1.blockNumber() > b2.blockNumber():
            b1, b2 = b2, b1
        cur = QTextCursor(b1)
        end = QTextCursor(b2)
        end.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        end.movePosition(QTextCursor.MoveOperation.NextCharacter)  # include newline
        cur.setPosition(b1.position())
        cur.setPosition(end.position(), QTextCursor.MoveMode.KeepAnchor)
        self._editor.setTextCursor(cur)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            blk = self._block_at_y(event.pos().y())
            if blk is not None and blk.isValid():
                self._drag_anchor = blk.blockNumber()
                self._select_lines(blk, blk)
                self._editor.setFocus()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_anchor >= 0:
            blk = self._block_at_y(event.pos().y())
            if blk is not None and blk.isValid():
                anchor = self._editor.document().findBlockByNumber(self._drag_anchor)
                self._select_lines(anchor, blk)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_anchor = -1
        super().mouseReleaseEvent(event)


class CodeEditor(QPlainTextEdit):
    """
    QPlainTextEdit with One Dark palette, line numbers, and kinsoku wrapping.
    Each instance carries its own file_path and file_encoding.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Per-tab file state
        self.file_path: str = ""
        self.file_encoding: str = "utf-8"

        self.setFont(QFont("Yu Gothic UI", 11))

        # One Dark palette
        p = self.palette()
        p.setColor(QPalette.ColorRole.Base,            QColor(C["bg"]))
        p.setColor(QPalette.ColorRole.Text,            QColor(C["fg"]))
        p.setColor(QPalette.ColorRole.Highlight,       QColor(C["select"]))
        p.setColor(QPalette.ColorRole.HighlightedText, QColor(C["fg"]))
        p.setColor(QPalette.ColorRole.Window,          QColor(C["bg"]))
        p.setColor(QPalette.ColorRole.WindowText,      QColor(C["fg"]))
        self.setPalette(p)

        # Kinsoku via Qt/ICU UAX#14
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.setCursorWidth(2)

        self._gutter = _Gutter(self)
        self.blockCountChanged.connect(self._update_gutter_width)
        self.updateRequest.connect(self._update_gutter)
        self.cursorPositionChanged.connect(self._highlight_line)

        self._update_gutter_width(0)
        self._highlight_line()

        # Middle-click auto-scroll
        self._autoscroll_active = False
        self._autoscroll_anchor = QPoint()
        self._scroll_accum = 0.0
        self._last_tick = 0.0
        self._as_cursor = self._make_autoscroll_cursor()
        self._autoscroll_timer = QTimer(self)
        self._autoscroll_timer.setInterval(16)
        self._autoscroll_timer.timeout.connect(self._do_autoscroll)

    # ------------------------------------------------------------------
    def gutter_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        return self.fontMetrics().horizontalAdvance("9") * digits + 24

    def _update_gutter_width(self, _) -> None:
        self.setViewportMargins(self.gutter_width(), 0, 0, 0)

    def _update_gutter(self, rect: QRect, dy: int) -> None:
        if dy:
            self._gutter.scroll(0, dy)
        else:
            self._gutter.update(0, rect.y(), self._gutter.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_gutter_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._gutter.setGeometry(
            QRect(cr.left(), cr.top(), self.gutter_width(), cr.height())
        )

    def _highlight_line(self) -> None:
        sel = QTextEdit.ExtraSelection()
        sel.format.setBackground(QColor(C["bg_hi"]))
        sel.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        # Select the entire logical block so FullWidthSelection covers all
        # wrapped visual lines, matching the gutter highlight height.
        cur = self.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cur.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                         QTextCursor.MoveMode.KeepAnchor)
        sel.cursor = cur
        self.setExtraSelections([sel])

    def paint_gutter(self, event) -> None:
        painter = QPainter(self._gutter)
        w = self._gutter.width()
        painter.fillRect(event.rect(), QColor(C["bg_panel"]))
        painter.setPen(QColor(C["border"]))
        painter.drawLine(w - 1, event.rect().top(), w - 1, event.rect().bottom())

        block = self.firstVisibleBlock()
        num = block.blockNumber()
        geo = self.blockBoundingGeometry(block).translated(self.contentOffset())
        top = round(geo.top())
        bottom = top + round(self.blockBoundingRect(block).height())
        cur = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                h = round(self.blockBoundingRect(block).height())
                if num == cur:
                    painter.fillRect(0, top, w - 1, h, QColor(C["bg_hi"]))
                    painter.setPen(QColor(C["fg"]))
                else:
                    painter.setPen(QColor(C["fg_dim"]))
                painter.setFont(self.font())
                painter.drawText(
                    QRect(0, top, w - 12, h),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    str(num + 1),
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            num += 1

    # ------------------------------------------------------------------
    # Middle-click auto-scroll
    # ------------------------------------------------------------------
    @staticmethod
    def _make_autoscroll_cursor() -> QCursor:
        px = QPixmap(32, 32)
        px.fill(Qt.GlobalColor.transparent)
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy, r = 16, 16, 7
        pen = QPen(QColor(30, 30, 30), 1.5)
        # Circle: white fill, dark border
        p.setPen(pen)
        p.setBrush(QColor(250, 250, 250))
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        # Arrows: white fill, dark border (visible on any background)
        p.setPen(pen)
        p.setBrush(QColor(250, 250, 250))
        p.drawPolygon(QPolygon([
            QPoint(cx,     cy - r - 5),
            QPoint(cx - 4, cy - r - 1),
            QPoint(cx + 4, cy - r - 1),
        ]))
        p.drawPolygon(QPolygon([
            QPoint(cx,     cy + r + 5),
            QPoint(cx - 4, cy + r + 1),
            QPoint(cx + 4, cy + r + 1),
        ]))
        # Center dot: dark
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(30, 30, 30))
        p.drawEllipse(cx - 2, cy - 2, 4, 4)
        p.end()
        return QCursor(px, cx, cy)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._start_autoscroll(event.position().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton and self._autoscroll_active:
            self._stop_autoscroll()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        cur = self.textCursor()
        has_sel  = cur.hasSelection()
        has_clip = self.canPaste()
        menu = QMenu(self)

        act = menu.addAction("元に戻す")
        act.setShortcut(QKeySequence.StandardKey.Undo)
        act.setEnabled(self.document().isUndoAvailable())
        act.triggered.connect(self.undo)

        act = menu.addAction("やり直し")
        act.setShortcut(QKeySequence.StandardKey.Redo)
        act.setEnabled(self.document().isRedoAvailable())
        act.triggered.connect(self.redo)

        menu.addSeparator()

        act = menu.addAction("切り取り")
        act.setShortcut(QKeySequence.StandardKey.Cut)
        act.setEnabled(has_sel)
        act.triggered.connect(self.cut)

        act = menu.addAction("コピー")
        act.setShortcut(QKeySequence.StandardKey.Copy)
        act.setEnabled(has_sel)
        act.triggered.connect(self.copy)

        act = menu.addAction("貼り付け")
        act.setShortcut(QKeySequence.StandardKey.Paste)
        act.setEnabled(has_clip)
        act.triggered.connect(self.paste)

        act = menu.addAction("削除")
        act.setEnabled(has_sel)
        act.triggered.connect(lambda: self.textCursor().removeSelectedText())

        menu.addSeparator()

        act = menu.addAction("すべて選択")
        act.setShortcut(QKeySequence.StandardKey.SelectAll)
        act.triggered.connect(self.selectAll)

        menu.exec(event.globalPos())

    def _start_autoscroll(self, local_pos: QPoint) -> None:
        self._autoscroll_active = True
        self._autoscroll_anchor = self.viewport().mapToGlobal(local_pos)
        self._scroll_accum = 0.0
        self._last_tick = time.monotonic()
        QApplication.setOverrideCursor(self._as_cursor)
        self._autoscroll_timer.start()

    def _stop_autoscroll(self) -> None:
        self._autoscroll_active = False
        self._autoscroll_timer.stop()
        QApplication.restoreOverrideCursor()

    def _do_autoscroll(self) -> None:
        now = time.monotonic()
        # Cap dt to 50 ms so a stalled timer never causes a sudden lurch
        dt = min(now - self._last_tick, 0.05)
        self._last_tick = now

        dy = QCursor.pos().y() - self._autoscroll_anchor.y()
        dead = 12  # px — dead zone around the anchor
        if abs(dy) <= dead:
            self._scroll_accum = 0.0
            return

        # Chromium-style: speed grows as dist^1.5 (gentle near anchor, fast far away)
        # Units: scrollbar steps/s  (1 step ≈ 1 visual line ≈ 20 px)
        dist = abs(dy) - dead
        speed = min((dist ** 1.5) * 0.15, 150.0)  # cap at 150 lines/s

        # Fractional accumulator — avoids the 0→1 snap and per-frame rounding loss
        self._scroll_accum += speed * dt * (1 if dy > 0 else -1)
        step = int(self._scroll_accum)
        if step:
            self._scroll_accum -= step
            bar = self.verticalScrollBar()
            bar.setValue(bar.value() + step)


# ---------------------------------------------------------------------------
# Project file tree
# ---------------------------------------------------------------------------
class FileTreePanel(QWidget):
    file_opened  = pyqtSignal(str)
    file_renamed = pyqtSignal(str, str)   # old_path, new_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_paths: list[str] = []
        self._lock_mgr: "FileLockManager | None" = None
        self._restoring = False
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_dir_changed)
        self._pending_refresh: set[str] = set()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(250)
        self._refresh_timer.timeout.connect(self._flush_refresh)
        self._dir_mtimes: dict[str, float] = {}
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(2000)
        self._poll_timer.timeout.connect(self._poll_dirs)
        self._poll_timer.start()
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self.setObjectName("file_tree_panel")
        self.setStyleSheet(f"#file_tree_panel {{ background:{C['bg_panel']}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tb = QWidget()
        tb_pal = tb.palette()
        tb_pal.setColor(QPalette.ColorRole.Window, QColor(C["bg_bar"]))
        tb.setPalette(tb_pal)
        tb.setAutoFillBackground(True)

        tb_row = QHBoxLayout(tb)
        tb_row.setContentsMargins(6, 4, 6, 4)
        tb_row.setSpacing(4)

        add_btn = QPushButton("フォルダの追加")
        add_btn.clicked.connect(self._add_folder)

        tb_row.addWidget(add_btn)
        tb_row.addStretch()
        layout.addWidget(tb)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{C['border']};")
        layout.addWidget(sep)

        self._model = QStandardItemModel()
        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setHeaderHidden(True)
        self._tree.setAnimated(True)
        self._tree.setIndentation(16)
        self._tree.expanded.connect(self._on_expand)
        self._tree.collapsed.connect(self._on_collapse)
        self._tree.clicked.connect(self._on_click)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        self._tree.installEventFilter(self)
        layout.addWidget(self._tree)

    def _load(self) -> None:
        cfg = _load_cfg()
        for path in cfg.get("project_folders", []):
            if os.path.isdir(path) and path not in self._root_paths:
                self._root_paths.append(path)
                self._insert_dir(path, self._model.invisibleRootItem())
                self._watcher.addPath(path)
        expanded = set(cfg.get("expanded_paths", []))
        if expanded:
            self._restore_expanded(expanded)

    def _persist(self) -> None:
        cfg = _load_cfg()
        cfg["project_folders"] = self._root_paths
        cfg["expanded_paths"] = self._expanded_paths()
        _save_cfg(cfg)

    def _expanded_paths(self) -> list[str]:
        result: list[str] = []
        def walk(parent: QStandardItem) -> None:
            for row in range(parent.rowCount()):
                item = parent.child(row)
                if item is None:
                    continue
                path = item.data(Qt.ItemDataRole.UserRole)
                if not path or path == "__dummy__":
                    continue
                idx = self._model.indexFromItem(item)
                if self._tree.isExpanded(idx):
                    result.append(path)
                    walk(item)
        walk(self._model.invisibleRootItem())
        return result

    def _restore_expanded(self, expanded: set[str]) -> None:
        self._restoring = True
        try:
            def walk(parent: QStandardItem) -> None:
                for row in range(parent.rowCount()):
                    item = parent.child(row)
                    if item is None:
                        continue
                    path = item.data(Qt.ItemDataRole.UserRole)
                    if not path or path == "__dummy__":
                        continue
                    if path in expanded:
                        idx = self._model.indexFromItem(item)
                        self._tree.setExpanded(idx, True)  # fires _on_expand → lazy-loads children
                        walk(item)  # recurse into now-loaded children
            walk(self._model.invisibleRootItem())
        finally:
            self._restoring = False

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if path and path not in self._root_paths:
            self._root_paths.append(path)
            self._insert_dir(path, self._model.invisibleRootItem())
            self._watcher.addPath(path)
            self._persist()

    def _remove_folder(self) -> None:
        idxs = self._tree.selectedIndexes()
        if not idxs:
            return
        idx = idxs[0]
        while idx.parent().isValid():
            idx = idx.parent()
        item = self._model.itemFromIndex(idx)
        path = item.data(Qt.ItemDataRole.UserRole)
        if path in self._root_paths:
            self._root_paths.remove(path)
            self._persist()
        self._model.removeRow(idx.row())

    @staticmethod
    def _dir_label(name: str, expanded: bool) -> str:
        return f"{'－' if expanded else '＋'} {name}"

    def _insert_dir(self, path: str, parent: QStandardItem) -> None:
        name = os.path.basename(path) or path
        item = QStandardItem(self._dir_label(name, expanded=False))
        item.setData(path, Qt.ItemDataRole.UserRole)
        item.setEditable(False)
        item.setForeground(QColor(C["accent"]))
        parent.appendRow(item)
        if self._has_children(path):
            dummy = QStandardItem("")
            dummy.setData("__dummy__", Qt.ItemDataRole.UserRole)
            dummy.setEditable(False)
            item.appendRow(dummy)

    @staticmethod
    def _has_children(path: str) -> bool:
        try:
            return any(True for _ in os.scandir(path))
        except PermissionError:
            return False

    def _on_expand(self, index: QModelIndex) -> None:
        item = self._model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and path != "__dummy__":
            item.setText(self._dir_label(os.path.basename(path) or path, expanded=True))
            self._watcher.addPath(path)   # 早期returnの前に登録

        if item.rowCount() != 1:
            return
        child = item.child(0)
        if not child or child.data(Qt.ItemDataRole.UserRole) != "__dummy__":
            return
        item.removeRow(0)
        try:
            for e in sorted(os.scandir(path), key=lambda x: (not x.is_dir(), x.name.lower())):
                if e.is_dir():
                    self._insert_dir(e.path, item)
                else:
                    fi = QStandardItem(f"   {e.name}")
                    fi.setData(e.path, Qt.ItemDataRole.UserRole)
                    fi.setForeground(QColor(C["fg"]))
                    fi.setEditable(False)
                    item.appendRow(fi)
        except PermissionError:
            pass
        if not self._restoring:
            self._persist()

    def _on_collapse(self, index: QModelIndex) -> None:
        item = self._model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and path != "__dummy__":
            item.setText(self._dir_label(os.path.basename(path) or path, expanded=False))
            # Stop watching non-root collapsed dirs to conserve watcher handles
            if path not in self._root_paths:
                self._watcher.removePath(path)
        if not self._restoring:
            self._persist()

    def _on_click(self, index: QModelIndex) -> None:
        item = self._model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path or path == "__dummy__":
            return
        if os.path.isdir(path):
            self._tree.setExpanded(index, not self._tree.isExpanded(index))
        elif os.path.isfile(path):
            self.file_opened.emit(path)

    # ------------------------------------------------------------------
    # File system watcher
    # ------------------------------------------------------------------
    def _find_item_by_path(self, path: str) -> "QStandardItem | None":
        norm = os.path.normcase(os.path.normpath(path))
        def walk(parent: QStandardItem) -> "QStandardItem | None":
            for row in range(parent.rowCount()):
                item = parent.child(row)
                if item is None:
                    continue
                p = item.data(Qt.ItemDataRole.UserRole)
                if p and p != "__dummy__" and os.path.normcase(os.path.normpath(p)) == norm:
                    return item
                found = walk(item)
                if found is not None:
                    return found
            return None
        return walk(self._model.invisibleRootItem())

    def _on_dir_changed(self, path: str) -> None:
        self._pending_refresh.add(os.path.normcase(os.path.normpath(path)))
        self._refresh_timer.start()

    def _poll_dirs(self) -> None:
        """Fallback: detect changes missed by QFileSystemWatcher."""
        for path in list(self._watcher.directories()):
            try:
                mtime = os.stat(path).st_mtime
            except OSError:
                continue
            prev = self._dir_mtimes.get(path)
            self._dir_mtimes[path] = mtime
            if prev is not None and mtime != prev:
                self._on_dir_changed(path)

    def _flush_refresh(self) -> None:
        paths = list(self._pending_refresh)
        self._pending_refresh.clear()
        for norm_path in paths:
            item = self._find_item_by_path(norm_path)
            if item is None:
                continue
            idx = self._model.indexFromItem(item)
            if self._tree.isExpanded(idx):
                self._reload_dir_item(item)
            else:
                has = self._has_children(norm_path)
                if has and item.rowCount() == 0:
                    dummy = QStandardItem("")
                    dummy.setData("__dummy__", Qt.ItemDataRole.UserRole)
                    dummy.setEditable(False)
                    item.appendRow(dummy)
                elif not has and item.rowCount() > 0:
                    item.removeRows(0, item.rowCount())

    # ------------------------------------------------------------------
    # Key events
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if obj is self._tree:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_F2:
                    idxs = self._tree.selectedIndexes()
                    if idxs:
                        item = self._model.itemFromIndex(idxs[0])
                        path = item.data(Qt.ItemDataRole.UserRole) if item else None
                        if path and path != "__dummy__" and not self._is_root_item(item):
                            self._rename_item(path, item)
                            return True
        return super().eventFilter(obj, event)


    # ------------------------------------------------------------------
    # Context menu
    # ------------------------------------------------------------------
    def _item_at(self, pos: QPoint):
        index = self._tree.indexAt(pos)
        if not index.isValid():
            return None, None
        item = self._model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not path or path == "__dummy__":
            return None, None
        return item, path

    def _is_root_item(self, item: QStandardItem) -> bool:
        return not self._model.indexFromItem(item).parent().isValid()

    def _show_context_menu(self, pos: QPoint) -> None:
        item, path = self._item_at(pos)
        is_dir  = bool(path and os.path.isdir(path))
        is_root = bool(item and self._is_root_item(item))

        menu = QMenu(self)

        act_add = menu.addAction("＋ プロジェクトフォルダを追加")
        act_add.triggered.connect(self._add_folder)

        if is_root:
            act_ex = menu.addAction("このフォルダをプロジェクトから除外する")
            act_ex.triggered.connect(lambda _=False, i=item: self._remove_by_item(i))

        if is_dir:
            menu.addSeparator()
            act_nf = menu.addAction("新規フォルダを作成")
            act_nf.triggered.connect(lambda _=False, p=path, i=item: self._new_folder(p, i))
            act_nt = menu.addAction("新規テキストファイルを作成")
            act_nt.triggered.connect(lambda _=False, p=path, i=item: self._new_text_file(p, i))

        if path and not is_root:
            menu.addSeparator()
            act_rn = menu.addAction("名前を変更")
            act_rn.triggered.connect(lambda _=False, p=path, i=item: self._rename_item(p, i))
            act_del = menu.addAction("削除")
            act_del.triggered.connect(lambda _=False, p=path, i=item: self._delete_item(p, i))

        if path:
            menu.addSeparator()
            target = path if is_dir else os.path.dirname(path)
            act_exp = menu.addAction("エクスプローラーで開く")
            act_exp.triggered.connect(lambda _=False, t=target: os.startfile(t))

        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _remove_by_item(self, item: QStandardItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path in self._root_paths:
            self._root_paths.remove(path)
        self._watcher.removePath(path)
        idx = self._model.indexFromItem(item)
        self._model.removeRow(idx.row())
        self._persist()

    def _reload_dir_item(self, item: QStandardItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path or not os.path.isdir(path):
            return
        idx = self._model.indexFromItem(item)
        was_expanded = self._tree.isExpanded(idx)
        item.removeRows(0, item.rowCount())
        if was_expanded:
            try:
                for e in sorted(os.scandir(path), key=lambda x: (not x.is_dir(), x.name.lower())):
                    if e.is_dir():
                        self._insert_dir(e.path, item)
                    else:
                        fi = QStandardItem(f"   {e.name}")
                        fi.setData(e.path, Qt.ItemDataRole.UserRole)
                        fi.setForeground(QColor(C["fg"]))
                        fi.setEditable(False)
                        item.appendRow(fi)
            except PermissionError:
                pass
            self._tree.setExpanded(idx, True)
        elif self._has_children(path):
            dummy = QStandardItem("")
            dummy.setData("__dummy__", Qt.ItemDataRole.UserRole)
            dummy.setEditable(False)
            item.appendRow(dummy)

    def _new_folder(self, parent_path: str, parent_item: QStandardItem) -> None:
        name, ok = QInputDialog.getText(self, "新規フォルダ", "フォルダ名:")
        if not ok or not name.strip():
            return
        new_path = os.path.join(parent_path, name.strip())
        try:
            os.makedirs(new_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "エラー", str(e))
            return
        self._reload_dir_item(parent_item)
        self._persist()

    def _new_text_file(self, parent_path: str, parent_item: QStandardItem) -> None:
        name, ok = QInputDialog.getText(self, "新規テキストファイル", "ファイル名:", text="新規ファイル.txt")
        if not ok or not name.strip():
            return
        new_path = os.path.join(parent_path, name.strip())
        if os.path.exists(new_path):
            QMessageBox.warning(self, "警告", "同名のファイルが既に存在します。")
            return
        try:
            with open(new_path, "w", encoding="utf-8"):
                pass
        except OSError as e:
            QMessageBox.critical(self, "エラー", str(e))
            return
        self._reload_dir_item(parent_item)
        self._persist()
        self.file_opened.emit(new_path)

    def _rename_item(self, path: str, item: QStandardItem) -> None:
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "名前を変更", "新しい名前:", text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_path = os.path.join(os.path.dirname(path), new_name.strip())
        if os.path.exists(new_path):
            QMessageBox.warning(self, "警告", "同名のファイルまたはフォルダが既に存在します。")
            return
        # エディターで開いている場合、リネーム前にロックを一時解放する
        was_locked = self._lock_mgr is not None and self._lock_mgr.temp_unlock(path)
        try:
            os.rename(path, new_path)
        except OSError as e:
            if was_locked:
                self._lock_mgr.restore_lock(path)
            QMessageBox.critical(self, "エラー", str(e))
            return
        # リネーム成功: 新パスへロック移転 & タブ更新を親に通知
        self.file_renamed.emit(path, new_path)
        parent_qitem = item.parent()
        if parent_qitem:
            self._reload_dir_item(parent_qitem)
        self._persist()

    def _delete_item(self, path: str, item: QStandardItem) -> None:
        name = os.path.basename(path)
        kind = "フォルダ" if os.path.isdir(path) else "ファイル"
        ans = QMessageBox.question(
            self, "削除の確認",
            f"{kind}「{name}」を削除しますか？\nこの操作は元に戻せません。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as e:
            QMessageBox.critical(self, "エラー", str(e))
            return
        parent_qitem = item.parent()
        if parent_qitem:
            self._reload_dir_item(parent_qitem)
        self._persist()


# ---------------------------------------------------------------------------
# RubyTextObject — QTextObjectInterface でルビをインライン描画
# ---------------------------------------------------------------------------
class RubyTextObject(QObject, QTextObjectInterface):
    """
    Qt rich text engine はネイティブ <ruby> 未対応のため、
    QTextObjectInterface でインラインオブジェクトとして描画する。
    intrinsicSize.height = body_fm.ascent() として行高さへの影響をゼロにする。
    読み仮名の描画は PreviewBrowser.paintEvent のオーバーレイで行う。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nudge: int = 3  # px: 読み仮名を下方向へオフセット（テーマごとに上書き）

    def intrinsicSize(self, doc, posInDocument, fmt):
        base    = fmt.property(_PROP_BASE)    or ""
        reading = fmt.property(_PROP_READING) or ""
        body_fm = QFontMetricsF(doc.defaultFont())
        rt_font = QFont(doc.defaultFont())
        rt_font.setPixelSize(_RUBY_RT_PX)
        rt_fm   = QFontMetricsF(rt_font)
        w = max(body_fm.horizontalAdvance(base),
                rt_fm.horizontalAdvance(reading))
        h = body_fm.ascent()
        return QSizeF(w, h)

    def drawObject(self, painter, rect, doc, posInDocument, fmt):
        base      = fmt.property(_PROP_BASE) or ""
        body_font = doc.defaultFont()
        body_fm   = QFontMetricsF(body_font)
        w = rect.width()
        painter.save()
        painter.setFont(body_font)
        x_base = rect.x() + (w - body_fm.horizontalAdvance(base)) / 2.0
        painter.drawText(QPointF(x_base, rect.bottom()), base)
        painter.restore()


# ---------------------------------------------------------------------------
# PreviewBrowser — QTextBrowser ベースのルビ対応プレビューウィジェット
# ---------------------------------------------------------------------------
class PreviewBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme: dict = _THEMES["narou"]
        self.setOpenLinks(False)
        self.setReadOnly(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # システムテーマ（Windows ダークモード等）に依存しないよう背景色を固定する
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(self._theme["bg"]))
        self.setPalette(pal)

        self._ruby_obj = RubyTextObject(self)
        self._ruby_obj.nudge = self._theme.get("ruby_nudge", 3)
        self.document().documentLayout().registerHandler(
            _RUBY_OBJ_TYPE, self._ruby_obj)

        self.document().setUndoRedoEnabled(False)

        # ルビ位置をブロック番号 + ブロック内オフセットで管理
        # (block_num, pos_in_block, base, reading)
        self._rubies: list[tuple[int, int, str, str]] = []
        # 差分更新用キャッシュ
        self._line_cache: list[str] = []
        self._title_cache: str = ""
        self._body_block: QTextBlockFormat | None = None
        self._body_char: QTextCharFormat | None = None
        # 遅延レンダリング管理
        self._rendered: set[int] = set()
        self._line_height_px: float = 0.0
        self._title_height_px: float = 0.0
        # _apply_margins のキャッシュ（同マージンで setFrameFormat を呼ばないため）
        self._margin_side_cache: int | None = None

    def set_theme(self, theme_id: str) -> None:
        self._theme = _THEMES.get(theme_id, _THEMES["narou"])
        self._ruby_obj.nudge = self._theme.get("ruby_nudge", 3)
        self.setMinimumWidth(_PREVIEW_MIN_W)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(self._theme["bg"]))
        self.setPalette(pal)
        # テーマ変更時は次回更新で全再構築させる
        self._body_block = None
        self._line_cache = []
        self._title_cache = ""
        self._rendered.clear()
        self._margin_side_cache = None

    def _make_body_formats(self) -> tuple[QTextBlockFormat, QTextCharFormat, QFont]:
        th = self._theme
        body_font = QFont(th["font_qt"])
        body_font.setPixelSize(round(th["font_px"]))
        body_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        body_char = QTextCharFormat()
        body_char.setFont(body_font)
        body_char.setForeground(QColor(th["fg"]))
        body_block = QTextBlockFormat()
        body_block.setTopMargin(0)
        body_block.setBottomMargin(0)
        # FixedHeight (type=2): CSS line-height と同じ計算（font_px × line_height px）
        body_block.setLineHeight(round(th["font_px"] * th["line_height"]), 2)
        return body_block, body_char, body_font

    def _update_line(self, line_idx: int, new_line: str) -> None:
        """レンダリング済みの1行をドキュメント内で差し替える。未レンダリング行はスキップ。"""
        if line_idx not in self._rendered:
            return
        title_offset = 1 if self._title_cache.strip() else 0
        block_num = line_idx + title_offset
        doc = self.document()
        block = doc.findBlockByNumber(block_num)
        if not block.isValid():
            return
        self._rubies = [r for r in self._rubies if r[0] != block_num]
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                            QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.setBlockFormat(self._body_block)
        cursor.setCharFormat(self._body_char)
        self._insert_line(cursor, new_line, self._body_char)

    def update_preview(self, body: str, title: str = "") -> bool:
        """プレビューを更新する。
        True  = 全再構築（_sync_scene_rect が必要）
        False = 再描画のみ or 変化なし
        """
        new_lines = body.split("\n")

        # 変化なし
        if (self._body_block is not None
                and title == self._title_cache
                and new_lines == self._line_cache):
            return False

        # ── 行数・タイトル変化なし → QTextDocument の構造はそのまま ──────────
        # _rendered をクリアして _trigger_render に可視行の再描画を委ねる。
        # doc.clear() + insertText("\n"*(N-1)) の O(N log N) Qt 操作をスキップ。
        if (self._body_block is not None
                and title == self._title_cache
                and len(new_lines) == len(self._line_cache)):
            self._line_cache = new_lines
            self._rendered.clear()
            return False  # 高さ変化なし → _sync_scene_rect 不要

        # ── 全再構築パス（行数変化・タイトル変化・初回）──────────────────────
        th = self._theme
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor(th["bg"]))
        pal.setColor(QPalette.ColorRole.Text, QColor(th["fg"]))
        self.setPalette(pal)

        body_block, body_char, body_font = self._make_body_formats()
        self._body_block = body_block
        self._body_char  = body_char

        doc = self.document()
        doc.setDefaultFont(body_font)
        doc.clear()
        self._rubies.clear()
        self._rendered.clear()
        self._margin_side_cache = None  # doc.clear() でフレーム書式がリセットされるため
        cursor = QTextCursor(doc)

        # フレームtopMargin=20 を基準にタイトルブロック高さを計算
        title_h = 20.0
        if title.strip():
            t_font = QFont(th["font_qt"])
            t_font.setPixelSize(round(th["title_px"]))
            t_font.setBold(th["title_weight"] == "bold")
            t_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)

            t_char = QTextCharFormat()
            t_char.setFont(t_font)
            t_char.setForeground(QColor(th["title_fg"]))

            t_block = QTextBlockFormat()
            t_block.setTopMargin(th["title_mt"])
            t_block.setBottomMargin(th["title_mb"])
            t_block.setLineHeight(round(th["title_px"] * th["title_lh"]), 2)
            _ALIGN = {
                "center": Qt.AlignmentFlag.AlignHCenter,
                "right":  Qt.AlignmentFlag.AlignRight,
                "left":   Qt.AlignmentFlag.AlignLeft,
            }
            t_block.setAlignment(_ALIGN.get(th["title_align"],
                                             Qt.AlignmentFlag.AlignLeft))

            cursor.setBlockFormat(t_block)
            cursor.setCharFormat(t_char)
            cursor.insertText(title.strip())
            cursor.insertBlock(body_block, body_char)

            title_h += (round(th["title_px"] * th["title_lh"])
                        + th["title_mt"] + th["title_mb"])

        # 全ボディブロックをプレースホルダー（空）として一括挿入。
        # insertBlock を N 回ループすると O(N²) になるため、
        # "\n" * (N-1) の一括 insertText でブロック分割を1回のレイアウト更新に集約する。
        cursor.setBlockFormat(body_block)
        cursor.setCharFormat(body_char)
        if len(new_lines) > 1:
            cursor.insertText("\n" * (len(new_lines) - 1))

        self._line_cache      = list(new_lines)
        self._title_cache     = title
        self._line_height_px  = float(round(th["font_px"] * th["line_height"]))
        self._title_height_px = title_h
        self._apply_margins()
        return True

    def update_dirty_lines(self, dirty: dict[int, str]) -> bool:
        """指定行のみ差分更新する。全再構築が必要な場合は True を返す。"""
        if self._body_block is None or not self._line_cache:
            return True
        if any(i < 0 or i >= len(self._line_cache) for i in dirty):
            return True
        for line_idx, text in dirty.items():
            self._line_cache[line_idx] = text
            self._update_line(line_idx, text)
        return False

    def render_range(self, first_line: int, last_line: int) -> bool:
        """first_line..last_line の未レンダリング行をドキュメントに書き込む。
        1行でも書いたら True を返す。"""
        if not self._line_cache or self._line_height_px == 0:
            return False
        n = len(self._line_cache)
        first_line = max(0, first_line)
        last_line  = min(n - 1, last_line)
        if first_line > last_line:
            return False
        title_offset = 1 if self._title_cache.strip() else 0
        doc = self.document()
        rendered_any = False
        for line_idx in range(first_line, last_line + 1):
            if line_idx in self._rendered:
                continue
            block_num = line_idx + title_offset
            block = doc.findBlockByNumber(block_num)
            if not block.isValid():
                continue
            self._rubies = [r for r in self._rubies if r[0] != block_num]
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                                QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.setBlockFormat(self._body_block)
            cursor.setCharFormat(self._body_char)
            self._insert_line(cursor, self._line_cache[line_idx], self._body_char)
            self._rendered.add(line_idx)
            rendered_any = True
        return rendered_any

    def _insert_line(self, cursor: QTextCursor,
                     line: str, base_fmt: QTextCharFormat) -> None:
        s = line.rstrip()
        if not s:
            return

        if _RE_HR_LINE.match(s):
            hr_fmt = QTextCharFormat(base_fmt)
            hr_fmt.setForeground(QColor("#999999"))
            hr_block = QTextBlockFormat(cursor.blockFormat())
            hr_block.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            cursor.setBlockFormat(hr_block)
            cursor.setCharFormat(hr_fmt)
            cursor.insertText(s)
            return

        segs: list[tuple[int, int, str, re.Match]] = []
        for pat, kind in (
            (_RE_EMPH_PIXIV_RAW, "emph_pixiv"),
            (_RE_EMPH,           "emph"),
            (_RE_RUBY_PIXIV_RAW, "ruby"),
            (_RE_RUBY1,          "ruby"),
            (_RE_RUBY2,          "ruby"),
        ):
            for m in pat.finditer(s):
                segs.append((m.start(), m.end(), kind, m))
        segs.sort(key=lambda x: x[0])

        filtered: list[tuple[int, int, str, re.Match]] = []
        pos = 0
        for seg in segs:
            if seg[0] >= pos:
                filtered.append(seg)
                pos = seg[1]

        text_pos = 0
        for start, end, kind, m in filtered:
            if start > text_pos:
                cursor.setCharFormat(base_fmt)
                cursor.insertText(s[text_pos:start])

            if kind == "ruby":
                self._insert_ruby(cursor, m.group(1), m.group(2).strip(), base_fmt)
            elif kind == "emph":
                for c in m.group(1):
                    self._insert_ruby(cursor, c, "・", base_fmt)
            elif kind == "emph_pixiv":
                dot = m.group(2).strip() or "﹅"
                for c in m.group(1).strip():
                    self._insert_ruby(cursor, c, dot, base_fmt)

            text_pos = end

        if text_pos < len(s):
            cursor.setCharFormat(base_fmt)
            cursor.insertText(s[text_pos:])

    def _insert_ruby(self, cursor: QTextCursor,
                     base: str, reading: str,
                     base_fmt: QTextCharFormat) -> None:
        # \u30D6\u30ED\u30C3\u30AF\u756A\u53F7 + \u30D6\u30ED\u30C3\u30AF\u5185\u30AA\u30D5\u30BB\u30C3\u30C8\u3067\u8A18\u9332\uFF08\u4ED6\u30D6\u30ED\u30C3\u30AF\u7DE8\u96C6\u306E\u5F71\u97FF\u3092\u53D7\u3051\u306A\u3044\uFF09
        self._rubies.append((cursor.blockNumber(), cursor.positionInBlock(), base, reading))
        fmt = QTextCharFormat(base_fmt)
        fmt.setObjectType(_RUBY_OBJ_TYPE)
        fmt.setProperty(_PROP_BASE,    base)
        fmt.setProperty(_PROP_READING, reading)
        cursor.insertText("\uFFFC", fmt)   # U+FFFC Object Replacement Character

    def _apply_margins(self) -> None:
        th = self._theme
        vw = self.viewport().width()
        side = max(16, (vw - th["content_w"]) // 2)
        if self._margin_side_cache == side:
            return  # マージン変化なし → setFrameFormat による O(N) 再レイアウトを回避
        self._margin_side_cache = side
        fmt = QTextFrameFormat()
        fmt.setLeftMargin(side)
        fmt.setRightMargin(side)
        fmt.setTopMargin(20)
        fmt.setBottomMargin(40)
        self.document().rootFrame().setFrameFormat(fmt)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self._rubies:
            return

        doc     = self.document()
        body_fm = QFontMetricsF(doc.defaultFont())
        rt_font = QFont(doc.defaultFont())
        rt_font.setPixelSize(_RUBY_RT_PX)
        rt_fm   = QFontMetricsF(rt_font)
        nudge   = self._ruby_obj.nudge

        painter = QPainter(self.viewport())
        painter.translate(QPointF(-self.horizontalScrollBar().value(),
                                  -self.verticalScrollBar().value()))
        painter.setFont(rt_font)
        painter.setPen(self.palette().color(QPalette.ColorRole.Text))

        for block_num, pos_in_block, base, reading in self._rubies:
            block = doc.findBlockByNumber(block_num)
            if not block.isValid():
                continue
            layout = block.layout()
            if layout is None:
                continue
            line = layout.lineForTextPosition(pos_in_block)
            if not line.isValid():
                continue
            lx    = line.cursorToX(pos_in_block)[0]
            obj_w = max(body_fm.horizontalAdvance(base),
                        rt_fm.horizontalAdvance(reading))
            rt_w  = rt_fm.horizontalAdvance(reading)
            doc_x = layout.position().x() + lx + (obj_w - rt_w) / 2.0
            baseline = (layout.position().y()
                        + line.position().y()
                        + line.ascent())
            doc_y = baseline - body_fm.ascent() - rt_fm.descent() + nudge
            painter.drawText(QPointF(doc_x, doc_y), reading)

        painter.end()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_margins()


# ---------------------------------------------------------------------------
# _PreviewScaleView — QGraphicsView wrapper that visually scales PreviewBrowser
# without changing any font or document settings.
# ---------------------------------------------------------------------------
class _PreviewScaleView(QGraphicsView):
    """
    PreviewBrowser を QGraphicsScene にのせ、setTransform() でスケーリングする。
    フォントサイズ・テーマ設定は一切変更せず、描画のみを拡大縮小する。
    """

    _SCALE_OPTIONS: list[tuple[str, float]] = [
        ("100%", 1.00),
        ("75%",  0.75),
        ("50%",  0.50),
        ("25%",  0.25),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0

        self._browser = PreviewBrowser()
        # 常に自然幅で描画させる。スクロールバーはView側に任せる
        self._browser.setFixedWidth(_PREVIEW_MIN_W)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scene = QGraphicsScene(self)
        self.setScene(scene)
        self._proxy = scene.addWidget(self._browser)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setBackgroundBrush(self._browser.palette().base())

        self._browser.document().documentLayout().documentSizeChanged.connect(
            self._sync_scene_rect
        )
        self._rendering = False
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    @property
    def browser(self) -> PreviewBrowser:
        return self._browser

    # ------------------------------------------------------------------
    # Delegate PreviewBrowser API
    # ------------------------------------------------------------------
    def update_dirty_lines(self, dirty: dict[int, str]) -> bool:
        """差分行のみ更新する。全再構築が必要な場合は True を返す。"""
        layout = self._browser.document().documentLayout()
        layout.blockSignals(True)
        try:
            needs_rebuild = self._browser.update_dirty_lines(dirty)
        finally:
            layout.blockSignals(False)
        if not needs_rebuild:
            self._trigger_render()
        return needs_rebuild

    def update_preview(self, body: str, title: str = "") -> None:
        layout = self._browser.document().documentLayout()
        layout.blockSignals(True)
        try:
            full_rebuild = self._browser.update_preview(body, title)
        finally:
            layout.blockSignals(False)
        # 全再構築時のみ _sync_scene_rect を直接呼ぶ。
        # 差分更新時は document().size() の O(N) レイアウト再計算を避け、
        # 高さ変化が生じた場合は _trigger_render 内の _sync_scene_rect が補完する。
        if full_rebuild:
            self._sync_scene_rect()
        self._trigger_render()

    def set_theme(self, theme_id: str) -> None:
        self._browser.set_theme(theme_id)
        bg = self._browser.palette().color(QPalette.ColorRole.Base)
        self.setBackgroundBrush(bg)
        self._sync_scene_rect()

    # ------------------------------------------------------------------
    # Scale
    # ------------------------------------------------------------------
    def set_scale(self, factor: float) -> None:
        self._scale = factor
        t = QTransform()
        t.scale(factor, factor)
        self.setTransform(t)
        self.updateGeometry()   # レイアウトに最小サイズの再評価を通知
        self._sync_scene_rect()
        self._trigger_render()

    @property
    def scale_factor(self) -> float:
        return self._scale

    def minimumSizeHint(self) -> QSize:
        return QSize(max(200, round(_PREVIEW_MIN_W * self._scale)), 200)

    def sizeHint(self) -> QSize:
        return QSize(round(_PREVIEW_MIN_W * self._scale), 600)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _sync_scene_rect(self) -> None:
        """ブラウザの文書高さに合わせてシーンサイズを更新する。"""
        br = self._browser
        n  = len(br._line_cache)
        lh = br._line_height_px
        if n > 0 and lh > 0:
            # FixedHeight ブロックの高さは数式で確定できる → Qt の O(N) レイアウト計算を回避
            # document().size() = _title_height_px + N × lineHeight + frameBottomMargin(40)
            # +40 は旧実装の document().size() + 40 に合わせたコンテンツ下余白
            doc_h = br._title_height_px + n * lh + 40.0
        else:
            doc_h = float(br.document().size().height())
        min_h = self.viewport().height() / self._scale if self._scale > 0 else doc_h
        h = max(doc_h + 40, min_h)  # +40: コンテンツ末尾に余白を確保（旧実装と同一）
        h_int = int(h)
        if br.height() != h_int:
            br.setFixedHeight(h_int)  # 高さ変化時のみ setFixedHeight（resizeEvent 抑制）
        self.setSceneRect(QRectF(0, 0, _PREVIEW_MIN_W, h))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_scene_rect()
        self._trigger_render()

    # ------------------------------------------------------------------
    # Lazy rendering
    # ------------------------------------------------------------------
    def _visible_line_range(self) -> tuple[int, int]:
        """現在の表示範囲 ±2倍バッファに対応する行番号範囲を返す。"""
        br = self._browser
        n = len(br._line_cache)
        if n == 0 or br._line_height_px <= 0:
            return (0, -1)
        # QGraphicsView のスクロール値はビューポートピクセル座標 → スケールで割ってシーン座標に変換
        doc_top = float(self.verticalScrollBar().value()) / max(self._scale, 0.01)
        doc_vis = self.viewport().height() / max(self._scale, 0.01)
        buffer  = doc_vis * 2.0
        title_h = br._title_height_px
        lh      = br._line_height_px
        first = max(0, int((doc_top - buffer - title_h) / lh))
        last  = min(n - 1, int((doc_top + doc_vis + buffer - title_h) / lh) + 1)
        return (first, last)

    def _trigger_render(self) -> None:
        """可視範囲 ±2画面バッファの未レンダリング行を書き込む。"""
        if self._rendering:
            return
        self._rendering = True
        try:
            first, last = self._visible_line_range()
            if first > last:
                return
            layout = self._browser.document().documentLayout()
            layout.blockSignals(True)
            try:
                rendered = self._browser.render_range(first, last)
            finally:
                layout.blockSignals(False)
            if rendered:
                self._sync_scene_rect()
                # blockSignals により layout の update(rect) シグナルが抑制されているため
                # 明示的に再描画を要求する（QGraphicsProxyWidget 経由でも確実に反映）
                self.scene().update()
        finally:
            self._rendering = False

    def _on_scroll(self) -> None:
        self._trigger_render()


# ---------------------------------------------------------------------------
# Preview panel (embeddable widget — toolbar + viewer + autoscroll)
# ---------------------------------------------------------------------------
class PreviewPane(QWidget):
    """Toolbar + content panel. Works both embedded in the main splitter
    (dock mode) and as the inner widget of a floating PreviewWindow."""
    closed        = pyqtSignal()
    theme_changed = pyqtSignal()
    dock_toggled  = pyqtSignal()
    zoom_changed  = pyqtSignal(float)   # フロート/ドック共通のズーム変更通知

    def __init__(self, parent=None):
        super().__init__(parent)

        _cfg = _load_cfg()
        self._theme_id = _cfg.get("preview_theme", "narou")
        self._zoom_idx_init = _cfg.get("preview_zoom_idx", 0)

        self._autoscroll_active = False
        self._autoscroll_anchor = QPoint()
        self._scroll_accum      = 0.0
        self._last_tick         = 0.0
        self._as_cursor         = CodeEditor._make_autoscroll_cursor()
        self._autoscroll_timer  = QTimer(self)
        self._autoscroll_timer.setInterval(16)
        self._autoscroll_timer.timeout.connect(self._do_autoscroll)

        self._build_ui()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    @property
    def theme_id(self) -> str:
        return self._theme_id

    def set_content(self, body: str, title: str = "") -> None:
        self._view.update_preview(body, title)

    def update_dirty_lines(self, dirty: dict[int, str], title: str) -> bool:
        """差分行のみ更新する。タイトル変化・キャッシュ不整合なら True（全再構築要）を返す。"""
        browser = self._view.browser
        if title != browser._title_cache:
            return True
        return self._view.update_dirty_lines(dirty)

    def sync_theme(self) -> None:
        """Re-read config theme and update combo silently (no signal emit)."""
        theme_id = _load_cfg().get("preview_theme", "narou")
        if theme_id == self._theme_id:
            return
        self._theme_id = theme_id
        idx = _THEME_ORDER.index(theme_id) if theme_id in _THEME_ORDER else 0
        self._theme_combo.blockSignals(True)
        self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.blockSignals(False)
        self._view.set_theme(theme_id)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QWidget          { color: #333; }
            #previewToolbar  { background: #f0f0f0; border-bottom: 1px solid #d0d0d0; }
            #previewFooter   { background: #f0f0f0; border-top:    1px solid #d0d0d0; }
            QLabel           { color: #333; background: transparent; }
            QComboBox {
                background: #fff; border: 1px solid #bbb; border-radius: 3px;
                padding: 2px 8px; font-size: 12px; color: #333; min-width: 150px;
            }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox QAbstractItemView {
                background: #fff; color: #333; selection-background-color: #cde;
            }
            QPushButton#dockBtn {
                background: #e8e8e8; border: 1px solid #bbb; border-radius: 3px;
                padding: 0 10px; height: 24px; font-size: 11px; color: #555;
            }
            QPushButton#dockBtn:hover { background: #d8d8d8; }
            QPushButton#zoomBtn {
                background: #e8e8e8; border: 1px solid #bbb; border-radius: 3px;
                width: 24px; height: 24px; font-size: 14px; color: #444; padding: 0;
            }
            QPushButton#zoomBtn:hover   { background: #d0d0d0; }
            QPushButton#zoomBtn:pressed { background: #b8b8b8; }
            QPushButton#zoomBtn:disabled { color: #bbb; background: #ebebeb; border-color: #d0d0d0; }
            QLabel#zoomLabel { font-size: 12px; color: #555; min-width: 42px; }
            QScrollBar:vertical {
                background: #f0f0f0; width: 12px; border: none; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0; border-radius: 6px; min-height: 28px; margin: 2px;
            }
            QScrollBar::handle:vertical:hover { background: #a0a0a0; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        # ── 上部ツールバー ──────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setObjectName("previewToolbar")
        toolbar.setFixedHeight(38)
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(10, 0, 10, 0)
        tl.setSpacing(8)

        lbl = QLabel("表示形式:")
        lbl.setStyleSheet("font-size:12px;")
        tl.addWidget(lbl)

        self._theme_combo = QComboBox()
        for tid in _THEME_ORDER:
            self._theme_combo.addItem(_THEMES[tid]["label"], tid)
        cur_idx = _THEME_ORDER.index(self._theme_id) if self._theme_id in _THEME_ORDER else 0
        self._theme_combo.setCurrentIndex(cur_idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        tl.addWidget(self._theme_combo)
        tl.addStretch()

        self._dock_btn = QPushButton("ドッキング")
        self._dock_btn.setObjectName("dockBtn")
        self._dock_btn.setFixedHeight(24)
        self._dock_btn.clicked.connect(self.dock_toggled)
        tl.addWidget(self._dock_btn)

        # ── プレビュー本体 ──────────────────────────────────────────────
        self._view = _PreviewScaleView()
        self._view.set_theme(self._theme_id)

        # ── 下部ズームバー ──────────────────────────────────────────────
        n = len(_PreviewScaleView._SCALE_OPTIONS)
        self._zoom_idx = max(0, min(self._zoom_idx_init, n - 1))

        footer = QWidget()
        footer.setObjectName("previewFooter")
        footer.setFixedHeight(32)
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(10, 0, 10, 0)
        fl.setSpacing(4)
        fl.addStretch()

        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setObjectName("zoomBtn")
        self._zoom_out_btn.setFixedSize(24, 24)
        self._zoom_out_btn.clicked.connect(self._zoom_out)
        fl.addWidget(self._zoom_out_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setObjectName("zoomLabel")
        self._zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl.addWidget(self._zoom_label)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setObjectName("zoomBtn")
        self._zoom_in_btn.setFixedSize(24, 24)
        self._zoom_in_btn.clicked.connect(self._zoom_in)
        fl.addWidget(self._zoom_in_btn)

        self._update_zoom_ui()
        if self._zoom_idx != 0:
            _, factor = _PreviewScaleView._SCALE_OPTIONS[self._zoom_idx]
            self._view.set_scale(factor)

        # ── レイアウト ──────────────────────────────────────────────────
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(toolbar)
        outer.addWidget(self._view, 1)
        outer.addWidget(footer)

    def set_dock_mode(self, docked: bool) -> None:
        self._dock_btn.setText("独立ウィンドウ" if docked else "ドッキング")

    @property
    def current_zoom_factor(self) -> float:
        return _PreviewScaleView._SCALE_OPTIONS[self._zoom_idx][1]

    def _on_theme_changed(self, index: int) -> None:
        self._theme_id = self._theme_combo.itemData(index)
        cfg = _load_cfg()
        cfg["preview_theme"] = self._theme_id
        _save_cfg(cfg)
        self._view.set_theme(self._theme_id)
        self.theme_changed.emit()

    def _zoom_in(self) -> None:
        if self._zoom_idx > 0:
            self._zoom_idx -= 1
            self._apply_zoom()

    def _zoom_out(self) -> None:
        if self._zoom_idx < len(_PreviewScaleView._SCALE_OPTIONS) - 1:
            self._zoom_idx += 1
            self._apply_zoom()

    def _apply_zoom(self) -> None:
        _, factor = _PreviewScaleView._SCALE_OPTIONS[self._zoom_idx]
        self._view.set_scale(factor)
        self._update_zoom_ui()
        cfg = _load_cfg()
        cfg["preview_zoom_idx"] = self._zoom_idx
        _save_cfg(cfg)
        self.zoom_changed.emit(factor)

    def _update_zoom_ui(self) -> None:
        opts = _PreviewScaleView._SCALE_OPTIONS
        label, _ = opts[self._zoom_idx]
        self._zoom_label.setText(label)
        self._zoom_in_btn.setEnabled(self._zoom_idx > 0)
        self._zoom_out_btn.setEnabled(self._zoom_idx < len(opts) - 1)

    # ------------------------------------------------------------------
    # Event filter lifecycle (install on show, remove on hide/close)
    # ------------------------------------------------------------------
    def showEvent(self, event) -> None:
        super().showEvent(event)
        QApplication.instance().installEventFilter(self)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        if self._autoscroll_active:
            self._stop_autoscroll()
        QApplication.instance().removeEventFilter(self)

    def closeEvent(self, event) -> None:
        if self._autoscroll_active:
            self._stop_autoscroll()
        QApplication.instance().removeEventFilter(self)
        self.closed.emit()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Middle-click auto-scroll
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.MiddleButton and self._is_under_view(obj):
                self._start_autoscroll()
                return True
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.MiddleButton and self._autoscroll_active:
                self._stop_autoscroll()
                return True
        return False

    def _is_under_view(self, obj) -> bool:
        if not isinstance(obj, QWidget):
            return False
        if obj.window() is not self.window():
            return False
        pos = self._view.mapFromGlobal(QCursor.pos())
        return self._view.rect().contains(pos)

    def _start_autoscroll(self) -> None:
        self._autoscroll_active = True
        self._autoscroll_anchor = QCursor.pos()
        self._scroll_accum = 0.0
        self._last_tick = time.monotonic()
        QApplication.setOverrideCursor(self._as_cursor)
        self._autoscroll_timer.start()

    def _stop_autoscroll(self) -> None:
        self._autoscroll_active = False
        self._autoscroll_timer.stop()
        QApplication.restoreOverrideCursor()

    def _do_autoscroll(self) -> None:
        now = time.monotonic()
        dt = min(now - self._last_tick, 0.05)
        self._last_tick = now
        dy = QCursor.pos().y() - self._autoscroll_anchor.y()
        dead = 12
        if abs(dy) <= dead:
            self._scroll_accum = 0.0
            return
        dist = abs(dy) - dead
        speed = min((dist ** 1.5) * 4.5, 4500.0)
        self._scroll_accum += speed * dt * (1 if dy > 0 else -1)
        step = int(self._scroll_accum)
        if step:
            self._scroll_accum -= step
            bar = self._view.verticalScrollBar()
            bar.setValue(bar.value() + step)


# ---------------------------------------------------------------------------
# Floating preview window (thin wrapper around PreviewPane)
# ---------------------------------------------------------------------------
class PreviewWindow(QWidget):
    closed        = pyqtSignal()
    theme_changed = pyqtSignal()
    dock_toggled  = pyqtSignal()
    zoom_changed  = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self._pane = PreviewPane()
        self._pane.theme_changed.connect(self._on_pane_theme_changed)
        self._pane.dock_toggled.connect(self.dock_toggled)
        self._pane.zoom_changed.connect(self.zoom_changed)

        self.setWindowTitle("プレビュー")
        self.resize(_PREVIEW_MIN_W, 900)
        self.setMinimumWidth(_PREVIEW_MIN_W)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._pane)

    @property
    def theme_id(self) -> str:
        return self._pane.theme_id

    @property
    def current_zoom_factor(self) -> float:
        return self._pane.current_zoom_factor

    def set_content(self, body: str, title: str = "") -> None:
        self._pane.set_content(body, title)

    def update_dirty_lines(self, dirty: dict[int, str], title: str) -> bool:
        return self._pane.update_dirty_lines(dirty, title)

    def _on_pane_theme_changed(self) -> None:
        self.theme_changed.emit()

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Custom tab bar — all drag handling delegated to NaroEditor.eventFilter
# ---------------------------------------------------------------------------
class _TabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom_drag: bool = False

    def mousePressEvent(self, event) -> None:
        self._custom_drag = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        # Left-button moves handled entirely by NaroEditor.eventFilter
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._custom_drag:
            self._custom_drag = False
            return  # Suppress spurious tab-selection after custom drag
        self._custom_drag = False
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# Floating drag preview — semi-transparent tab that follows the cursor
# ---------------------------------------------------------------------------
class _TabDragFloat(QWidget):
    # Colors matching QTabBar::tab:selected stylesheet values
    _BG     = QColor(40,  44,  52,  200)   # C['bg']    #282c34, ~80% opacity
    _ACCENT = QColor(97,  175, 239, 220)   # C['accent'] #61afef
    _BORDER = QColor(24,  26,  31,  200)   # C['border'] #181a1f
    _FG     = QColor(171, 178, 191, 220)   # C['fg']     #abb2bf

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._text = ""
        # Tab height: 2px top-border + 7px padding + ~14px text + 7px padding = 30px
        self.setFixedHeight(30)
        self.setFixedWidth(120)

    def set_text(self, text: str) -> None:
        self._text = text
        f = self.font()
        f.setPointSize(9)
        w = QFontMetrics(f).horizontalAdvance(text) + 28
        self.setFixedWidth(min(max(w, 80), 220))
        self.update()

    def follow(self, gpos: QPoint) -> None:
        self.move(gpos.x() - self.width() // 2, gpos.y() - self.height() // 2)

    def paintEvent(self, event) -> None:
        if not self._text:
            return
        p = QPainter(self)
        r = self.rect()

        # Tab body (selected tab background)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._BG)
        p.drawRect(r)

        # 2px accent top border
        p.setBrush(self._ACCENT)
        p.drawRect(QRect(r.left(), r.top(), r.width(), 2))

        # 1px right border
        p.setBrush(self._BORDER)
        p.drawRect(QRect(r.right(), r.top(), 1, r.height()))

        # Tab label text (font-size 12px = ~9pt, color C['fg'])
        p.setPen(self._FG)
        f = p.font()
        f.setPointSize(9)
        p.setFont(f)
        p.drawText(r.adjusted(0, 2, 0, 0), Qt.AlignmentFlag.AlignCenter, self._text)
        p.end()


# ---------------------------------------------------------------------------
# Split-zone overlay — covers the editor container during tab drag
# ---------------------------------------------------------------------------
class _SplitOverlay(QWidget):
    """Transparent overlay that highlights split/merge drop zones during tab drag."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._zone = ""
        self._rect: QRect | None = None
        self.hide()

    def set_zone(self, zone: str, rect: QRect | None = None) -> None:
        if zone == self._zone and rect == self._rect:
            return
        self._zone = zone
        self._rect = rect
        if zone:
            if self.parent():
                self.setGeometry(self.parent().rect())
            self.show()
            self.raise_()
        else:
            self.hide()
        self.update()

    def paintEvent(self, event) -> None:
        if not self._zone:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()

        if self._zone == "MERGE" and self._rect is not None:
            highlight  = QColor(80, 200, 120, 70)
            border_col = QColor(80, 200, 120, 200)
            zone_rect  = self._rect
            label      = "ペインを結合"
        elif self._zone == "V":
            highlight  = QColor(80, 140, 255, 70)
            border_col = QColor(80, 140, 255, 200)
            zone_rect  = QRect(r.width() // 2, 0, r.width() - r.width() // 2, r.height())
            label      = "左右に分割"
        else:
            highlight  = QColor(80, 140, 255, 70)
            border_col = QColor(80, 140, 255, 200)
            zone_rect  = QRect(0, r.height() // 2, r.width(), r.height() - r.height() // 2)
            label      = "上下に分割"

        p.fillRect(zone_rect, highlight)
        p.setPen(QPen(border_col, 2))
        p.drawRect(zone_rect.adjusted(1, 1, -1, -1))

        p.setPen(QColor(255, 255, 255))
        f = p.font()
        f.setPointSize(13)
        f.setBold(True)
        p.setFont(f)
        p.drawText(zone_rect, Qt.AlignmentFlag.AlignCenter, label)
        p.end()


# ---------------------------------------------------------------------------
# Auto-update: version check thread
# ---------------------------------------------------------------------------
class _UpdateChecker(QThread):
    """GitHub releases API を非同期で問い合わせ、新バージョンがあれば通知する。"""
    update_available = pyqtSignal(str, str)  # (latest_version, download_url)
    no_update        = pyqtSignal()           # 最新バージョン使用中
    check_error      = pyqtSignal()           # ネットワーク／解析エラー

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self._current = current_version

    def run(self) -> None:
        try:
            import urllib.request as _ur
            req = _ur.Request(
                _GITHUB_API_LATEST,
                headers={"User-Agent": f"NaroEditor/{self._current}"},
            )
            with _ur.urlopen(req, timeout=10) as resp:
                import json as _json
                data = _json.loads(resp.read().decode())
            tag = data.get("tag_name", "").lstrip("vV")
            if not tag:
                self.no_update.emit()
                return
            if (tuple(map(int, tag.split(".")))
                    <= tuple(map(int, self._current.split(".")))):
                self.no_update.emit()
                return
            for asset in data.get("assets", []):
                if asset.get("name", "").lower().endswith(".exe"):
                    self.update_available.emit(tag, asset["browser_download_url"])
                    return
            self.no_update.emit()  # リリースはあるが EXE アセットなし
        except Exception:
            self.check_error.emit()


# ---------------------------------------------------------------------------
# Auto-update: download thread
# ---------------------------------------------------------------------------
class _DownloadThread(QThread):
    """新バージョン EXE を一時ファイルにダウンロードする。"""
    progress = pyqtSignal(int)   # 0-100
    finished = pyqtSignal(str)   # 一時ファイルパス
    error    = pyqtSignal(str)   # エラーメッセージ

    def __init__(self, url: str, dest: str, parent=None):
        super().__init__(parent)
        self._url  = url
        self._dest = dest

    def run(self) -> None:
        try:
            import urllib.request as _ur
            req = _ur.Request(self._url, headers={"User-Agent": f"NaroEditor/{APP_VERSION}"})
            with _ur.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                done  = 0
                with open(self._dest, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if total > 0:
                            self.progress.emit(int(done * 100 / total))
            # MZ ヘッダー検証
            with open(self._dest, "rb") as f:
                if f.read(2) != b"MZ":
                    raise ValueError("ダウンロードしたファイルが無効です。")
            self.finished.emit(self._dest)
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class NaroEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NaroEditor")
        self.resize(1200, 760)
        self.setMinimumSize(640, 480)
        _ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NaroEditor.ico")
        if os.path.exists(_ico):
            self.setWindowIcon(QIcon(_ico))
        cfg = _load_cfg()
        geom = cfg.get("window_geometry")
        if geom:
            self.restoreGeometry(QByteArray(bytes.fromhex(geom)))
        self._preview: PreviewWindow | None = None
        self._preview_mode: str = cfg.get("preview_mode", "float")
        self._drag_editor: CodeEditor | None = None
        self._drag_pane: QTabWidget | None = None
        self._drag_mode: str = ""          # "" | "slide" | "float"
        self._drag_tab_idx: int = -1       # current visual index during slide
        self._drag_start_gpos: QPoint = QPoint()
        self._float: _TabDragFloat | None = None
        self._panes: list[QTabWidget] = []
        self._active_pane: QTabWidget | None = None
        self._lock_mgr = FileLockManager()
        self._build_ui()
        self._build_menu()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)
        self._autosave_timer.timeout.connect(self._do_autosave)
        self._autosave_timer.start()
        self._preview_update_timer = QTimer(self)
        self._preview_update_timer.setSingleShot(True)
        self._preview_update_timer.timeout.connect(self._do_preview_update)
        self._preview_editor_block_count: int = 0
        # クラッシュ判定はロックファイル作成より前に行う
        self._prev_crashed = os.path.isfile(_LOCK_PATH)
        try:
            with open(_LOCK_PATH, "w", encoding="utf-8") as _f:
                _f.write("locked")
        except OSError:
            pass
        QTimer.singleShot(0, self._restore_session)
        QTimer.singleShot(0, _ensure_updater)
        QTimer.singleShot(3000, self._check_for_update)
        QApplication.instance().focusChanged.connect(self._on_focus_changed)

    # ------------------------------------------------------------------
    # Convenience accessor for the active editor
    # ------------------------------------------------------------------
    @property
    def _editor(self) -> CodeEditor | None:
        if self._active_pane is None:
            return None
        w = self._active_pane.currentWidget()
        return w if isinstance(w, CodeEditor) else None

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self._main_splitter)

        self._file_tree = FileTreePanel()
        self._file_tree._lock_mgr = self._lock_mgr
        self._file_tree.file_opened.connect(self._open_path)
        self._file_tree.file_renamed.connect(self._on_file_renamed)
        self._file_tree.setMinimumWidth(120)
        self._main_splitter.addWidget(self._file_tree)

        self._editor_container = QWidget()
        self._editor_container.setStyleSheet(f"background:{C['bg']};")
        ec_layout = QVBoxLayout(self._editor_container)
        ec_layout.setContentsMargins(0, 0, 0, 0)
        ec_layout.setSpacing(0)

        self._pane_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._pane_splitter.setChildrenCollapsible(False)
        ec_layout.addWidget(self._pane_splitter)

        self._tabs = self._make_pane()
        self._panes = [self._tabs]
        self._active_pane = self._tabs
        self._pane_splitter.addWidget(self._tabs)

        self._overlay = _SplitOverlay(self._editor_container)

        self._main_splitter.addWidget(self._editor_container)

        # Dock-mode preview pane (hidden until activated)
        self._dock_pane = PreviewPane()
        self._dock_pane.set_dock_mode(True)
        self._dock_pane.theme_changed.connect(self._force_preview_update)
        self._dock_pane.dock_toggled.connect(self._toggle_preview_mode)
        self._dock_pane.zoom_changed.connect(self._on_dock_zoom_changed)
        self._dock_pane.hide()
        self._main_splitter.addWidget(self._dock_pane)

        self._main_splitter.setSizes([220, 980, 0])
        self._main_splitter.setStretchFactor(0, 0)  # file tree: fixed
        self._main_splitter.setStretchFactor(1, 1)  # editor: absorbs resize
        self._main_splitter.setStretchFactor(2, 0)  # dock pane: fixed

        # Status bar
        self._char_lbl = QLabel("文字数: 0")
        self._enc_lbl = QLabel("UTF-8")
        sb = self.statusBar()
        sb.addWidget(self._char_lbl)
        sb.addWidget(self._vsep())
        sb.addWidget(self._enc_lbl)

    @staticmethod
    def _vsep() -> QLabel:
        sep = QLabel("|")
        sep.setStyleSheet(f"color:{C['fg_subtle']}; padding:0 4px;")
        return sep

    def _build_menu(self) -> None:
        mb = self.menuBar()

        fm = mb.addMenu("ファイル")
        fm.addAction("新規タブ",         QKeySequence.StandardKey.New,        self._new_tab)
        fm.addAction("開く",             QKeySequence.StandardKey.Open,       self._open_file)
        fm.addAction("保存",             QKeySequence.StandardKey.Save,       self._save_file)
        fm.addAction("名前を付けて保存", QKeySequence("Ctrl+Shift+S"),        self._save_as)
        fm.addAction("タブを閉じる",     QKeySequence("Ctrl+W"),              self._close_current_tab)
        fm.addSeparator()
        fm.addAction("終了", self.close)

        em = mb.addMenu("編集")
        self._act_undo   = em.addAction("元に戻す", QKeySequence.StandardKey.Undo,  self._undo)
        self._act_redo   = em.addAction("やり直し", QKeySequence.StandardKey.Redo,  self._redo)
        em.addSeparator()
        self._act_cut    = em.addAction("切り取り", QKeySequence.StandardKey.Cut,   self._cut)
        self._act_copy   = em.addAction("コピー",   QKeySequence.StandardKey.Copy,  self._copy)
        self._act_paste  = em.addAction("貼り付け", QKeySequence.StandardKey.Paste, self._paste)
        self._act_qpaste = em.addAction("引用符付き貼り付け", QKeySequence("Ctrl+Q"), self._quote_paste)
        self._act_delete = em.addAction("削除",                                      self._delete_selection)
        em.addAction("行削除", QKeySequence("Ctrl+Return"), self._delete_line)

        conv = em.addMenu("変換")
        self._act_lower   = conv.addAction("小文字に変換",   QKeySequence("Ctrl+L"),        self._to_lowercase)
        self._act_upper   = conv.addAction("大文字に変換",   QKeySequence("Shift+Ctrl+L"),  self._to_uppercase)
        conv.addSeparator()
        self._act_hankaku = conv.addAction("半角に変換",     QKeySequence("Ctrl+G"),        self._to_hankaku)
        self._act_zenkaku = conv.addAction("全角に変換",     QKeySequence("Shift+Ctrl+G"),  self._to_zenkaku)
        conv.addSeparator()
        conv.addAction("TABインデント",   lambda: self._indent())
        conv.addAction("TAB逆インデント", lambda: self._unindent())
        conv.addSeparator()
        conv.addAction("空白 インデント",   QKeySequence("Shift+Ctrl+I"), self._space_indent)
        conv.addAction("空白 逆インデント", QKeySequence("Shift+Ctrl+U"), self._space_unindent)
        conv.addSeparator()
        self._act_del_nl = conv.addAction("改行削除", QKeySequence("Shift+Ctrl+T"), self._delete_newlines)
        conv.aboutToShow.connect(self._update_conv_menu)

        em.addSeparator()
        em.addAction("すべて選択", QKeySequence.StandardKey.SelectAll, self._select_all)
        self._act_ro = em.addAction("書き換え禁止", QKeySequence("Shift+Ctrl+N"), self._toggle_readonly)
        self._act_ro.setCheckable(True)
        em.aboutToShow.connect(self._update_edit_menu)

        sm = mb.addMenu("検索")
        sm.addAction("検索", QKeySequence.StandardKey.Find, self._show_search)
        sm.addAction("置換", QKeySequence("Ctrl+R"),        self._show_replace)

        km = mb.addMenu("校正")
        km.addAction("段落下げ", self._para_indent)
        km.addSeparator()
        self._act_ruby_narou  = km.addAction("ルビ(なろう/カクヨム)",  QKeySequence("Alt+R"), self._ruby_narou)
        self._act_ruby_pixiv  = km.addAction("ルビ(Pixiv)",            QKeySequence("Alt+E"), self._ruby_pixiv)
        km.addSeparator()
        self._act_bouten_narou = km.addAction("傍点(なろう/カクヨム)", QKeySequence("Alt+/"), self._bouten_narou)
        self._act_bouten_pixiv = km.addAction("傍点(Pixiv)",           QKeySequence("Alt+."), self._bouten_pixiv)
        km.aboutToShow.connect(self._update_kosei_menu)

        vm = mb.addMenu("表示")
        vm.addAction("プレビュー", QKeySequence("Ctrl+Shift+P"), self._toggle_preview)
        vm.addSeparator()
        self._dock_action = vm.addAction("プレビューをドッキング", self._toggle_preview_mode)
        self._dock_action.setCheckable(True)
        self._dock_action.setChecked(self._preview_mode == "dock")
        vm.addSeparator()
        self._act_split_v = vm.addAction("左右に分割",  lambda: self._split_view("V"))
        self._act_split_v.setEnabled(False)
        self._act_split_h = vm.addAction("上下に分割",  lambda: self._split_view("H"))
        self._act_split_h.setEnabled(False)
        vm.addSeparator()
        self._act_merge   = vm.addAction("ペインを結合", self._merge_all_panes)
        self._act_merge.setEnabled(False)
        vm.aboutToShow.connect(self._update_view_menu)

        hm = mb.addMenu("ヘルプ")
        hm.addAction("使い方", QKeySequence("F1"), self._show_help)
        hm.addSeparator()
        self._act_check_update = hm.addAction("アップデートを確認", self._check_for_update_manual)
        hm.addSeparator()
        hm.addAction("バージョン情報", self._show_about)

    # ------------------------------------------------------------------
    # Pane factory and split helpers
    # ------------------------------------------------------------------
    def _make_pane(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setTabBar(_TabBar())
        tabs.setTabsClosable(False)
        tabs.setMovable(False)  # custom drag handles reordering
        tabs.currentChanged.connect(
            lambda idx, p=tabs: self._on_pane_tab_changed(p, idx)
        )
        tabs.tabBar().installEventFilter(self)
        return tabs

    def _pane_for_tabbar(self, obj) -> "QTabWidget | None":
        if not isinstance(obj, QTabBar):
            return None
        for pane in self._panes:
            if obj is pane.tabBar():
                return pane
        return None

    def _get_split_zone(self) -> str:
        gpos = QCursor.pos()
        if len(self._panes) >= 2 and self._drag_pane is not None:
            for pane in self._panes:
                if pane is self._drag_pane:
                    continue
                if pane.rect().contains(pane.mapFromGlobal(gpos)):
                    return "MERGE"
            return ""
        local = self._editor_container.mapFromGlobal(gpos)
        r = self._editor_container.rect()
        if not r.contains(local):
            return ""
        in_right  = local.x() / r.width()  > 0.60
        in_bottom = local.y() / r.height() > 0.60
        if in_right and in_bottom:
            rx = local.x() / r.width()  - 0.60
            ry = local.y() / r.height() - 0.60
            return "V" if rx > ry else "H"
        if in_right:
            return "V"
        if in_bottom:
            return "H"
        return ""

    def _do_split(self, pane: QTabWidget, editor: "CodeEditor", zone: str) -> None:
        if zone != "MERGE" and pane.count() <= 1:
            return
        tab_idx = next(
            (i for i in range(pane.count()) if pane.widget(i) is editor), -1
        )
        if tab_idx < 0:
            return
        title = pane.tabText(tab_idx)

        if len(self._panes) >= 2:
            other = self._panes[1] if pane is self._panes[0] else self._panes[0]
            pane.removeTab(tab_idx)
            new_idx = other.addTab(editor, title)
            other.tabBar().setTabButton(
                new_idx, QTabBar.ButtonPosition.RightSide, self._make_close_btn(editor)
            )
            other.setCurrentIndex(new_idx)
            self._active_pane = other
            if pane.count() == 0:
                self._remove_pane(pane)
            self._update_window_title()
            self._update_status()
            return

        ori = Qt.Orientation.Horizontal if zone == "V" else Qt.Orientation.Vertical
        self._pane_splitter.setOrientation(ori)

        pane.removeTab(tab_idx)

        new_pane = self._make_pane()
        self._panes.append(new_pane)
        self._pane_splitter.addWidget(new_pane)
        new_idx = new_pane.addTab(editor, title)
        new_pane.tabBar().setTabButton(
            new_idx, QTabBar.ButtonPosition.RightSide, self._make_close_btn(editor)
        )
        new_pane.setCurrentIndex(new_idx)

        total = (self._pane_splitter.width() if ori == Qt.Orientation.Horizontal
                 else self._pane_splitter.height())
        half = max(total // 2, 100)
        self._pane_splitter.setSizes([half, total - half])

        self._active_pane = new_pane
        self._update_window_title()
        self._update_status()
        self._force_preview_update()

    def _remove_pane(self, pane: QTabWidget) -> None:
        if pane in self._panes:
            self._panes.remove(pane)
        if self._active_pane is pane:
            self._active_pane = self._panes[0] if self._panes else None
        pane.setParent(None)
        pane.deleteLater()

    def _split_view(self, zone: str) -> None:
        pane = self._active_pane
        if pane is None:
            return
        editor = pane.currentWidget()
        if not isinstance(editor, CodeEditor):
            return
        self._do_split(pane, editor, zone)

    def _merge_all_panes(self) -> None:
        if len(self._panes) < 2:
            return
        dst = self._panes[0]
        src = self._panes[1]
        while src.count() > 0:
            editor = src.widget(0)
            title  = src.tabText(0)
            src.removeTab(0)
            new_idx = dst.addTab(editor, title)
            dst.tabBar().setTabButton(
                new_idx, QTabBar.ButtonPosition.RightSide,
                self._make_close_btn(editor),
            )
        dst.setCurrentIndex(dst.count() - 1)
        self._active_pane = dst
        self._remove_pane(src)
        self._update_window_title()
        self._update_status()
        self._force_preview_update()

    def _update_view_menu(self) -> None:
        can_split = (len(self._panes) < 2
                     and self._active_pane is not None
                     and self._active_pane.count() > 1)
        can_merge = len(self._panes) >= 2
        self._act_split_v.setEnabled(can_split)
        self._act_split_h.setEnabled(can_split)
        self._act_merge.setEnabled(can_merge)

    # ------------------------------------------------------------------
    # Tab lifecycle
    # ------------------------------------------------------------------
    def eventFilter(self, obj, event) -> bool:
        pane = self._pane_for_tabbar(obj)
        if pane is not None:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.MiddleButton:
                    idx = obj.tabAt(event.pos())
                    if idx >= 0:
                        self._close_tab(idx, pane)
                        return True
                elif event.button() == Qt.MouseButton.LeftButton:
                    self._active_pane = pane
                    idx = obj.tabAt(event.pos())
                    self._drag_mode   = ""
                    self._drag_tab_idx = idx
                    self._drag_editor = None
                    self._drag_pane   = None
                    self._drag_start_gpos = QCursor.pos()
                    if idx >= 0 and isinstance(pane.widget(idx), CodeEditor):
                        self._drag_editor = pane.widget(idx)
                        self._drag_pane   = pane

            elif event.type() == QEvent.Type.MouseMove:
                if (event.buttons() & Qt.MouseButton.LeftButton
                        and self._drag_editor is not None
                        and self._drag_pane is not None):
                    gpos = QCursor.pos()
                    bar  = self._drag_pane.tabBar()

                    # ── Threshold not yet exceeded ─────────────────────────
                    if self._drag_mode == "":
                        dist = (gpos - self._drag_start_gpos).manhattanLength()
                        if dist > QApplication.startDragDistance():
                            obj._custom_drag = True
                            if bar.rect().contains(bar.mapFromGlobal(gpos)):
                                self._drag_mode = "slide"
                            else:
                                self._drag_mode = "float"
                                self._start_float_drag()

                    # ── Slide mode: tab moves along the tab bar ────────────
                    if self._drag_mode == "slide":
                        local = bar.mapFromGlobal(gpos)
                        if bar.rect().contains(local):
                            target = bar.tabAt(local)
                            if target >= 0 and target != self._drag_tab_idx:
                                bar.moveTab(self._drag_tab_idx, target)
                                self._drag_tab_idx = target
                        else:
                            # Cursor left the tab bar → switch to float
                            self._drag_mode = "float"
                            self._start_float_drag()

                    # ── Float mode: floating widget + split/merge overlay ──
                    if self._drag_mode == "float":
                        self._float.follow(gpos)
                        if not self._float.isVisible():
                            self._float.show()
                        can_split = self._drag_pane.count() > 1
                        can_merge = len(self._panes) >= 2
                        if can_split or can_merge:
                            zone = self._get_split_zone()
                            if zone == "MERGE":
                                other = next(
                                    p for p in self._panes if p is not self._drag_pane
                                )
                                pos = self._editor_container.mapFromGlobal(
                                    other.mapToGlobal(QPoint(0, 0))
                                )
                                self._overlay.set_zone("MERGE", QRect(pos, other.size()))
                            else:
                                self._overlay.set_zone(zone)
                        else:
                            self._overlay.set_zone("")
                else:
                    if self._float:
                        self._float.hide()
                    self._overlay.set_zone("")

            elif event.type() == QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self._float:
                        self._float.hide()
                    zone = self._overlay._zone
                    self._overlay.set_zone("")
                    if self._drag_mode == "float" and self._drag_editor is not None:
                        de, dp, dz, gp = (
                            self._drag_editor, self._drag_pane,
                            zone, QCursor.pos(),
                        )
                        def _drop(de=de, dp=dp, dz=dz, gp=gp):
                            if dz in ("V", "H", "MERGE"):
                                self._do_split(dp, de, dz)
                            else:
                                self._handle_tab_drop(gp, dp, de)
                        QTimer.singleShot(0, _drop)
                    # slide mode: tab already in final position via moveTab
                    self._drag_mode   = ""
                    self._drag_tab_idx = -1
                    self._drag_editor = None
                    self._drag_pane   = None

        return super().eventFilter(obj, event)

    def _start_float_drag(self) -> None:
        if self._float is None:
            self._float = _TabDragFloat()
        idx = self._drag_tab_idx
        title = self._drag_pane.tabText(idx) if idx >= 0 else ""
        self._float.set_text(title)

    def _handle_tab_drop(self, gpos: QPoint, from_pane: QTabWidget,
                         editor: "CodeEditor") -> None:
        from_idx = next(
            (i for i in range(from_pane.count()) if from_pane.widget(i) is editor), -1
        )
        if from_idx < 0:
            return
        for pane in self._panes:
            bar = pane.tabBar()
            local = bar.mapFromGlobal(gpos)
            if not bar.rect().contains(local):
                continue
            to_idx = bar.tabAt(local)
            if to_idx < 0:
                to_idx = max(pane.count() - 1, 0)
            if pane is from_pane:
                if to_idx != from_idx:
                    bar.moveTab(from_idx, to_idx)
            else:
                title = from_pane.tabText(from_idx)
                from_pane.removeTab(from_idx)
                new_idx = pane.insertTab(min(to_idx, pane.count()), editor, title)
                pane.tabBar().setTabButton(
                    new_idx, QTabBar.ButtonPosition.RightSide,
                    self._make_close_btn(editor),
                )
                pane.setCurrentIndex(new_idx)
                self._active_pane = pane
                if from_pane.count() == 0:
                    if from_pane is not self._panes[0]:
                        self._remove_pane(from_pane)
                    else:
                        # pane[0] は常に生かす — from_pane に新規タブを追加する
                        prev_active = self._active_pane
                        self._active_pane = from_pane
                        self._new_tab()
                        self._active_pane = prev_active
                self._update_window_title()
                self._update_status()
            return

    def _make_close_btn(self, editor: "CodeEditor") -> QPushButton:
        btn = QPushButton("✕")
        btn.setFixedSize(16, 16)
        btn.setStyleSheet(f"""
            QPushButton {{
                color: {C['fg_dim']};
                background: transparent;
                border: none;
                font-size: 11px;
                padding: 0;
                margin: 0;
            }}
            QPushButton:hover {{ color: {C['red']}; }}
        """)
        btn.clicked.connect(lambda: self._close_tab_by_editor(editor))
        return btn

    def _close_tab_by_editor(self, editor: "CodeEditor") -> None:
        for pane in self._panes:
            for i in range(pane.count()):
                if pane.widget(i) is editor:
                    self._active_pane = pane
                    self._close_tab(i, pane)
                    return

    def _make_editor(self) -> CodeEditor:
        ed = CodeEditor()
        ed.document().modificationChanged.connect(
            lambda mod, e=ed: self._on_mod_changed(e, mod)
        )
        ed.document().contentsChanged.connect(self._update_status)
        ed.document().contentsChange.connect(
            lambda pos, rm, add, _ed=ed: self._on_editor_change(_ed, pos, rm, add)
        )
        return ed

    def _tab_title(self, editor: CodeEditor) -> str:
        name = os.path.basename(editor.file_path) if editor.file_path else "新規ファイル"
        return f"● {name}" if editor.document().isModified() else name

    def _new_tab(self) -> None:
        ed = self._make_editor()
        idx = self._active_pane.addTab(ed, "新規ファイル")
        self._active_pane.tabBar().setTabButton(idx, QTabBar.ButtonPosition.RightSide, self._make_close_btn(ed))
        self._active_pane.setCurrentIndex(idx)
        ed.setFocus()

    def _close_tab(self, index: int, pane: QTabWidget | None = None) -> None:
        if pane is None:
            pane = self._active_pane
        ed = pane.widget(index)
        if isinstance(ed, CodeEditor) and ed.document().isModified():
            self._active_pane = pane
            pane.setCurrentIndex(index)
            name = os.path.basename(ed.file_path) if ed.file_path else "新規ファイル"
            ans = QMessageBox.question(
                self, "未保存の変更",
                f"「{name}」の変更を保存しますか？",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if ans == QMessageBox.StandardButton.Cancel:
                return
            if ans == QMessageBox.StandardButton.Save:
                self._save_file()
                # Save As がキャンセルされた場合はタブを閉じない
                if isinstance(ed, CodeEditor) and ed.document().isModified():
                    return

        if isinstance(ed, CodeEditor):
            self._lock_mgr.unlock(ed.file_path)
        pane.removeTab(index)
        if pane.count() == 0:
            if pane is self._panes[0] or len(self._panes) == 1:
                self._active_pane = pane
                self._new_tab()
            else:
                self._remove_pane(pane)

    def _close_current_tab(self) -> None:
        idx = self._active_pane.currentIndex()
        if idx >= 0:
            self._close_tab(idx, self._active_pane)

    def _on_tab_changed(self, _index: int) -> None:
        self._update_window_title()
        self._update_status()
        self._force_preview_update()

    def _on_pane_tab_changed(self, pane: QTabWidget, index: int) -> None:
        self._active_pane = pane
        self._on_tab_changed(index)

    def _on_focus_changed(self, _old, new: QWidget) -> None:
        if new is None:
            return
        w = new
        while w is not None:
            if isinstance(w, CodeEditor):
                break
            w = w.parentWidget()
        if w is None:
            return
        for pane in self._panes:
            for i in range(pane.count()):
                if pane.widget(i) is w:
                    if self._active_pane is not pane:
                        self._active_pane = pane
                        self._force_preview_update()
                    return

    def _on_mod_changed(self, editor: CodeEditor, _modified: bool) -> None:
        for pane in self._panes:
            for i in range(pane.count()):
                if pane.widget(i) is editor:
                    pane.setTabText(i, self._tab_title(editor))
                    break
        if self._editor is editor:
            self._update_window_title()

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "ファイルを開く", "",
            "テキストファイル (*.txt *.py *.md *.csv *.json *.xml *.html "
            "*.css *.js *.ts *.ini *.cfg *.log *.bat *.sh *.yaml *.toml);;"
            "すべてのファイル (*.*)",
        )
        if path:
            self._open_path(path)

    def _on_file_renamed(self, old_path: str, new_path: str) -> None:
        """ツリーでのリネーム後、ロックを新パスへ移転しタブを更新する。"""
        self._lock_mgr.on_rename(old_path, new_path)
        for pane in self._panes:
            for i in range(pane.count()):
                ed = pane.widget(i)
                if isinstance(ed, CodeEditor) and ed.file_path == old_path:
                    ed.file_path = new_path
                    pane.setTabText(i, self._tab_title(ed))
        self._update_window_title()

    def _open_path(self, path: str) -> None:
        # Switch to already-open tab in any pane
        for pane in self._panes:
            for i in range(pane.count()):
                ed = pane.widget(i)
                if isinstance(ed, CodeEditor) and ed.file_path == path:
                    self._active_pane = pane
                    pane.setCurrentIndex(i)
                    return

        # Reuse current tab if it is a pristine blank tab
        cur = self._editor
        reuse = (
            cur is not None
            and not cur.file_path
            and not cur.document().isModified()
            and not cur.toPlainText()
        )
        if reuse:
            ed = cur
            tab_idx = self._active_pane.currentIndex()
        else:
            ed = self._make_editor()
            tab_idx = self._active_pane.addTab(ed, "…")
            self._active_pane.tabBar().setTabButton(
                tab_idx, QTabBar.ButtonPosition.RightSide, self._make_close_btn(ed)
            )

        try:
            with open(path, "rb") as f:
                data = f.read()
            enc = detect_encoding(data)
            ed.setPlainText(data.decode(enc))
            ed.document().setModified(False)
            ed.file_path = path
            ed.file_encoding = enc
            name = os.path.basename(path)
            self._active_pane.setTabText(tab_idx, name)
            self._active_pane.setCurrentIndex(tab_idx)
            self._update_window_title()
            self._update_status()
            self._lock_mgr.lock(path)
        except Exception as e:
            if not reuse:
                self._active_pane.removeTab(tab_idx)
            QMessageBox.critical(self, "エラー", f"ファイルを開けませんでした:\n{e}")

    def _save_file(self) -> None:
        cur = self._editor
        if cur is None:
            return
        if cur.file_path:
            self._write(cur, cur.file_path)
        else:
            self._save_as()

    def _save_as(self) -> None:
        cur = self._editor
        if cur is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "",
            "テキストファイル (*.txt);;すべてのファイル (*.*)",
        )
        if not path:
            return
        old_path = cur.file_path
        cur.file_path = path
        cur.file_encoding = "utf-8"
        self._write(cur, path)
        if old_path:
            self._lock_mgr.unlock(old_path)
        self._lock_mgr.lock(path)
        idx = self._active_pane.currentIndex()
        self._active_pane.setTabText(idx, self._tab_title(cur))
        self._update_window_title()

    def _write(self, editor: CodeEditor, path: str) -> None:
        try:
            with open(path, "w", encoding=editor.file_encoding, errors="replace") as f:
                f.write(editor.toPlainText())
            editor.document().setModified(False)
            # tab title is updated via modificationChanged → _on_mod_changed
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"保存できませんでした:\n{e}")

    def closeEvent(self, event) -> None:
        preview_open = (
            (self._preview_mode == "float" and self._preview is not None)
            or (self._preview_mode == "dock" and self._dock_pane.isVisible())
        )
        if self._preview is not None:
            self._preview.close()
        for pane in list(self._panes):
            for i in range(pane.count()):
                ed = pane.widget(i)
                if not isinstance(ed, CodeEditor) or not ed.document().isModified():
                    continue
                self._active_pane = pane
                pane.setCurrentIndex(i)
                name = os.path.basename(ed.file_path) if ed.file_path else "新規ファイル"
                ans = QMessageBox.question(
                    self, "未保存の変更",
                    f"「{name}」の変更を保存しますか？",
                    QMessageBox.StandardButton.Save
                    | QMessageBox.StandardButton.Discard
                    | QMessageBox.StandardButton.Cancel,
                )
                if ans == QMessageBox.StandardButton.Cancel:
                    event.ignore()
                    return
                if ans == QMessageBox.StandardButton.Save:
                    self._save_file()
                    if isinstance(ed, CodeEditor) and ed.document().isModified():
                        event.ignore()
                        return
        # Save session state
        session_files = []
        for pane in self._panes:
            for i in range(pane.count()):
                ed = pane.widget(i)
                if isinstance(ed, CodeEditor) and ed.file_path:
                    session_files.append(ed.file_path)
        cfg = _load_cfg()
        cfg["session_files"] = session_files
        cfg["session_active_tab"] = self._active_pane.currentIndex()
        cfg["session_preview_open"] = preview_open
        cfg["preview_mode"] = self._preview_mode
        cfg["splitter_sizes"] = self._main_splitter.sizes()
        cfg["window_geometry"] = bytes(self.saveGeometry()).hex()
        _save_cfg(cfg)
        self._lock_mgr.unlock_all()
        self._clear_recovery()
        event.accept()

    def _restore_session(self) -> None:
        if self._prev_crashed:
            self._offer_recovery()

        cfg = _load_cfg()
        paths = cfg.get("session_files", [])
        active = cfg.get("session_active_tab", 0)
        preview_open = cfg.get("session_preview_open", False)
        opened = 0
        for path in paths:
            if os.path.isfile(path):
                self._open_path(path)
                opened += 1
        total_tabs = sum(p.count() for p in self._panes)
        if total_tabs == 0:
            self._new_tab()
        elif opened > 0:
            target = min(active, self._active_pane.count() - 1)
            if target >= 0:
                self._active_pane.setCurrentIndex(target)
        if preview_open:
            if self._preview_mode == "float":
                self._toggle_preview()
            else:
                # Defer dock setup until after window.show() so the splitter
                # has been fully laid out and sizes() returns real pixel values.
                saved_sizes = cfg.get("splitter_sizes")
                def _open_dock(sizes=saved_sizes):
                    self._toggle_preview()
                    if sizes and len(sizes) == 3:
                        self._main_splitter.setSizes(sizes)
                QTimer.singleShot(0, _open_dock)

    # ------------------------------------------------------------------
    # Auto-update
    # ------------------------------------------------------------------
    def _check_for_update(self) -> None:
        if not getattr(sys, "frozen", False):
            return
        self._update_checker = _UpdateChecker(APP_VERSION, self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

    def _check_for_update_manual(self) -> None:
        self._act_check_update.setEnabled(False)
        self._act_check_update.setText("確認中…")
        checker = _UpdateChecker(APP_VERSION, self)
        self._manual_update_checker = checker

        def _restore_action():
            self._act_check_update.setEnabled(True)
            self._act_check_update.setText("アップデートを確認")

        def _on_no_update():
            _restore_action()
            QMessageBox.information(
                self, "アップデートの確認",
                f"NaroEditor は最新バージョン (v{APP_VERSION}) です。",
            )

        def _on_error():
            _restore_action()
            QMessageBox.warning(
                self, "アップデートの確認",
                "アップデートの確認に失敗しました。\nネットワーク接続を確認してください。",
            )

        def _on_available(version: str, url: str):
            _restore_action()
            self._on_update_available(version, url)

        checker.update_available.connect(_on_available)
        checker.no_update.connect(_on_no_update)
        checker.check_error.connect(_on_error)
        checker.start()

    def _on_update_available(self, version: str, url: str) -> None:
        ret = QMessageBox.question(
            self,
            "アップデートの確認",
            f"NaroEditor v{version} が公開されています。\n今すぐアップデートしますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        if not os.path.isfile(_UPDATER_PATH):
            QMessageBox.warning(
                self, "アップデート",
                "アップデータが見つかりません。\n"
                f"{_UPDATER_DIR} に NaroEditorUpdater.exe を配置してください。",
            )
            return

        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), f"NaroEditor_{version}_new.exe")

        dlg = QProgressDialog(
            f"NaroEditor v{version} をダウンロード中…",
            None,   # キャンセルボタンなし
            0, 100, self,
        )
        dlg.setWindowTitle("アップデート")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.setAutoClose(False)
        dlg.setValue(0)

        self._dl_thread = _DownloadThread(url, tmp, self)

        def _on_progress(v: int) -> None:
            dlg.setValue(v)

        def _on_finished(path: str) -> None:
            dlg.close()
            self._launch_updater(version, path)

        def _on_error(msg: str) -> None:
            dlg.close()
            QMessageBox.critical(self, "アップデート", f"ダウンロードに失敗しました。\n{msg}")

        self._dl_thread.progress.connect(_on_progress)
        self._dl_thread.finished.connect(_on_finished)
        self._dl_thread.error.connect(_on_error)
        self._dl_thread.start()
        dlg.exec()

    def _launch_updater(self, version: str, source: str) -> None:
        """ダウンロード済み EXE を渡して NaroEditorUpdater.exe を起動し、自身は終了する。"""
        import subprocess
        # _MEIPASS2 を 3 段階で確実に除去する:
        #   1. Win32 環境ブロック (SetEnvironmentVariableW) — PyInstaller が設定した本体
        #   2. CRT 環境 (os.environ.pop) — Python が管理するコピー
        #   3. Popen の env= 引数 — ブロック構築に使う辞書
        # これにより新 NaroEditor.exe が旧 _MEI* フォルダを参照する問題を確実に防ぐ。
        ctypes.windll.kernel32.SetEnvironmentVariableW("_MEIPASS2", None)
        os.environ.pop("_MEIPASS2", None)
        env = {k: v for k, v in os.environ.items() if k != "_MEIPASS2"}
        subprocess.Popen(
            [_UPDATER_PATH,
             "--pid",     str(os.getpid()),
             "--source",  source,
             "--target",  sys.executable,
             "--version", version],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            env=env,
        )
        QApplication.instance().quit()

    # ------------------------------------------------------------------
    # Crash recovery
    # ------------------------------------------------------------------
    def _do_autosave(self) -> None:
        """30秒ごとに全エディタ内容をリカバリーディレクトリへ書き出す。"""
        idx = 0
        for pane in self._panes:
            for i in range(pane.count()):
                ed = pane.widget(i)
                if not isinstance(ed, CodeEditor):
                    continue
                content = ed.toPlainText()
                if not content:
                    continue
                path = ed.file_path or ""
                save_path = os.path.join(_RECOVERY_DIR, f"{idx:03d}.autosave")
                try:
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(path + "\n")
                        f.write(content)
                except OSError:
                    pass
                idx += 1
        # 今回のタブ数より多い古いファイルを削除
        for entry in os.scandir(_RECOVERY_DIR):
            if not entry.name.endswith(".autosave"):
                continue
            try:
                n = int(entry.name.replace(".autosave", ""))
            except ValueError:
                continue
            if n >= idx:
                try:
                    os.remove(entry.path)
                except OSError:
                    pass

    def _offer_recovery(self) -> None:
        """前回クラッシュ時のリカバリーファイルを検出してユーザーに提示する。"""
        entries = sorted(
            [e for e in os.scandir(_RECOVERY_DIR) if e.name.endswith(".autosave")],
            key=lambda e: e.name,
        )
        if not entries:
            return

        items: list[tuple[str, str]] = []   # (original_path_or_empty, content)
        for entry in entries:
            try:
                with open(entry.path, "r", encoding="utf-8") as f:
                    first = f.readline().rstrip("\n")
                    content = f.read()
                items.append((first, content))
            except OSError:
                continue
        if not items:
            return

        names = "\n".join(
            f"  ・{os.path.basename(p) if p else '新規ファイル'}"
            for p, _ in items
        )
        ans = QMessageBox.question(
            self,
            "クラッシュからの復元",
            f"前回の終了時に保存されていないデータが見つかりました。\n\n"
            f"{names}\n\n復元しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans != QMessageBox.StandardButton.Yes:
            self._clear_autosaves()
            return

        for orig_path, content in items:
            ed = self._make_editor()
            if orig_path and os.path.isfile(orig_path):
                # 元ファイルが存在する場合は復元内容で上書き（未保存差分を復元）
                ed.file_path = orig_path
                ed.setPlainText(content)
                ed.document().setModified(True)
                title = os.path.basename(orig_path) + " [復元]"
                self._lock_mgr.lock(orig_path)
            else:
                ed.setPlainText(content)
                ed.document().setModified(True)
                title = (os.path.basename(orig_path) if orig_path else "新規ファイル") + " [復元]"
            idx = self._active_pane.addTab(ed, title)
            self._active_pane.tabBar().setTabButton(
                idx, QTabBar.ButtonPosition.RightSide, self._make_close_btn(ed)
            )

        self._clear_autosaves()

    def _clear_autosaves(self) -> None:
        """autosave ファイルのみ削除する（ロックは残す）。"""
        try:
            for entry in os.scandir(_RECOVERY_DIR):
                if entry.name.endswith(".autosave"):
                    os.remove(entry.path)
        except OSError:
            pass

    def _clear_recovery(self) -> None:
        """autosave ファイルとセッションロックを削除する（正常終了時に呼ぶ）。"""
        self._clear_autosaves()
        try:
            os.remove(_LOCK_PATH)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------
    def _toggle_preview(self) -> None:
        if self._preview_mode == "dock":
            if self._dock_pane.isVisible():
                self._dock_pane.hide()
                sizes = self._main_splitter.sizes()
                self._main_splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            else:
                self._dock_pane.sync_theme()
                self._dock_pane.show()
                sizes = self._main_splitter.sizes()
                content_w = _THEMES.get(self._dock_pane.theme_id, _THEMES["narou"])["content_w"]
                want = content_w + 80
                total = sizes[0] + sizes[1] + sizes[2]
                self._main_splitter.setSizes([sizes[0], total - sizes[0] - want, want])
                self._force_preview_update()
        else:
            if self._preview is None:
                self._preview = PreviewWindow()
                self._preview.closed.connect(self._on_preview_closed)
                self._preview.theme_changed.connect(self._force_preview_update)
                self._preview.dock_toggled.connect(self._toggle_preview_mode)
                self._preview.zoom_changed.connect(self._on_float_zoom_changed)
                self._preview.show()
                self._force_preview_update()
                # 保存済みズーム倍率をウィンドウ幅に反映する
                factor = self._preview.current_zoom_factor
                if factor != 1.0:
                    self._on_float_zoom_changed(factor)
            else:
                self._preview.close()

    def _on_preview_closed(self) -> None:
        self._preview = None

    def _on_dock_zoom_changed(self, factor: float) -> None:
        """ドックモードでズームが変わったらプレビューペインの幅を倍率に合わせる。"""
        if not self._dock_pane.isVisible():
            return
        sizes = self._main_splitter.sizes()
        new_w = max(200, round(_PREVIEW_MIN_W * factor))
        total = sum(sizes)
        self._main_splitter.setSizes([sizes[0], total - sizes[0] - new_w, new_w])

    def _on_float_zoom_changed(self, factor: float) -> None:
        """フロートモードでズームが変わったらウィンドウ幅を倍率に合わせる。"""
        if self._preview is None:
            return
        new_w = max(280, round(_PREVIEW_MIN_W * factor))
        self._preview.setMinimumWidth(new_w)
        self._preview.resize(new_w, self._preview.height())

    def _toggle_preview_mode(self) -> None:
        was_open = (
            (self._preview_mode == "float" and self._preview is not None)
            or (self._preview_mode == "dock" and self._dock_pane.isVisible())
        )
        # Close current preview
        if self._preview_mode == "dock":
            if self._dock_pane.isVisible():
                sizes = self._main_splitter.sizes()
                self._dock_pane.hide()
                self._main_splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            self._preview_mode = "float"
        else:
            if self._preview is not None:
                self._preview.close()
                self._preview = None
            self._preview_mode = "dock"
        self._dock_action.setChecked(self._preview_mode == "dock")
        cfg = _load_cfg()
        cfg["preview_mode"] = self._preview_mode
        _save_cfg(cfg)
        if was_open:
            self._toggle_preview()

    def _on_editor_change(self, ed: "CodeEditor",
                          pos: int, removed: int, added: int) -> None:
        """行数が変化した（改行・行削除）なら即時、文字入力のみなら 2 秒後にプレビューを更新する。"""
        if ed is not self._editor:
            return
        new_count = ed.document().blockCount()
        block_changed = (new_count != self._preview_editor_block_count)
        self._preview_editor_block_count = new_count
        # 改行・行削除は即時反映、文字入力のみは 300ms デバウンス
        self._preview_update_timer.start(0 if block_changed else 300)

    def _force_preview_update(self) -> None:
        """強制的に全再構築でプレビューを更新する（タブ切替・テーマ変更等）。"""
        self._do_preview_update()

    def _get_preview_title(self, cur: "CodeEditor") -> str:
        if cur.file_path:
            return os.path.splitext(os.path.basename(cur.file_path))[0]
        return "新規ファイル"

    def _do_preview_update(self) -> None:
        if self._preview_mode == "dock":
            target = self._dock_pane if self._dock_pane.isVisible() else None
        else:
            target = self._preview
        if target is None:
            return
        cur = self._editor
        if cur is None:
            return
        title = self._get_preview_title(cur)
        target.set_content(cur.toPlainText(), title)
        self._preview_editor_block_count = cur.document().blockCount()

    # ------------------------------------------------------------------
    # Search / Replace
    # ------------------------------------------------------------------
    def _show_search(self) -> None:
        if self._editor:
            SearchReplaceDialog(self, self._editor, "search").show()

    def _show_replace(self) -> None:
        if self._editor:
            SearchReplaceDialog(self, self._editor, "replace").show()

    # ------------------------------------------------------------------
    # Edit menu actions
    # ------------------------------------------------------------------
    def _undo(self) -> None:
        if e := self._editor: e.undo()

    def _redo(self) -> None:
        if e := self._editor: e.redo()

    def _cut(self) -> None:
        if e := self._editor: e.cut()

    def _copy(self) -> None:
        if e := self._editor: e.copy()

    def _paste(self) -> None:
        if e := self._editor: e.paste()

    def _select_all(self) -> None:
        if e := self._editor: e.selectAll()

    def _delete_line(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        cur.beginEditBlock()
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.movePosition(QTextCursor.MoveOperation.EndOfLine,
                         QTextCursor.MoveMode.KeepAnchor)
        if not cur.atEnd():
            cur.movePosition(QTextCursor.MoveOperation.NextCharacter,
                             QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.endEditBlock()
        e.setTextCursor(cur)

    def _indent(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if not cur.hasSelection():
            cur.insertText("\t")
            return
        doc = e.document()
        s = doc.findBlock(cur.selectionStart()).blockNumber()
        end_pos = cur.selectionEnd()
        eb = doc.findBlock(end_pos)
        n = eb.blockNumber()
        if eb.position() == end_pos and n > s:
            n -= 1
        cur.beginEditBlock()
        for i in range(s, n + 1):
            QTextCursor(doc.findBlockByNumber(i)).insertText("\t")
        cur.endEditBlock()

    def _unindent(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        doc = e.document()
        if cur.hasSelection():
            s = doc.findBlock(cur.selectionStart()).blockNumber()
            end_pos = cur.selectionEnd()
            eb = doc.findBlock(end_pos)
            n = eb.blockNumber()
            if eb.position() == end_pos and n > s:
                n -= 1
        else:
            s = n = doc.findBlock(cur.position()).blockNumber()
        cur.beginEditBlock()
        for i in range(s, n + 1):
            blk = doc.findBlockByNumber(i)
            text = blk.text()
            c = QTextCursor(blk)
            if text.startswith("\t"):
                c.deleteChar()
            elif text.startswith("    "):
                for _ in range(4):
                    c.deleteChar()
            elif text.startswith(" "):
                c.deleteChar()
        cur.endEditBlock()

    def _to_uppercase(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if cur.hasSelection():
            cur.insertText(cur.selectedText().upper())

    def _to_lowercase(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if cur.hasSelection():
            cur.insertText(cur.selectedText().lower())

    def _delete_selection(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if cur.hasSelection():
            cur.removeSelectedText()
        else:
            cur.deleteChar()
        e.setTextCursor(cur)

    def _quote_paste(self) -> None:
        e = self._editor
        if e is None:
            return
        text = QApplication.clipboard().text()
        if not text:
            return
        quoted = "\n".join("> " + ln for ln in text.splitlines())
        e.textCursor().insertText(quoted)

    def _to_hankaku(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if not cur.hasSelection():
            return
        result = []
        for ch in cur.selectedText():
            code = ord(ch)
            if 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            elif ch == "　":
                result.append(" ")
            else:
                result.append(ch)
        cur.insertText("".join(result))

    def _to_zenkaku(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if not cur.hasSelection():
            return
        result = []
        for ch in cur.selectedText():
            code = ord(ch)
            if 0x21 <= code <= 0x7E:
                result.append(chr(code + 0xFEE0))
            elif ch == " ":
                result.append("　")
            else:
                result.append(ch)
        cur.insertText("".join(result))

    def _space_indent(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        doc = e.document()
        if cur.hasSelection():
            s  = doc.findBlock(cur.selectionStart()).blockNumber()
            eb = doc.findBlock(cur.selectionEnd())
            n  = eb.blockNumber()
            if eb.position() == cur.selectionEnd() and n > s:
                n -= 1
        else:
            s = n = doc.findBlock(cur.position()).blockNumber()
        cur.beginEditBlock()
        for i in range(s, n + 1):
            QTextCursor(doc.findBlockByNumber(i)).insertText("    ")
        cur.endEditBlock()

    def _space_unindent(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        doc = e.document()
        if cur.hasSelection():
            s  = doc.findBlock(cur.selectionStart()).blockNumber()
            eb = doc.findBlock(cur.selectionEnd())
            n  = eb.blockNumber()
            if eb.position() == cur.selectionEnd() and n > s:
                n -= 1
        else:
            s = n = doc.findBlock(cur.position()).blockNumber()
        cur.beginEditBlock()
        for i in range(s, n + 1):
            blk  = doc.findBlockByNumber(i)
            text = blk.text()
            c    = QTextCursor(blk)
            if text.startswith("    "):
                for _ in range(4):
                    c.deleteChar()
            elif text.startswith(" "):
                c.deleteChar()
        cur.endEditBlock()

    def _delete_newlines(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if cur.hasSelection():
            # selectedText() uses U+2029 (paragraph separator), not actual newlines
            cur.insertText(cur.selectedText().replace(" ", ""))
        else:
            new_text = e.toPlainText().replace("\n", "").replace("\r", "")
            cur2 = QTextCursor(e.document())
            cur2.beginEditBlock()
            cur2.select(QTextCursor.SelectionType.Document)
            cur2.insertText(new_text)
            cur2.endEditBlock()

    # 段落先頭でインデントをスキップする文字（日本語文法による）
    _PARA_SKIP = frozenset(
        "「『（【〔〈《〖｢"   # 開き括弧・引用符
        "※・"               # 注記・箇条書き
        "─―—〜"            # 区切り・ダッシュ
    )

    def _para_indent(self) -> None:
        e = self._editor
        if e is None:
            return
        doc = e.document()
        cur = e.textCursor()
        cur.beginEditBlock()
        blk = doc.begin()
        while blk.isValid():
            text = blk.text()
            # 空行・空白のみはスキップ
            if not text.strip():
                blk = blk.next()
                continue
            # すでに全角スペースで始まる行はスキップ
            if text.startswith("　"):
                blk = blk.next()
                continue
            # 特定文字で始まる行はスキップ
            if text[0] in self._PARA_SKIP:
                blk = blk.next()
                continue
            # 段落先頭に全角スペースを挿入
            QTextCursor(blk).insertText("　")
            blk = blk.next()
        cur.endEditBlock()

    def _ruby_narou(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        selected = cur.selectedText()
        cur.beginEditBlock()
        cur.insertText(f"|{selected}《》")
        cur.endEditBlock()
        # カーソルを《》の間に移動
        cur.setPosition(cur.position() - 1)
        e.setTextCursor(cur)

    def _ruby_pixiv(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        selected = cur.selectedText()
        cur.beginEditBlock()
        cur.insertText(f"[[rb:{selected} > ルビ]]")
        cur.endEditBlock()
        # 「ルビ」を選択状態にしてすぐ入力できる状態に
        end = cur.position()
        cur.setPosition(end - 4)                                    # 「ルビ]]」の「ル」の前
        cur.setPosition(end - 2, QTextCursor.MoveMode.KeepAnchor)  # 「ルビ」を選択
        e.setTextCursor(cur)

    def _bouten_narou(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if not cur.hasSelection():
            return
        # 空白・改行（Qt の段落区切り U+2029 を含む）はそのまま通す
        result = "".join(ch if ch.isspace() else f"|{ch}《・》"
                         for ch in cur.selectedText())
        cur.insertText(result)

    def _bouten_pixiv(self) -> None:
        e = self._editor
        if e is None:
            return
        cur = e.textCursor()
        if not cur.hasSelection():
            return
        cur.insertText(f"[[emphasismark:{cur.selectedText()} > ﹅]]")

    def _toggle_readonly(self) -> None:
        e = self._editor
        if e is None:
            return
        e.setReadOnly(not e.isReadOnly())
        self._act_ro.setChecked(e.isReadOnly())

    def _update_edit_menu(self) -> None:
        e = self._editor
        has_sel  = e is not None and e.textCursor().hasSelection()
        has_clip = e is not None and QApplication.clipboard().mimeData().hasText()
        self._act_undo.setEnabled(e is not None and e.document().isUndoAvailable())
        self._act_redo.setEnabled(e is not None and e.document().isRedoAvailable())
        self._act_cut.setEnabled(has_sel)
        self._act_copy.setEnabled(has_sel)
        self._act_paste.setEnabled(has_clip)
        self._act_qpaste.setEnabled(has_clip)
        self._act_delete.setEnabled(has_sel)
        if e is not None:
            self._act_ro.setChecked(e.isReadOnly())

    def _update_conv_menu(self) -> None:
        e = self._editor
        has_sel = e is not None and e.textCursor().hasSelection()
        self._act_lower.setEnabled(has_sel)
        self._act_upper.setEnabled(has_sel)
        self._act_hankaku.setEnabled(has_sel)
        self._act_zenkaku.setEnabled(has_sel)
        self._act_del_nl.setEnabled(e is not None)

    def _update_kosei_menu(self) -> None:
        e = self._editor
        has_sel = e is not None and e.textCursor().hasSelection()
        self._act_ruby_narou.setEnabled(has_sel)
        self._act_ruby_pixiv.setEnabled(has_sel)
        self._act_bouten_narou.setEnabled(has_sel)
        self._act_bouten_pixiv.setEnabled(has_sel)

    # ------------------------------------------------------------------
    # Title / status
    # ------------------------------------------------------------------
    def _show_help(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("NaroEditor - 使い方")
        dlg.resize(720, 580)
        dlg.setStyleSheet(f"QDialog {{ background:{C['bg_panel']}; }}")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        browser = QTextBrowser(dlg)
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet(
            f"QTextBrowser {{ background:{C['bg']}; color:{C['fg']};"
            f" border:1px solid {C['border']}; border-radius:4px; padding:8px; }}"
        )
        browser.setHtml(f"""
<style>
  body  {{ font-family:'Yu Gothic UI',sans-serif; font-size:13px;
           color:{C['fg']}; background:{C['bg']}; margin:0; padding:4px; }}
  h2    {{ color:{C['accent']}; border-bottom:1px solid {C['border']};
           padding-bottom:4px; margin-top:18px; }}
  h3    {{ color:{C['green']}; margin-top:12px; margin-bottom:4px; }}
  table {{ border-collapse:collapse; width:100%; margin:6px 0; }}
  th    {{ background:{C['bg_panel']}; color:{C['fg_dim']};
           text-align:left; padding:4px 8px;
           border:1px solid {C['border']}; }}
  td    {{ padding:4px 8px; border:1px solid {C['border']}; }}
  code  {{ background:{C['bg_panel']}; color:{C['accent']};
           padding:1px 4px; border-radius:3px; font-size:12px; }}
</style>
<h2>📄 ファイル操作</h2>
<table><tr><th>操作</th><th>ショートカット</th></tr>
<tr><td>新規タブ</td><td><code>Ctrl+N</code></td></tr>
<tr><td>ファイルを開く</td><td><code>Ctrl+O</code></td></tr>
<tr><td>上書き保存</td><td><code>Ctrl+S</code></td></tr>
<tr><td>名前を付けて保存</td><td><code>Ctrl+Shift+S</code></td></tr>
<tr><td>タブを閉じる</td><td><code>Ctrl+W</code></td></tr>
</table>

<h2>✏️ 編集操作</h2>
<table><tr><th>操作</th><th>ショートカット</th></tr>
<tr><td>元に戻す</td><td><code>Ctrl+Z</code></td></tr>
<tr><td>やり直し</td><td><code>Ctrl+Y</code></td></tr>
<tr><td>切り取り</td><td><code>Ctrl+X</code></td></tr>
<tr><td>コピー</td><td><code>Ctrl+C</code></td></tr>
<tr><td>貼り付け</td><td><code>Ctrl+V</code></td></tr>
<tr><td>引用符付き貼り付け</td><td><code>Ctrl+Q</code></td></tr>
<tr><td>削除</td><td>—</td></tr>
<tr><td>行削除</td><td><code>Ctrl+Enter</code></td></tr>
<tr><td>すべて選択</td><td><code>Ctrl+A</code></td></tr>
<tr><td>書き換え禁止（読み取り専用）</td><td><code>Shift+Ctrl+N</code></td></tr>
</table>

<h2>🔄 変換（編集 → 変換）</h2>
<table><tr><th>操作</th><th>ショートカット</th></tr>
<tr><td>小文字に変換</td><td><code>Ctrl+L</code></td></tr>
<tr><td>大文字に変換</td><td><code>Shift+Ctrl+L</code></td></tr>
<tr><td>半角に変換</td><td><code>Ctrl+G</code></td></tr>
<tr><td>全角に変換</td><td><code>Shift+Ctrl+G</code></td></tr>
<tr><td>TABインデント</td><td><code>Tab</code>（選択時）</td></tr>
<tr><td>TAB逆インデント</td><td><code>Shift+Tab</code>（選択時）</td></tr>
<tr><td>空白インデント</td><td><code>Shift+Ctrl+I</code></td></tr>
<tr><td>空白逆インデント</td><td><code>Shift+Ctrl+U</code></td></tr>
<tr><td>改行削除</td><td><code>Shift+Ctrl+T</code></td></tr>
</table>

<h2>🔍 検索・置換</h2>
<table><tr><th>操作</th><th>ショートカット</th></tr>
<tr><td>検索</td><td><code>Ctrl+F</code></td></tr>
<tr><td>置換</td><td><code>Ctrl+R</code></td></tr>
</table>

<h2>✒️ 校正機能</h2>
<table><tr><th>操作</th><th>ショートカット</th><th>変換例</th></tr>
<tr><td>段落下げ</td><td>—</td><td>文頭に全角スペースを自動挿入（会話行等はスキップ）</td></tr>
<tr><td>ルビ（なろう/カクヨム）</td><td><code>Alt+R</code></td><td>選択 → <code>|文字《ルビ》</code></td></tr>
<tr><td>ルビ（Pixiv）</td><td><code>Alt+E</code></td><td>選択 → <code>[[rb:文字 &gt; ルビ]]</code></td></tr>
<tr><td>傍点（なろう/カクヨム）</td><td><code>Alt+/</code></td><td>選択 → <code>|文《・》|字《・》</code></td></tr>
<tr><td>傍点（Pixiv）</td><td><code>Alt+.</code></td><td>選択 → <code>[[emphasismark:文字 &gt; ﹅]]</code></td></tr>
</table>

<h2>📑 タブ・ペイン操作</h2>
<h3>タブ</h3>
<ul>
<li>タブをドラッグ → タブバー内でスライド移動、バー外でフローティング表示</li>
<li>タブをエディタ右端（60%超）にドロップ → 左右に分割</li>
<li>タブをエディタ下端（60%超）にドロップ → 上下に分割</li>
<li>タブをもう一方のペインにドロップ → ペインを結合</li>
<li>タブを中クリック → タブを閉じる</li>
</ul>
<h3>行番号エリア</h3>
<ul>
<li>行番号をクリック → その行全体を選択</li>
<li>行番号をドラッグ → 複数行を選択</li>
</ul>
<h3>ペイン分割（表示メニュー）</h3>
<table><tr><th>操作</th><th>条件</th></tr>
<tr><td>左右に分割</td><td>1ペイン・タブ2枚以上の時</td></tr>
<tr><td>上下に分割</td><td>1ペイン・タブ2枚以上の時</td></tr>
<tr><td>ペインを結合</td><td>2ペイン時</td></tr>
</table>

<h2>👁 プレビュー</h2>
<ul>
<li><code>Ctrl+Shift+P</code> でMarkdownプレビューを表示/非表示</li>
<li>プレビューをドッキングするとエディタ右側に常時表示</li>
<li>アクティブなタブの内容がリアルタイムで反映される</li>
</ul>
""")
        layout.addWidget(browser)
        btn = QPushButton("閉じる", dlg)
        btn.clicked.connect(dlg.accept)
        btn.setFixedWidth(100)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn)
        layout.addLayout(btn_row)
        dlg.exec()

    def _show_about(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("バージョン情報")
        dlg.setFixedSize(340, 200)
        dlg.setStyleSheet(f"QDialog {{ background:{C['bg_panel']}; }}")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(8)

        title = QLabel("NaroEditor")
        title.setStyleSheet(
            f"color:{C['accent']}; font-size:20px; font-weight:bold; background:transparent;"
        )
        layout.addWidget(title)

        for text in (
            f"バージョン: {APP_VERSION}",
            "PyQt6 ベースの日本語テキストエディタ",
        ):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color:{C['fg']}; font-size:13px; background:transparent;")
            layout.addWidget(lbl)

        layout.addStretch()

        btn = QPushButton("OK", dlg)
        btn.clicked.connect(dlg.accept)
        btn.setFixedWidth(80)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn)
        layout.addLayout(btn_row)
        dlg.exec()

    def _update_window_title(self) -> None:
        cur = self._editor
        if cur is None:
            self.setWindowTitle("NaroEditor")
            return
        name = os.path.basename(cur.file_path) if cur.file_path else "新規ファイル"
        prefix = "* " if cur.document().isModified() else ""
        self.setWindowTitle(f"{prefix}NaroEditor — {name}")

    def _update_status(self) -> None:
        cur = self._editor
        if cur is None:
            self._char_lbl.setText("文字数: 0")
            self._enc_lbl.setText("UTF-8")
            return
        self._char_lbl.setText(f"文字数: {cur.document().characterCount() - 1:,}")
        enc = cur.file_encoding.upper().replace("_", "-")
        enc = enc.replace("UTF-8-SIG", "UTF-8 (BOM)").replace("CP932", "Shift-JIS")
        self._enc_lbl.setText(enc)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # ANGLE/DirectX を使用することで、OpenGL ドライバーが不安定な環境でも
    # Qt のレンダリングを安定させる。
    os.environ.setdefault("QT_OPENGL", "angle")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_QSS)
    window = NaroEditor()
    window.show()
    sys.exit(app.exec())
