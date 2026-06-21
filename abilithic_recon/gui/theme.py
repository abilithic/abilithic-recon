"""Brand palette + Qt stylesheets (dark / light)."""
from __future__ import annotations

# Abilithic brand palette
CHARCOAL = "#0c1118"
SLATE = "#161e29"
SLATE2 = "#1d2734"
LINE = "#26303f"
TEXT = "#e7edf5"
MUTED = "#8c97a8"
ACCENT = "#48f3d2"
ACCENT_DK = "#0fb497"

SEV_COLORS = {
    "CRITICAL": "#ff5c7a",
    "HIGH": "#ff9f43",
    "MEDIUM": "#ffd166",
    "LOW": "#62d5b8",
    "INFO": "#8c97a8",
}

_DARK = f"""
QMainWindow, QWidget {{ background:{CHARCOAL}; color:{TEXT};
  font-family:'Segoe UI','Roboto',Arial,sans-serif; font-size:13px; }}
QMenuBar {{ background:{SLATE}; color:{TEXT}; }}
QMenuBar::item:selected {{ background:{SLATE2}; }}
QMenu {{ background:{SLATE}; color:{TEXT}; border:1px solid {LINE}; }}
QMenu::item:selected {{ background:{ACCENT_DK}; color:{CHARCOAL}; }}
QLineEdit {{ background:{SLATE2}; border:1px solid {LINE}; border-radius:8px;
  padding:8px 10px; color:{TEXT}; selection-background-color:{ACCENT_DK}; }}
QLineEdit:focus {{ border:1px solid {ACCENT}; }}
QPushButton {{ background:{ACCENT}; color:{CHARCOAL}; border:none; border-radius:8px;
  padding:8px 16px; font-weight:600; }}
QPushButton:hover {{ background:{ACCENT_DK}; color:{TEXT}; }}
QPushButton:disabled {{ background:{LINE}; color:{MUTED}; }}
QPushButton#secondary {{ background:{SLATE2}; color:{TEXT}; border:1px solid {LINE}; }}
QPushButton#secondary:hover {{ border:1px solid {ACCENT}; }}
QComboBox {{ background:{SLATE2}; border:1px solid {LINE}; border-radius:8px; padding:6px 10px; }}
QComboBox QAbstractItemView {{ background:{SLATE}; selection-background-color:{ACCENT_DK}; }}
QFrame#card {{ background:{SLATE}; border:1px solid {LINE}; border-radius:12px; }}
QLabel#cardNum {{ font-size:24px; font-weight:700; color:{TEXT}; }}
QLabel#cardLbl {{ color:{MUTED}; font-size:11px; }}
QTableView {{ background:{SLATE}; gridline-color:{LINE}; border:1px solid {LINE};
  border-radius:10px; selection-background-color:{ACCENT_DK}; selection-color:{CHARCOAL}; }}
QHeaderView::section {{ background:{SLATE2}; color:{MUTED}; border:none;
  border-bottom:1px solid {LINE}; padding:8px; }}
QTextEdit, QPlainTextEdit {{ background:{SLATE}; border:1px solid {LINE}; border-radius:10px; }}
QProgressBar {{ background:{SLATE2}; border:1px solid {LINE}; border-radius:8px; text-align:center;
  color:{TEXT}; height:18px; }}
QProgressBar::chunk {{ background:{ACCENT}; border-radius:7px; }}
QStatusBar {{ background:{SLATE}; color:{MUTED}; }}
QSplitter::handle {{ background:{LINE}; }}
QScrollBar:vertical {{ background:{CHARCOAL}; width:10px; }}
QScrollBar::handle:vertical {{ background:{LINE}; border-radius:5px; }}
QToolTip {{ background:{SLATE2}; color:{TEXT}; border:1px solid {ACCENT}; padding:6px; }}
"""

_LIGHT = """
QMainWindow, QWidget { background:#f4f6fa; color:#1b2533;
  font-family:'Segoe UI','Roboto',Arial,sans-serif; font-size:13px; }
QLineEdit { background:#fff; border:1px solid #cdd5e0; border-radius:8px; padding:8px 10px; }
QPushButton { background:#0fb497; color:#fff; border:none; border-radius:8px; padding:8px 16px; font-weight:600; }
QPushButton:disabled { background:#cdd5e0; color:#8c97a8; }
QFrame#card { background:#fff; border:1px solid #e0e6ee; border-radius:12px; }
QTableView { background:#fff; gridline-color:#e0e6ee; border:1px solid #e0e6ee; border-radius:10px; }
QHeaderView::section { background:#eef1f6; color:#5a6675; border:none; border-bottom:1px solid #e0e6ee; padding:8px; }
"""


def stylesheet(theme: str) -> str:
    return _LIGHT if theme == "light" else _DARK
