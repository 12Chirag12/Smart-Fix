"""
SmartFix AI — Proper Windows Application (PyQt6)
Main Window: Dashboard + System Tray + Live Monitor + Alert Popups
"""
import sys
import os
import threading
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, List


ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Auto-load .env configuration if present
_env_path = os.path.join(ROOT, ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QDialog, QProgressBar,
    QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem, QStackedWidget,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QSize, QPoint
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QPainter, QPen, QBrush,
    QPixmap, QLinearGradient, QPalette, QAction, QFontDatabase
)
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


from monitor.error_catalog import ERROR_CATALOG, CATALOG_LIST
from monitor.monitor import BackgroundMonitor
from monitor.repair_engine import execute_repair

from monitor.history import get_history, get_stats, clear_history, log_repair, log_ignore, log_detection, get_stats, clear_history
from monitor.network_diag import run_full_diagnostics
import webbrowser

from monitor.ai_dialog import AIAssistantDialog
from monitor.demo_mode import DemoController, DEMO_SCENARIOS, DEMO_LIST
from monitor.lab_config import (
    get_mode, set_mode, get_seat_name, set_seat_name, get_local_ip, LAB_PORT,
    verify_admin_passkey, set_admin_passkey, DEFAULT_PASSKEY
)
from monitor.lab_agent import LabClientAgent
from monitor.lab_admin import LabAdminManager, ClientInfo

_log_level_str = os.getenv("SMARTFIX_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_str, logging.INFO)
logging.basicConfig(level=_log_level,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smartfix.app")


BG_MAIN    = "#0E0F14"
BG_SIDEBAR = "#09090D"
BG_CARD    = "#13141A"
BG_CARD2   = "#1A1B23"
BORDER     = "#1E2030"
BORDER2    = "#2A2D40"
ACCENT     = "#5B6EF5"
GREEN      = "#34D399"
RED        = "#F87171"
ORANGE     = "#FB923C"
YELLOW     = "#FBBF24"
TEXT1      = "#E8EAF0"
TEXT2      = "#8B8FA8"
TEXT3      = "#4A4D62"

SEV_COLORS = {"CRITICAL": RED, "HIGH": ORANGE, "MEDIUM": YELLOW, "LOW": ACCENT}
SEV_ICONS  = {"CRITICAL": "C", "HIGH": "H", "MEDIUM": "M", "LOW": "L"}

STYLESHEET = f"""
QWidget {{
    background-color: {BG_MAIN};
    color: {TEXT1};
    font-family: 'Segoe UI Variable Text', 'Segoe UI', system-ui, sans-serif;
    font-size: 13px;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER2};
    border-radius: 2px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QTableWidget {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    outline: 0;
}}
QTableWidget::item {{ padding: 8px 16px; border-bottom: 1px solid {BORDER}; }}
QTableWidget::item:selected {{ background: {ACCENT}15; color: {TEXT1}; }}
QHeaderView::section {{
    background: {BG_CARD};
    color: {TEXT3};
    padding: 8px 16px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}}
QTextEdit {{
    background: {BG_SIDEBAR};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 10px 12px;
    color: {TEXT2};
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    line-height: 1.5;
}}
"""



class RepairWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, repair_id: str):
        super().__init__()
        self.repair_id = repair_id

    def run(self):
        result = execute_repair(self.repair_id)
        self.finished.emit(result)



class AlertBridge(QThread):
    """Bridges monitor alerts from background threads to Qt signals."""
    alert_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._queue = []
        self._lock = threading.Lock()
        self._monitor = None

    def set_monitor(self, monitor):
        self._monitor = monitor

    def on_alert(self, error_info: dict):
        self.alert_received.emit(error_info)



class StatCard(QFrame):
    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(6)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"""
            color: {TEXT1};
            font-size: 28px;
            font-weight: 700;
            background: transparent;
            border: none;
            letter-spacing: -0.5px;
        """)
        layout.addWidget(self.value_lbl)

        row = QHBoxLayout()
        row.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background: {color}; border-radius: 3px; border: none;")
        row.addWidget(dot)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 11px; font-weight: 500; background: transparent; border: none;")
        row.addWidget(title_lbl)
        row.addStretch()
        layout.addLayout(row)

    def set_value(self, v: str):
        self.value_lbl.setText(v)



class AlertItem(QFrame):
    def __init__(self, error_info: dict, on_fix, on_ignore, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        sev   = error_info.get("severity", "HIGH")
        color = SEV_COLORS.get(sev, ORANGE)

        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 2px solid {color};
                border-radius: 4px;
            }}
            QFrame:hover {{ border-color: {BORDER2}; border-left: 2px solid {color}; }}
        """)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 12, 12, 12)
        outer.setSpacing(14)

        # Severity indicator dot
        dot_col = QVBoxLayout()
        dot_col.setAlignment(Qt.AlignmentFlag.AlignTop)
        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background: {color}; border-radius: 4px; border: none; margin-top: 4px;")
        dot_col.addWidget(dot)
        outer.addLayout(dot_col)

        # Content
        mid = QVBoxLayout()
        mid.setSpacing(3)

        name_lbl = QLabel(error_info.get("name", "Unknown Error"))
        name_lbl.setStyleSheet(f"color: {TEXT1}; font-weight: 600; font-size: 13px; background: transparent; border: none;")
        mid.addWidget(name_lbl)

        desc_text = error_info.get("description", "")
        if len(desc_text) > 90:
            desc_text = desc_text[:90] + "..."
        desc = QLabel(desc_text)
        desc.setStyleSheet(f"color: {TEXT2}; font-size: 11px; background: transparent; border: none;")
        desc.setWordWrap(True)
        mid.addWidget(desc)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)

        sev_lbl = QLabel(sev)
        sev_lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 600; background: transparent; border: none;")
        meta_row.addWidget(sev_lbl)

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none;")
        meta_row.addWidget(sep)

        cat_lbl = QLabel(error_info.get("category", "System"))
        cat_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none;")
        meta_row.addWidget(cat_lbl)

        ts = error_info.get("detected_at", "")[:16].replace("T", " ")
        if ts:
            sep2 = QLabel("|")
            sep2.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none;")
            meta_row.addWidget(sep2)
            time_lbl = QLabel(ts)
            time_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none;")
            meta_row.addWidget(time_lbl)

        meta_row.addStretch()
        mid.addLayout(meta_row)
        outer.addLayout(mid, 1)

        # Action buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(6)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        fix_btn = QPushButton("Fix")
        fix_btn.setFixedSize(64, 28)
        fix_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #6D7EF7; }}
            QPushButton:pressed {{ background: #4A5BE0; }}
        """)
        fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fix_btn.clicked.connect(lambda: on_fix(error_info, self))
        btn_col.addWidget(fix_btn)

        ign_btn = QPushButton("Ignore")
        ign_btn.setFixedSize(64, 28)
        ign_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT3};
                border: 1px solid {BORDER};
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {TEXT2}; border-color: {BORDER2}; }}
        """)
        ign_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ign_btn.clicked.connect(lambda: on_ignore(self))
        btn_col.addWidget(ign_btn)

        outer.addLayout(btn_col)



class RepairDialog(QDialog):
    def __init__(self, error_info: dict, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        self.repair_id  = error_info.get("repair_id", "")
        self.worker     = None

        self.setWindowTitle("SmartFix — Repairing")
        self.setMinimumSize(520, 400)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_CARD}; }}
            QLabel  {{ background: transparent; border: none; }}
        """)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self._build_ui()
        self._start_repair()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        brand = QLabel("🛡 SmartFix AI")
        brand.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 15px;")
        hdr.addWidget(brand)
        hdr.addStretch()
        layout.addLayout(hdr)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(div)

        # Title row
        title_row = QHBoxLayout()
        self.status_icon = QLabel("⚙️")
        self.status_icon.setStyleSheet("font-size: 28px;")
        title_row.addWidget(self.status_icon)

        title_col = QVBoxLayout()
        self.title_lbl = QLabel("Repair in Progress…")
        self.title_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 16px; font-weight: bold;")
        title_col.addWidget(self.title_lbl)

        error_lbl = QLabel(self.error_info.get("name", ""))
        error_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        title_col.addWidget(error_lbl)
        title_row.addLayout(title_col)
        layout.addLayout(title_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {BORDER};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {ACCENT};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)

        # Log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(120)
        self.log_box.setPlaceholderText("Running repair scripts…")
        layout.addWidget(self.log_box)

        # Result frame
        self.result_frame = QFrame()
        self.result_frame.setStyleSheet(f"background: {BG_CARD2}; border-radius: 8px; border: 1px solid {BORDER};")
        self.result_frame.setVisible(False)
        res_layout = QHBoxLayout(self.result_frame)
        self.result_icon = QLabel("✅")
        self.result_icon.setStyleSheet("font-size: 22px;")
        res_layout.addWidget(self.result_icon)
        self.result_lbl = QLabel("Repair successful!")
        self.result_lbl.setStyleSheet(f"color: {GREEN}; font-weight: bold; font-size: 13px;")
        res_layout.addWidget(self.result_lbl)
        layout.addWidget(self.result_frame)

        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: #3D7ADB; }}
        """)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _start_repair(self):
        self.log_box.append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting repair: {self.repair_id}")
        self.worker = RepairWorker(self.repair_id)
        self.worker.finished.connect(self._on_repair_done)
        self.worker.start()

    def _on_repair_done(self, result: dict):
        success = result.get("success", False)
        output  = result.get("output", "")[:800]
        elapsed = result.get("elapsed_seconds", 0)

        self.log_box.append(f"\n[Output]\n{output}")
        self.log_box.append(f"\n[Elapsed: {elapsed}s]")

        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        log_repair(self.error_info, result)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {BORDER};
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: {'#00D26A' if success else RED};
                border-radius: 3px;
            }}
        """)

        self.result_frame.setVisible(True)
        if success:
            self.status_icon.setText("✅")
            self.title_lbl.setText("Repair Successful!")
            self.title_lbl.setStyleSheet(f"color: {GREEN}; font-size: 16px; font-weight: bold;")
            self.result_icon.setText("✅")
            self.result_lbl.setText("The issue has been resolved successfully.")
            self.result_lbl.setStyleSheet(f"color: {GREEN}; font-weight: bold; font-size: 13px;")
        else:
            self.status_icon.setText("❌")
            self.title_lbl.setText("Repair Encountered Issues")
            self.title_lbl.setStyleSheet(f"color: {RED}; font-size: 16px; font-weight: bold;")
            self.result_icon.setText("⚠️")
            self.result_lbl.setText("Some steps may require Administrator rights.")
            self.result_lbl.setStyleSheet(f"color: {ORANGE}; font-weight: bold; font-size: 13px;")

        self.close_btn.setVisible(True)


class AlertPopup(QDialog):
    """Clean Windows-11 style toast notification — bottom right corner. CRITICAL only."""

    def __init__(self, error_info: dict, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        self._countdown = 30
        self._color = RED

        self.setFixedWidth(380)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._build_ui()
        self._position()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        card = QFrame()
        card.setObjectName("toast")
        card.setStyleSheet(f"""
            QFrame#toast {{
                background: {BG_CARD};
                border-radius: 14px;
                border: 1px solid {BORDER};
                border-top: 2px solid {RED};
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)

        outer.addWidget(card)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(10)

        # Header row
        hdr = QHBoxLayout()
        app_lbl = QLabel("SmartFix AI")
        app_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 10px; font-weight: 700; letter-spacing: 0.06em; background: transparent;")
        hdr.addWidget(app_lbl)
        hdr.addStretch()

        time_lbl = QLabel(datetime.now().strftime("%H:%M"))
        time_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent;")
        hdr.addWidget(time_lbl)

        x_btn = QPushButton("✕")
        x_btn.setFixedSize(18, 18)
        x_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        x_btn.setStyleSheet(f"QPushButton {{ background: transparent; border: none; color: {TEXT3}; font-size: 11px; margin-left: 8px; }} QPushButton:hover {{ color: {RED}; }}")
        x_btn.clicked.connect(self._ignore)
        hdr.addWidget(x_btn)
        cl.addLayout(hdr)

        # Thin separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER};")
        cl.addWidget(sep)

        # Error row — icon + title stacked
        err_row = QHBoxLayout()
        err_row.setSpacing(12)

        # Red exclamation circle
        icon_lbl = QLabel("⚠")
        icon_lbl.setFixedWidth(36)
        icon_lbl.setFixedHeight(36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 18px; color: {RED}; background: {RED}18; border-radius: 18px;")
        err_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        name = self.error_info.get("name", "Unknown Error")
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 13px; font-weight: 600; background: transparent;")
        name_lbl.setWordWrap(True)
        title_col.addWidget(name_lbl)

        cat = self.error_info.get("category", "System")
        cat_lbl = QLabel(f"Critical  ·  {cat}")
        cat_lbl.setStyleSheet(f"color: {RED}; font-size: 10px; font-weight: 600; background: transparent;")
        title_col.addWidget(cat_lbl)
        err_row.addLayout(title_col)
        cl.addLayout(err_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        fix_btn = QPushButton("Fix Now")
        fix_btn.setFixedHeight(34)
        fix_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: #818CF8; }}
            QPushButton:pressed {{ background: #4F46E5; }}
        """)
        fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fix_btn.clicked.connect(self._fix)
        btn_row.addWidget(fix_btn)

        ign_btn = QPushButton("Dismiss")
        ign_btn.setFixedHeight(34)
        ign_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT2};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {BG_CARD2}; color: {TEXT1}; }}
        """)
        ign_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ign_btn.clicked.connect(self._ignore)
        btn_row.addWidget(ign_btn)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        # Progress bar countdown
        self.countdown_bar = QProgressBar()
        self.countdown_bar.setRange(0, 30)
        self.countdown_bar.setValue(30)
        self.countdown_bar.setFixedHeight(2)
        self.countdown_bar.setTextVisible(False)
        self.countdown_bar.setStyleSheet(f"""
            QProgressBar {{ background: {BORDER}20; border-radius: 1px; border: none; }}
            QProgressBar::chunk {{ background: {ACCENT}; border-radius: 1px; }}
        """)
        cl.addWidget(self.countdown_bar)

    def _position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.adjustSize()
        target_x = screen.right() - self.width() - 20
        target_y = screen.bottom() - self.height() - 20
        self.move(screen.right() + 50, target_y)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(350)
        self.animation.setStartValue(QPoint(screen.right() + 50, target_y))
        self.animation.setEndValue(QPoint(target_x, target_y))
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

    def _tick(self):
        self._countdown -= 1
        self.countdown_bar.setValue(self._countdown)
        if self._countdown <= 0:
            self._ignore()

    def _fix(self):
        self._timer.stop()
        main_win = self.parent()
        if main_win and hasattr(main_win, "_popup_visible"):
            main_win._popup_visible = False
        self.hide()
        if main_win and hasattr(main_win, "resolve_alert_from_popup"):
            main_win.resolve_alert_from_popup(self.error_info)
        else:
            if self.error_info.get("repair_id") == "unknown_error":
                dlg = AIAssistantDialog(self.error_info, self)
            else:
                dlg = RepairDialog(self.error_info, self)
            dlg.exec()
        self.close()

    def _ignore(self):
        self._timer.stop()
        main_win = self.parent()
        if main_win and hasattr(main_win, "_popup_visible"):
            main_win._popup_visible = False
        self.close()

    def closeEvent(self, event):
        self._timer.stop()
        main_win = self.parent()
        if main_win and hasattr(main_win, "_popup_visible"):
            main_win._popup_visible = False
        super().closeEvent(event)



class MetricWorkerThread(QThread):
    """
    Dedicated background worker thread that continuously samples system metrics
    matching Windows Task Manager real-time performance monitoring.
    Samples every 800ms for authentic, dynamic percentage fluctuations.
    """
    metrics_ready = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def run(self):
        import psutil
        critical_svcs = ['Spooler', 'WSearch', 'AudioSrv', 'wuauserv', 'bthserv']

        # Initial prime
        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        while self._running:
            try:
                # interval=0.8 accurately samples CPU across all cores, exactly matching Task Manager
                cpu = psutil.cpu_percent(interval=0.8)
                cores = psutil.cpu_count(logical=True) or 1
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage('C:\\')

                # Critical services count
                running_svcs = 0
                for s in critical_svcs:
                    try:
                        svc = psutil.win_service_get(s)
                        if svc.status() == 'running':
                            running_svcs += 1
                    except Exception:
                        pass

                # System uptime
                boot_time = psutil.boot_time()
                uptime_s = int(time.time() - boot_time)
                days = uptime_s // 86400
                hrs = (uptime_s % 86400) // 3600
                mins = (uptime_s % 3600) // 60
                uptime_str = f"{days}d {hrs}h {mins}m" if days > 0 else f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

                # Quick network ping check
                net_ok = True
                try:
                    import socket
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.3)
                    s.connect(("8.8.8.8", 53))
                    s.close()
                except Exception:
                    net_ok = False

                self.metrics_ready.emit({
                    "__type__": "metric_update",
                    "cpu": cpu,
                    "cores": cores,
                    "ram_pct": mem.percent,
                    "ram_used_gb": mem.used / (1024**3),
                    "ram_total_gb": mem.total / (1024**3),
                    "disk_pct": disk.percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "svcs_running": running_svcs,
                    "svcs_total": len(critical_svcs),
                    "net_ok": net_ok,
                    "uptime_str": uptime_str,
                })
            except Exception:
                time.sleep(1.0)

    def stop(self):
        self._running = False
        self.wait(1200)


class MainWindow(QMainWindow):
    _alert_signal = pyqtSignal(dict)

    def __init__(self, is_background: bool = False):
        super().__init__()
        self.is_background = is_background
        self.setWindowTitle("SmartFix AI — Windows Error Monitor")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(STYLESHEET)

        self._alerts: List[dict] = []
        self._alert_count = 0
        self._fixed_count = 0
        self._ignored_count = 0
        self._monitor = None
        self._demo = None
        self._active_popups: List[AlertPopup] = []
        # Track IDs of alerts currently showing in the alerts list (prevents duplicate entries)
        self._active_alert_ids: set = set()
        # Prevent popup spam — only 1 popup at a time
        self._popup_visible: bool = False

        # Lab Monitor
        self._lab_agent: Optional[LabClientAgent] = None
        self._lab_admin: Optional[LabAdminManager] = None
        self._lab_mode: str = "unset"   # "admin" | "client" | "unset"

        self._alert_signal.connect(self._show_alert)

        self._build_ui()
        self._setup_tray()
        self._start_monitor()
        self._start_metric_timer()
        self._start_lab_services()

        # Single-instance server: wake up when user launches app again
        try:
            self._single_instance_server = QLocalServer(self)
            self._single_instance_server.removeServer("SmartFixAI_SingleInstance")
            self._single_instance_server.listen("SmartFixAI_SingleInstance")
            self._single_instance_server.newConnection.connect(self._on_single_instance_ping)
        except Exception as e:
            logger.debug(f"Single-instance server error: {e}")

        # Clean shutdown on application exit
        app_inst = QApplication.instance()
        if app_inst:
            app_inst.aboutToQuit.connect(self._cleanup_on_quit)

        # Ensure auto-start on PC boot is registered in background
        threading.Thread(target=ensure_windows_autostart, daemon=True).start()

    def _cleanup_on_quit(self):
        try:
            if hasattr(self, "_metric_worker") and self._metric_worker:
                self._metric_worker.stop()
            if self._lab_agent:
                self._lab_agent.stop()
            if self._lab_admin:
                self._lab_admin.stop()
            if self._monitor:
                self._monitor.stop()
        except Exception as e:
            logger.debug(f"Quit cleanup note: {e}")

    def _on_single_instance_ping(self):
        """Called when a second instance tries to launch — bring this window to foreground."""
        try:
            sock = self._single_instance_server.nextPendingConnection()
            if sock:
                def _read_and_show():
                    try:
                        data = sock.readAll().data().decode("utf-8", errors="ignore")
                        if "SHOW" in data or not data.strip():
                            self.show_and_raise()
                    except Exception:
                        self.show_and_raise()
                    sock.disconnectFromServer()
                sock.readyRead.connect(_read_and_show)
                QTimer.singleShot(400, self.show_and_raise)
        except Exception as e:
            logger.debug(f"Error handling single-instance ping: {e}")

    

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        
        sidebar = self._make_sidebar()
        root.addWidget(sidebar)

        
        self.stack = QStackedWidget()
        self.stack.addWidget(self._make_dashboard())    # 0
        self.stack.addWidget(self._make_alerts_page())  # 1
        self.stack.addWidget(self._make_catalog_page()) # 2
        self.stack.addWidget(self._make_demo_page())    # 3
        self.stack.addWidget(self._make_history_page()) # 4
        self.stack.addWidget(self._make_network_page()) # 5
        self.stack.addWidget(self._make_lab_page())     # 6
        root.addWidget(self.stack, 1)

    def _make_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(60)
        logo_frame.setStyleSheet(f"background: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER};")
        logo_l = QHBoxLayout(logo_frame)
        logo_l.setContentsMargins(16, 0, 16, 0)

        icon_box = QLabel("SF")
        icon_box.setFixedSize(28, 28)
        icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_box.setStyleSheet(f"""
            background: {ACCENT};
            color: white;
            border-radius: 6px;
            border: none;
            font-size: 11px;
            font-weight: 700;
        """)
        logo_l.addWidget(icon_box)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand_lbl = QLabel("SmartFix")
        brand_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        brand_col.addWidget(brand_lbl)
        sub_lbl = QLabel("Error Monitor")
        sub_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none;")
        brand_col.addWidget(sub_lbl)
        logo_l.addLayout(brand_col)
        logo_l.addStretch()
        layout.addWidget(logo_frame)

        # Status pill
        self.status_frame = QFrame()
        self.status_frame.setFixedHeight(36)
        self.status_frame.setStyleSheet(f"background: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER};")
        status_l = QHBoxLayout(self.status_frame)
        status_l.setContentsMargins(16, 0, 16, 0)
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(6, 6)
        self.status_dot.setStyleSheet(f"background: {GREEN}; border-radius: 3px; border: none;")
        status_l.addWidget(self.status_dot)
        self.status_lbl = QLabel("Monitoring")
        self.status_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 10px; background: transparent; border: none; margin-left: 6px;")
        status_l.addWidget(self.status_lbl)
        status_l.addStretch()
        layout.addWidget(self.status_frame)

        # Nav section label
        nav_section = QLabel("NAVIGATION")
        nav_section.setStyleSheet(f"color: {TEXT3}; font-size: 9px; font-weight: 700; letter-spacing: 0.1em; background: transparent; border: none; padding: 14px 16px 6px 16px;")
        layout.addWidget(nav_section)

        nav_items = [
            ("Dashboard",     0),
            ("Active Alerts", 1),
            ("Error Catalog", 2),
            ("Demo Mode",     3),
            ("History",       4),
            ("Network",       5),
            ("Lab Monitor",   6),
        ]

        nav_wrap = QWidget()
        nav_wrap.setStyleSheet("background: transparent;")
        nav_l = QVBoxLayout(nav_wrap)
        nav_l.setContentsMargins(8, 0, 8, 0)
        nav_l.setSpacing(1)

        self._nav_btns = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setFixedHeight(34)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT2};
                    border: none;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 12px;
                    border-radius: 4px;
                    font-weight: 400;
                }}
                QPushButton:hover {{
                    background: {BG_CARD};
                    color: {TEXT1};
                }}
                QPushButton:checked {{
                    background: {BG_CARD};
                    color: {TEXT1};
                    font-weight: 500;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._nav(i, b))
            self._nav_btns.append(btn)
            nav_l.addWidget(btn)

        layout.addWidget(nav_wrap)
        self._nav_btns[0].setChecked(True)
        layout.addStretch()

        ver_lbl = QLabel("v1.0")
        ver_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 9px; background: transparent; border: none; padding: 10px 16px;")
        layout.addWidget(ver_lbl)

        return sidebar

    def _nav(self, idx: int, btn: QPushButton):
        for b in self._nav_btns:
            b.setChecked(False)
        btn.setChecked(True)
        self.stack.setCurrentIndex(idx)

    def _make_dashboard(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        
        title_row = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;")
        title_row.addWidget(title)
        title_row.addStretch()

        self.last_scan_lbl = QLabel("Scanning…")
        self.last_scan_lbl.setStyleSheet(f"color: {TEXT3}; font-size: 11px; background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 12px;")
        title_row.addWidget(self.last_scan_lbl)
        layout.addLayout(title_row)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        self.card_alerts    = StatCard("Active Alerts",     "0",                     RED)
        self.card_fixed     = StatCard("Issues Fixed",      "0",                     GREEN)
        self.card_monitored = StatCard("Errors Monitored",  str(len(CATALOG_LIST)),  ACCENT)
        self.card_uptime    = StatCard("Uptime",            "0m",                    TEXT3)

        for card in [self.card_alerts, self.card_fixed, self.card_monitored, self.card_uptime]:
            card.setFixedHeight(100)
            cards_row.addWidget(card)
        layout.addLayout(cards_row)

        health_row = QHBoxLayout()
        health_title = QLabel("System Health")
        health_title.setStyleSheet(f"color: {TEXT2}; font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;")
        health_row.addWidget(health_title)
        health_row.addStretch()
        layout.addLayout(health_row)

        health_grid = QGridLayout()
        health_grid.setSpacing(8)

        self.health_widgets = {}
        health_items = [
            ("CPU Usage",         "cpu",    "--"),
            ("Memory Usage",      "ram",    "--"),
            ("Disk (C:)",         "disk",   "--"),
            ("Network",           "net",    "--"),
            ("Critical Services", "svc",    "--"),
            ("Recent Alerts",     "errors", "--"),
        ]
        for i, (label, key, val) in enumerate(health_items):
            card = QFrame()
            card.setStyleSheet(f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 4px;")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 11, 14, 11)

            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT3}; font-size: 11px; font-weight: 500; background: transparent; border: none;")
            card_layout.addWidget(lbl)
            card_layout.addStretch()

            val_lbl = QLabel(val)
            val_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
            card_layout.addWidget(val_lbl)

            self.health_widgets[key] = val_lbl
            health_grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(health_grid)
        layout.addStretch()

        return page

    def _make_alerts_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        
        hdr = QHBoxLayout()
        title = QLabel("Active Alerts")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;")
        hdr.addWidget(title)
        hdr.addStretch()

        clear_btn = QPushButton("Clear all")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT3};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 5px 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {RED}; border-color: {RED}40; }}
        """)
        clear_btn.clicked.connect(self._clear_all_alerts)
        hdr.addWidget(clear_btn)
        layout.addLayout(hdr)

        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")

        self.alerts_container = QWidget()
        self.alerts_layout = QVBoxLayout(self.alerts_container)
        self.alerts_layout.setSpacing(10)
        self.alerts_layout.addStretch()

        self.no_alerts_lbl = QLabel("✅  No active alerts. System is healthy.")
        self.no_alerts_lbl.setStyleSheet(f"color: {GREEN}; font-size: 14px;")
        self.no_alerts_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alerts_layout.insertWidget(0, self.no_alerts_lbl)

        scroll.setWidget(self.alerts_container)
        layout.addWidget(scroll)
        return page

    def _make_catalog_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel(f"Error Catalog  ({len(CATALOG_LIST)} errors monitored)")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["#", "Error Name", "Category", "Severity", "Detection"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 40)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setRowCount(len(CATALOG_LIST))

        for row, err in enumerate(CATALOG_LIST):
            sev = err.get("severity", "HIGH")
            color = SEV_COLORS.get(sev, ORANGE)
            icon = SEV_ICONS.get(sev, "⚠️")
            det = err.get("detection", {})
            det_str = det.get("type", "") + (f": {det.get('service_name','')}" if det.get('service_name') else
                                              f" ID {det.get('event_ids','')}" if det.get('event_ids') else "")

            items = [
                QTableWidgetItem(str(row + 1)),
                QTableWidgetItem(err.get("name", "")),
                QTableWidgetItem(err.get("category", "")),
                QTableWidgetItem(f"{icon} {sev}"),
                QTableWidgetItem(det_str),
            ]
            items[3].setForeground(QColor(color))
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                table.setItem(row, col, item)

        layout.addWidget(table)
        return page

    def _make_demo_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(16)

        title = QLabel("Demo Mode")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 26px; font-weight: 700; letter-spacing: -0.5px;")
        outer.addWidget(title)

        subtitle = QLabel(
            "Select a scenario to simulate a real Windows error. "
            "SmartFix detects it in seconds and shows the alert. "
            "Click \u2018Fix Now\u2019 to apply the real repair."
        )
        subtitle.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        warn = QFrame()
        warn.setStyleSheet(f"background: {ORANGE}18; border: 1px solid {ORANGE}60; border-radius: 8px;")
        warn_layout = QHBoxLayout(warn)
        warn_layout.setContentsMargins(16, 10, 16, 10)
        warn_icon = QLabel("\u26a0")
        warn_icon.setStyleSheet(f"color: {ORANGE}; font-size: 16px; background: transparent; border: none;")
        warn_layout.addWidget(warn_icon)
        warn_lbl = QLabel("Demo scenarios temporarily stop real Windows services. They are fully reversed by the repair. Requires Administrator.")
        warn_lbl.setStyleSheet(f"color: {ORANGE}; font-size: 11px; background: transparent; border: none;")
        warn_lbl.setWordWrap(True)
        warn_layout.addWidget(warn_lbl, 1)
        outer.addWidget(warn)

        # Scrollable card list — fully responsive at any window size
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        cards_widget = QWidget()
        cards_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(cards_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        for sc in DEMO_LIST:
            self._make_demo_card(layout, sc)

        layout.addStretch()
        scroll.setWidget(cards_widget)
        outer.addWidget(scroll)
        return page

    def _make_demo_card(self, parent_layout, sc):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {ACCENT};
            }}
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(20, 14, 16, 14)

        
        col = QVBoxLayout()
        col.setSpacing(3)
        name_lbl = QLabel(sc.name)
        name_lbl.setStyleSheet(f"color: {TEXT1}; font-weight: bold; font-size: 13px; background: transparent; border: none;")
        col.addWidget(name_lbl)
        desc_lbl = QLabel(sc.description)
        desc_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 11px; background: transparent; border: none;")
        col.addWidget(desc_lbl)

        err = ERROR_CATALOG.get(sc.error_id, {})
        sev = err.get("severity", "HIGH")
        color = SEV_COLORS.get(sev, ORANGE)
        badge = QLabel(f" {sev} ")
        badge.setStyleSheet(f"background: {color}; color: white; border-radius: 4px; font-size: 9px; font-weight: bold; padding: 2px 6px; border: none;")
        badge_row = QHBoxLayout()
        badge_row.addWidget(badge)
        badge_row.addStretch()
        col.addLayout(badge_row)
        row.addLayout(col, 1)

        
        trigger_btn = QPushButton("▶  Trigger Demo")
        trigger_btn.setFixedWidth(150)
        trigger_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: #3D7ADB; }}
            QPushButton:pressed {{ background: #2A5FBD; }}
        """)
        trigger_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        trigger_btn.clicked.connect(lambda checked, sid=sc.error_id, btn=trigger_btn: self._run_demo(sid, btn))
        row.addWidget(trigger_btn)

        parent_layout.addWidget(card)

    

    
    def _make_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        
        title_row = QHBoxLayout()
        title = QLabel("Repair History")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 22px; font-weight: bold;")
        title_row.addWidget(title)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(f"background: {BG_CARD2}; color: {TEXT1}; padding: 6px 16px; border-radius: 6px; border: 1px solid {BORDER};")
        refresh_btn.clicked.connect(lambda: self._populate_history())
        title_row.addWidget(refresh_btn)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Error Name", "Category", "Action", "Success"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setColumnWidth(0, 140)
        self.history_table.setColumnWidth(1, 280)
        self.history_table.setColumnWidth(2, 120)
        self.history_table.setColumnWidth(3, 100)
        layout.addWidget(self.history_table)
        
        self._populate_history()
        return page

    def _populate_history(self):
        if not hasattr(self, 'history_table'): return
        try:
            records = get_history(50)
            self.history_table.setRowCount(len(records))
            for i, r in enumerate(records):
                ts = str(r.get('timestamp', ''))[:19].replace('T', ' ')
                self.history_table.setItem(i, 0, QTableWidgetItem(ts))
                self.history_table.setItem(i, 1, QTableWidgetItem(r.get('error_name', '')))
                self.history_table.setItem(i, 2, QTableWidgetItem(r.get('category', '')))
                
                action = r.get('action', '')
                act_item = QTableWidgetItem(action)
                if action == 'REPAIRED': act_item.setForeground(QColor(GREEN))
                elif action == 'DETECTED': act_item.setForeground(QColor(ORANGE))
                self.history_table.setItem(i, 3, act_item)
                
                succ = r.get('success', '')
                succ_str = ""
                if action == 'REPAIRED':
                    succ_str = "Yes" if succ else "No"
                succ_item = QTableWidgetItem(succ_str)
                if succ == 1: succ_item.setForeground(QColor(GREEN))
                elif succ == 0 and action == 'REPAIRED': succ_item.setForeground(QColor(RED))
                self.history_table.setItem(i, 4, succ_item)
        except Exception as e:
            logger.error(f"History load failed: {e}")

    def _make_network_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        
        title = QLabel("Network Diagnostics")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("Run a full network stack diagnosis including DNS, Gateway, Ports, and Internet connectivity.")
        desc.setStyleSheet(f"color: {TEXT2}; font-size: 13px;")
        layout.addWidget(desc)
        
        self.net_btn = QPushButton("Run Network Diagnostics")
        self.net_btn.setStyleSheet(f"background: {ACCENT}; color: white; padding: 12px 24px; font-weight: bold; font-size: 14px; border-radius: 8px; border: none; margin-top: 10px; width: 250px;")
        self.net_btn.setFixedWidth(250)
        self.net_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.net_btn.clicked.connect(self._run_network_diag)
        layout.addWidget(self.net_btn)
        
        self.net_log = QTextEdit()
        self.net_log.setReadOnly(True)
        self.net_log.setPlaceholderText("Click 'Run Network Diagnostics' to start...")
        layout.addWidget(self.net_log)
        
        return page

    def _run_network_diag(self):
        self.net_btn.setEnabled(False)
        self.net_btn.setText("Running...")
        self.net_log.clear()
        self.net_log.append("Running diagnostics... This may take up to 30 seconds.")
        
        
        def runner():
            try:
                res = run_full_diagnostics()
                self._alert_signal.emit({"type": "net_done", "res": res})
            except Exception as e:
                self._alert_signal.emit({"type": "net_err", "err": str(e)})
        threading.Thread(target=runner, daemon=True).start()


    # ─────────────────────────────────────────────────────────────────────────
    # LAB MONITOR PAGE
    # ─────────────────────────────────────────────────────────────────────────

    def _make_lab_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── Header ───────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("🖥  Lab Monitor")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 22px; font-weight: bold;")
        hdr.addWidget(title)
        hdr.addStretch()

        # Switch role button (allows switching between Admin and Client anytime)
        self._lab_switch_role_btn = QPushButton("⇄ Switch Role")
        self._lab_switch_role_btn.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT1}; border: 1px solid {BORDER}; "
            f"border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 500;"
        )
        self._lab_switch_role_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lab_switch_role_btn.setToolTip("Switch this PC between Admin and Client mode")
        self._lab_switch_role_btn.clicked.connect(self._lab_switch_role_dialog)
        hdr.addWidget(self._lab_switch_role_btn)

        # Passkey settings button
        self._lab_passkey_btn = QPushButton("🔑 Passkey")
        self._lab_passkey_btn.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT2}; border: 1px solid {BORDER}; "
            f"border-radius: 6px; padding: 5px 12px; font-size: 12px;"
        )
        self._lab_passkey_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lab_passkey_btn.setToolTip("Manage Admin Authentication Passkey")
        self._lab_passkey_btn.clicked.connect(self._lab_change_passkey_dialog)
        hdr.addWidget(self._lab_passkey_btn)

        # Mode badge
        self._lab_mode_badge = QLabel("Mode: unset")
        self._lab_mode_badge.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT3}; border: 1px solid {BORDER}; "
            f"border-radius: 6px; padding: 4px 12px; font-size: 11px;"
        )
        hdr.addWidget(self._lab_mode_badge)
        layout.addLayout(hdr)

        # ── Mode setup card ───────────────────────────────────────────────────
        self._lab_setup_card = QFrame()
        self._lab_setup_card.setStyleSheet(
            f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 10px;"
        )
        setup_layout = QVBoxLayout(self._lab_setup_card)
        setup_layout.setContentsMargins(24, 20, 24, 20)
        setup_layout.setSpacing(12)

        setup_title = QLabel("Set Up This PC")
        setup_title.setStyleSheet(f"color: {TEXT1}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        setup_layout.addWidget(setup_title)

        setup_desc = QLabel(
            "Choose a role for this PC. Any computer in the lab can become the Admin (Central Controller) "
            "with the Admin Passkey, or a Client (Managed Workstation). Roles can be switched at any time."
        )
        setup_desc.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: transparent; border: none;")
        setup_desc.setWordWrap(True)
        setup_layout.addWidget(setup_desc)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._btn_admin_mode = QPushButton("🛡  Set as Admin (Central Controller)")
        self._btn_admin_mode.setStyleSheet(
            f"background: {ACCENT}; color: white; padding: 10px 20px; border: none; "
            f"border-radius: 8px; font-weight: bold; font-size: 13px;"
        )
        self._btn_admin_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_admin_mode.clicked.connect(lambda: self._lab_set_admin_mode(skip_auth=False))
        btn_row.addWidget(self._btn_admin_mode)

        self._btn_client_mode = QPushButton("💻  Set as Client (Managed Workstation)")
        self._btn_client_mode.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT1}; padding: 10px 20px; border: 1px solid {BORDER}; "
            f"border-radius: 8px; font-weight: bold; font-size: 13px;"
        )
        self._btn_client_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_client_mode.clicked.connect(lambda: self._lab_set_client_mode(prompt_seat=True))
        btn_row.addWidget(self._btn_client_mode)
        btn_row.addStretch()
        setup_layout.addLayout(btn_row)
        layout.addWidget(self._lab_setup_card)

        # ── Admin dashboard (hidden by default) ───────────────────────────────
        self._lab_admin_panel = QWidget()
        admin_v = QVBoxLayout(self._lab_admin_panel)
        admin_v.setContentsMargins(0, 0, 0, 0)
        admin_v.setSpacing(12)

        admin_bar = QHBoxLayout()
        self._lab_client_count_lbl = QLabel("0 PCs online")
        self._lab_client_count_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 13px;")
        admin_bar.addWidget(self._lab_client_count_lbl)
        admin_bar.addStretch()

        demote_btn = QPushButton("💻 Switch this PC to Client")
        demote_btn.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT1}; padding: 6px 14px; border: 1px solid {BORDER}; "
            f"border-radius: 6px; font-size: 12px;"
        )
        demote_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def _demote_to_client():
            if not self._lab_prompt_admin_auth():
                return
            self._lab_set_client_mode(prompt_seat=True)
        demote_btn.clicked.connect(_demote_to_client)
        admin_bar.addWidget(demote_btn)

        add_btn = QPushButton("+ Add PC manually")
        add_btn.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT1}; padding: 6px 14px; border: 1px solid {BORDER}; "
            f"border-radius: 6px; font-size: 12px;"
        )
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._lab_add_client_dialog)
        admin_bar.addWidget(add_btn)
        admin_v.addLayout(admin_bar)

        # Scroll area for PC cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._lab_cards_widget = QWidget()
        self._lab_cards_widget.setStyleSheet("background: transparent;")
        self._lab_cards_layout = QVBoxLayout(self._lab_cards_widget)
        self._lab_cards_layout.setSpacing(8)
        self._lab_cards_layout.addStretch()
        scroll.setWidget(self._lab_cards_widget)
        admin_v.addWidget(scroll)
        self._lab_admin_panel.setVisible(False)
        layout.addWidget(self._lab_admin_panel)

        # ── Client status card (hidden by default) ────────────────────────────
        self._lab_client_panel = QWidget()
        cp_v = QVBoxLayout(self._lab_client_panel)
        cp_v.setContentsMargins(0, 0, 0, 0)
        cp_v.setSpacing(10)

        self._lab_client_status = QFrame()
        self._lab_client_status.setStyleSheet(
            f"background: {BG_CARD}; border: 1px solid {GREEN}60; border-radius: 10px;"
        )
        csl = QVBoxLayout(self._lab_client_status)
        csl.setContentsMargins(24, 18, 24, 18)
        csl.setSpacing(8)
        self._lab_client_seat_lbl = QLabel("Seat: —")
        self._lab_client_seat_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        csl.addWidget(self._lab_client_seat_lbl)
        self._lab_client_ip_lbl = QLabel("IP: —")
        self._lab_client_ip_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: transparent; border: none;")
        csl.addWidget(self._lab_client_ip_lbl)
        self._lab_client_agent_lbl = QLabel("Agent: starting…")
        self._lab_client_agent_lbl.setStyleSheet(f"color: {GREEN}; font-size: 12px; background: transparent; border: none;")
        csl.addWidget(self._lab_client_agent_lbl)

        # Client action buttons (Promote to Admin & Rename)
        client_act_row = QHBoxLayout()
        client_act_row.setSpacing(10)

        promote_btn = QPushButton("🛡 Promote this PC to Admin")
        promote_btn.setStyleSheet(
            f"background: {ACCENT}; color: white; padding: 7px 16px; border: none; "
            f"border-radius: 6px; font-weight: bold; font-size: 12px;"
        )
        promote_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        promote_btn.setToolTip("Authenticate and promote this machine to Central Controller")
        promote_btn.clicked.connect(lambda: self._lab_set_admin_mode(skip_auth=False))
        client_act_row.addWidget(promote_btn)

        rename_seat_btn = QPushButton("✏ Rename Seat")
        rename_seat_btn.setStyleSheet(
            f"background: {BG_CARD2}; color: {TEXT1}; padding: 7px 14px; border: 1px solid {BORDER}; "
            f"border-radius: 6px; font-size: 12px;"
        )
        rename_seat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_seat_btn.setToolTip("Change the workstation name broadcast to Admin")
        rename_seat_btn.clicked.connect(self._lab_rename_seat_dialog)
        client_act_row.addWidget(rename_seat_btn)

        client_act_row.addStretch()
        csl.addLayout(client_act_row)

        cp_v.addWidget(self._lab_client_status)
        self._lab_client_panel.setVisible(False)
        layout.addWidget(self._lab_client_panel)

        layout.addStretch()
        return page

    def _lab_prompt_admin_auth(self) -> bool:
        """Prompt for admin passkey before allowing switch to Admin role."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Admin Authentication")
        dlg.setFixedWidth(400)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}
            QLabel {{ color: {TEXT1}; background: transparent; }}
            QLineEdit {{
                background: {BG_MAIN}; color: {TEXT1}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 8px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(14)

        icon_lbl = QLabel("🛡  Admin Authentication Required")
        icon_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-weight: bold;")
        v.addWidget(icon_lbl)

        info_lbl = QLabel("Enter the Lab Admin passkey to authorize this PC as Central Controller.")
        info_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        info_lbl.setWordWrap(True)
        v.addWidget(info_lbl)

        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_edit.setPlaceholderText("Enter admin passkey…")
        v.addWidget(pwd_edit)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {RED}; font-size: 11px;")
        err_lbl.setVisible(False)
        v.addWidget(err_lbl)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"background: {BG_CARD2}; color: {TEXT2}; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 16px; font-size: 12px;")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(dlg.reject)
        btns.addWidget(cancel_btn)

        submit_btn = QPushButton("Authorize Admin")
        submit_btn.setStyleSheet(f"background: {ACCENT}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; font-size: 12px;")
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        def try_auth():
            val = pwd_edit.text()
            if verify_admin_passkey(val):
                dlg.accept()
            else:
                err_lbl.setText("⚠ Incorrect passkey. Access denied.")
                err_lbl.setVisible(True)
                pwd_edit.selectAll()
                pwd_edit.setFocus()

        submit_btn.clicked.connect(try_auth)
        pwd_edit.returnPressed.connect(try_auth)
        btns.addWidget(submit_btn)
        v.addLayout(btns)

        res = dlg.exec()
        return res == QDialog.DialogCode.Accepted

    def _lab_change_passkey_dialog(self):
        """Allow changing the lab admin passkey."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Manage Admin Passkey")
        dlg.setFixedWidth(400)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 12px; }}
            QLabel {{ color: {TEXT1}; background: transparent; }}
            QLineEdit {{
                background: {BG_MAIN}; color: {TEXT1}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 8px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(10)

        icon_lbl = QLabel("🔑  Lab Admin Passkey")
        icon_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-weight: bold;")
        v.addWidget(icon_lbl)

        info_lbl = QLabel("Update the passkey used to grant Admin permissions and authenticate remote commands across the lab.")
        info_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        info_lbl.setWordWrap(True)
        v.addWidget(info_lbl)

        v.addWidget(QLabel("Current Passkey:"))
        curr_edit = QLineEdit()
        curr_edit.setEchoMode(QLineEdit.EchoMode.Password)
        curr_edit.setPlaceholderText("Enter current admin passkey")
        v.addWidget(curr_edit)

        v.addWidget(QLabel("New Passkey:"))
        new_edit = QLineEdit()
        new_edit.setEchoMode(QLineEdit.EchoMode.Password)
        new_edit.setPlaceholderText("At least 4 characters")
        v.addWidget(new_edit)

        v.addWidget(QLabel("Confirm New Passkey:"))
        conf_edit = QLineEdit()
        conf_edit.setEchoMode(QLineEdit.EchoMode.Password)
        conf_edit.setPlaceholderText("Re-type new passkey")
        v.addWidget(conf_edit)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet(f"color: {RED}; font-size: 11px;")
        err_lbl.setVisible(False)
        v.addWidget(err_lbl)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"background: {BG_CARD2}; color: {TEXT2}; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 16px; font-size: 12px;")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(dlg.reject)
        btns.addWidget(cancel_btn)

        save_btn = QPushButton("Save Passkey")
        save_btn.setStyleSheet(f"background: {ACCENT}; color: white; border: none; border-radius: 6px; padding: 8px 18px; font-weight: bold; font-size: 12px;")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        def try_save():
            curr = curr_edit.text()
            newp = new_edit.text().strip()
            conf = conf_edit.text().strip()

            if not verify_admin_passkey(curr):
                err_lbl.setText("⚠ Current passkey is incorrect.")
                err_lbl.setVisible(True)
                curr_edit.selectAll()
                curr_edit.setFocus()
                return

            if len(newp) < 4:
                err_lbl.setText("⚠ New passkey must be at least 4 characters.")
                err_lbl.setVisible(True)
                new_edit.setFocus()
                return

            if newp != conf:
                err_lbl.setText("⚠ New passkeys do not match.")
                err_lbl.setVisible(True)
                conf_edit.selectAll()
                conf_edit.setFocus()
                return

            set_admin_passkey(newp)
            dlg.accept()

        save_btn.clicked.connect(try_save)
        btns.addWidget(save_btn)
        v.addLayout(btns)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Passkey Updated", "Admin passkey has been successfully updated!")

    def _lab_switch_role_dialog(self):
        """Allow switching between Admin and Client roles with password authorization."""
        if not self._lab_prompt_admin_auth():
            return
        current = self._lab_mode
        if current == "admin":
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Switch to Client Mode",
                "Switch this PC from Admin Controller to a Managed Client Workstation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._lab_set_client_mode(prompt_seat=True)
        else:
            self._lab_set_admin_mode(skip_auth=True)

    def _lab_rename_seat_dialog(self):
        """Allow renaming this client workstation's seat name (requires admin authorization)."""
        if not self._lab_prompt_admin_auth():
            return
        from PyQt6.QtWidgets import QInputDialog
        import socket
        curr = get_seat_name() or f"PC-{socket.gethostname()}"
        name, ok = QInputDialog.getText(
            self, "Rename Unique Seat",
            "Enter a unique seat name for this client PC:",
            text=curr
        )
        if ok and name.strip():
            new_seat = name.strip()
            set_seat_name(new_seat)
            self._lab_client_seat_lbl.setText(f"Seat: {new_seat}")
            if self._lab_agent:
                self._lab_agent.seat = new_seat

    def _lab_set_admin_mode(self, skip_auth: bool = False):
        """Configure this PC as Admin (with authentication) and (re)start the admin manager."""
        if not skip_auth:
            if not self._lab_prompt_admin_auth():
                return

        # If currently running client agent, stop it cleanly first
        if self._lab_agent:
            try:
                self._lab_agent.stop()
            except Exception as e:
                logger.warning(f"Error stopping lab agent: {e}")
            self._lab_agent = None

        set_mode("admin")
        self._lab_mode = "admin"
        self._lab_setup_card.setVisible(False)
        self._lab_admin_panel.setVisible(True)
        self._lab_client_panel.setVisible(False)
        self._lab_mode_badge.setText("Mode: Admin")
        self._lab_mode_badge.setStyleSheet(
            f"background: {ACCENT}30; color: {ACCENT}; border: 1px solid {ACCENT}60; "
            f"border-radius: 6px; padding: 4px 12px; font-size: 11px;"
        )
        self._ensure_lab_admin()

    def _lab_set_client_mode(self, prompt_seat: bool = True):
        """Configure this PC as a client workstation and (re)start client agent."""
        import socket
        current = get_seat_name() or ""
        if prompt_seat or not current:
            from PyQt6.QtWidgets import QInputDialog
            default_name = current or f"PC-{socket.gethostname()}"
            name, ok = QInputDialog.getText(
                self, "Set Unique Seat Name",
                "Enter a unique seat name for this client PC (e.g. PC-01):",
                text=default_name
            )
            if not ok or not name.strip():
                return
            current = name.strip()
            set_seat_name(current)

        # If currently running admin manager, stop it cleanly first
        if self._lab_admin:
            try:
                self._lab_admin.stop()
            except Exception as e:
                logger.warning(f"Error stopping lab admin: {e}")
            self._lab_admin = None

        set_mode("client")
        self._lab_mode = "client"
        self._lab_setup_card.setVisible(False)
        self._lab_admin_panel.setVisible(False)
        self._lab_client_panel.setVisible(True)
        self._lab_mode_badge.setText("Mode: Client")
        self._lab_mode_badge.setStyleSheet(
            f"background: {GREEN}20; color: {GREEN}; border: 1px solid {GREEN}50; "
            f"border-radius: 6px; padding: 4px 12px; font-size: 11px;"
        )
        self._lab_client_seat_lbl.setText(f"Seat: {current}")
        self._lab_client_ip_lbl.setText(f"IP: {get_local_ip()}  |  Port: {LAB_PORT}")
        self._ensure_lab_agent()

    def _ensure_lab_agent(self):
        """Start the client agent if not already running."""
        if self._lab_agent is None:
            self._lab_agent = LabClientAgent()
            self._lab_agent.start()
        self._lab_client_agent_lbl.setText("Agent: running — broadcasting presence on LAN")

    def _ensure_lab_admin(self):
        """Start the admin manager if not already running."""
        if self._lab_admin is None:
            self._lab_admin = LabAdminManager(
                on_update=lambda clients: self._alert_signal.emit(
                    {"__type__": "lab_update", "clients": clients}
                )
            )
            self._lab_admin.start()

    def _lab_add_client_dialog(self):
        """Allow admin to manually register a client PC by seat + IP (requires admin authorization)."""
        if not self._lab_prompt_admin_auth():
            return
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Client PC to Network")
        dlg.setStyleSheet(self.styleSheet())
        form = QFormLayout(dlg)
        seat_edit = QLineEdit()
        seat_edit.setPlaceholderText("e.g. PC-01 (unique seat name)")
        ip_edit = QLineEdit()
        ip_edit.setPlaceholderText("e.g. 192.168.1.50")
        form.addRow("Unique Seat name:", seat_edit)
        form.addRow("Client IP address:", ip_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() and seat_edit.text().strip() and ip_edit.text().strip():
            if self._lab_admin:
                self._lab_admin.add_client_manual(seat_edit.text().strip(), ip_edit.text().strip())

    def _lab_update_admin_ui(self, clients: list):
        """Rebuild the admin PC cards grid. Called on main thread via signal."""
        # Clear existing cards (leave the stretch)
        while self._lab_cards_layout.count() > 1:
            item = self._lab_cards_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)

        online = sum(1 for c in clients if c.online)
        self._lab_client_count_lbl.setText(
            f"{online} online / {len(clients)} total"
        )

        for client in sorted(clients, key=lambda c: c.seat):
            card = self._make_lab_client_card(client)
            self._lab_cards_layout.insertWidget(
                self._lab_cards_layout.count() - 1, card
            )

    def _make_lab_client_card(self, client: ClientInfo) -> QFrame:
        """Create a card widget for one client PC."""
        online = client.online
        status_color = GREEN if online else TEXT3
        border_col   = f"{GREEN}50" if online else BORDER
        err_count    = client.error_count

        card = QFrame()
        card.setStyleSheet(
            f"background: {BG_CARD}; border: 1px solid {border_col}; border-radius: 10px;"
        )
        row = QHBoxLayout(card)
        row.setContentsMargins(16, 12, 14, 12)
        row.setSpacing(12)

        # Status dot
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background: {status_color}; border-radius: 5px; border: none;")
        row.addWidget(dot)

        # Seat + IP
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        seat_lbl = QLabel(client.seat)
        seat_lbl.setStyleSheet(f"color: {TEXT1}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        info_col.addWidget(seat_lbl)
        ip_lbl = QLabel(client.ip if online else "Offline")
        ip_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 11px; background: transparent; border: none;")
        info_col.addWidget(ip_lbl)
        row.addLayout(info_col)
        row.addStretch()

        # Metrics pills
        if online and client.metrics:
            m = client.metrics
            def pill(label, val, warn=70, crit=90):
                col = RED if val >= crit else ORANGE if val >= warn else GREEN
                lbl = QLabel(f"{label} {val:.0f}%")
                lbl.setStyleSheet(
                    f"background: {col}20; color: {col}; border: 1px solid {col}40; "
                    f"border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: bold;"
                )
                return lbl
            for lbl in [
                pill("CPU",  m.get("cpu_percent", 0)),
                pill("RAM",  m.get("memory_percent", 0)),
                pill("Disk", m.get("disk_percent", 0)),
            ]:
                row.addWidget(lbl)

        # Error count badge
        if err_count > 0:
            err_badge = QLabel(f"⚠ {err_count} error{'s' if err_count != 1 else ''}")
            err_badge.setStyleSheet(
                f"background: {RED}20; color: {RED}; border: 1px solid {RED}40; "
                f"border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: bold;"
            )
            row.addWidget(err_badge)
        elif online:
            ok_badge = QLabel("✓ Healthy")
            ok_badge.setStyleSheet(
                f"background: {GREEN}20; color: {GREEN}; border: 1px solid {GREEN}40; "
                f"border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: bold;"
            )
            row.addWidget(ok_badge)

        # Actions row
        if online:
            refresh_btn = QPushButton("↻")
            refresh_btn.setFixedSize(28, 28)
            refresh_btn.setToolTip("Refresh status now")
            refresh_btn.setStyleSheet(
                f"background: {BG_CARD2}; color: {TEXT1}; border: 1px solid {BORDER}; "
                f"border-radius: 6px; font-size: 14px;"
            )
            refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            refresh_btn.clicked.connect(
                lambda _, seat=client.seat: self._lab_admin.poll_client_now(seat) if self._lab_admin else None
            )
            row.addWidget(refresh_btn)

            view_btn = QPushButton(f"⚠ Fix Errors ({err_count})" if err_count > 0 else "🔧 Fix & Manage")
            btn_bg = f"{ORANGE}25" if err_count > 0 else BG_CARD2
            btn_col = ORANGE if err_count > 0 else TEXT1
            btn_border = f"{ORANGE}60" if err_count > 0 else BORDER
            view_btn.setStyleSheet(
                f"background: {btn_bg}; color: {btn_col}; border: 1px solid {btn_border}; "
                f"border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: bold;"
            )
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(
                lambda _, c=client: self._lab_show_errors_dialog(c)
            )
            row.addWidget(view_btn)

        return card

    def _lab_show_errors_dialog(self, client: ClientInfo):
        """Show a dialog listing errors on the client PC with remote-repair buttons and maintenance tools."""
        from PyQt6.QtWidgets import QDialog, QScrollArea, QComboBox
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Diagnostics & Remote Repair — {client.seat} ({client.ip})")
        dlg.setMinimumSize(640, 520)
        dlg.setStyleSheet(self.styleSheet())
        outer = QVBoxLayout(dlg)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(12)

        # Title and header
        title_row = QHBoxLayout()
        title = QLabel(f"🖥  {client.seat}  ·  Remote Error Management")
        title.setStyleSheet(f"color: {TEXT1}; font-size: 16px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        ip_tag = QLabel(f"IP: {client.ip}")
        ip_tag.setStyleSheet(f"color: {TEXT2}; font-size: 12px; background: {BG_CARD2}; border: 1px solid {BORDER}; border-radius: 4px; padding: 2px 8px;")
        title_row.addWidget(ip_tag)
        outer.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setSpacing(10)

        # Section 1: Active Detected Errors
        active_sec = QLabel(f"LIVE DETECTED ISSUES ({len(client.errors)})")
        active_sec.setStyleSheet(f"color: {ORANGE}; font-size: 10px; font-weight: bold; letter-spacing: 0.08em;")
        body_layout.addWidget(active_sec)

        if not client.errors:
            no_err_card = QFrame()
            no_err_card.setStyleSheet(f"background: {GREEN}15; border: 1px solid {GREEN}40; border-radius: 8px;")
            neh = QHBoxLayout(no_err_card)
            neh.setContentsMargins(14, 10, 14, 10)
            neh.addWidget(QLabel("✅ No active errors reported by this workstation. System is healthy."))
            body_layout.addWidget(no_err_card)
        else:
            # Fix all errors button
            fix_all_btn = QPushButton(f"🚀 Fix All {len(client.errors)} Errors on {client.seat}")
            fix_all_btn.setStyleSheet(f"background: {GREEN}; color: black; font-weight: bold; padding: 8px 16px; border-radius: 6px; border: none;")
            fix_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)

            def fix_all():
                for err in client.errors:
                    eid = err.get("repair_id") or err.get("id", "")
                    self._lab_remote_repair(client.seat, eid, fix_all_btn)
            fix_all_btn.clicked.connect(fix_all)
            body_layout.addWidget(fix_all_btn)

            for err in client.errors:
                eframe = QFrame()
                eframe.setStyleSheet(f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px;")
                erow = QHBoxLayout(eframe)
                erow.setContentsMargins(14, 10, 12, 10)
                erow.setSpacing(10)

                ecol = QVBoxLayout()
                ecol.setSpacing(2)
                ename = QLabel(err.get("name", err.get("id", "Unknown")))
                ename.setStyleSheet(f"color: {TEXT1}; font-weight: bold; font-size: 13px; background: transparent; border: none;")
                ecol.addWidget(ename)
                edesc = QLabel(err.get("description", ""))
                edesc.setStyleSheet(f"color: {TEXT2}; font-size: 11px; background: transparent; border: none;")
                edesc.setWordWrap(True)
                ecol.addWidget(edesc)
                erow.addLayout(ecol, 1)

                fix_btn = QPushButton("🔧 Fix Remotely")
                fix_btn.setStyleSheet(
                    f"background: {ACCENT}; color: white; border: none; border-radius: 6px; "
                    f"padding: 7px 14px; font-weight: bold; font-size: 11px;"
                )
                fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                fix_btn.clicked.connect(
                    lambda _, seat=client.seat, eid=err.get("repair_id", err.get("id", "")), btn=fix_btn:
                        self._lab_remote_repair(seat, eid, btn)
                )
                erow.addWidget(fix_btn)
                body_layout.addWidget(eframe)

        # Section 2: Quick Remote Fixes & Maintenance
        maint_sec = QLabel("ON-DEMAND REMOTE FIXES & CLEANUP")
        maint_sec.setStyleSheet(f"color: {TEXT3}; font-size: 10px; font-weight: bold; letter-spacing: 0.08em; margin-top: 10px;")
        body_layout.addWidget(maint_sec)

        maint_card = QFrame()
        maint_card.setStyleSheet(f"background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px;")
        maint_layout = QVBoxLayout(maint_card)
        maint_layout.setContentsMargins(14, 12, 14, 12)
        maint_layout.setSpacing(10)

        maint_desc = QLabel("Select an error repair to run directly on this client workstation:")
        maint_desc.setStyleSheet(f"color: {TEXT2}; font-size: 11px;")
        maint_layout.addWidget(maint_desc)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        repair_combo = QComboBox()
        repair_combo.setStyleSheet(f"""
            QComboBox {{
                background: {BG_MAIN}; color: {TEXT1}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 6px 12px; font-size: 12px; min-width: 320px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD}; color: {TEXT1}; selection-background-color: {ACCENT};
            }}
        """)
        common_repairs = [
            ("Purge Temporary Files & Cache Clutter", "purge_temp_cache_files"),
            ("Reset Network, Flush DNS & TCP Stack", "fix_network_dns"),
            ("Restart Windows Audio Service", "restart_audio_services"),
            ("Reset Windows Update Services", "restart_windows_update"),
            ("Restart Print Spooler Service", "restart_print_spooler"),
            ("Fix High CPU / Reset WMI Repository", "fix_wmi_high_cpu"),
            ("Clear VS Code Hung Processes & Lockfiles", "lab_fix_vscode_frozen"),
            ("Reset Display Topology (Fix Black Screen)", "lab_reset_display_mode"),
            ("Restore USB Storage Access & Permissions", "lab_fix_usb_storage"),
            ("Resync System Clock via NTP", "lab_resync_clock_ntp"),
            ("Unblock Task Manager, Regedit & CMD", "lab_unlock_taskmgr_cmd"),
            ("Run System File Checker (SFC Scan)", "fix_sfc_scan"),
        ]
        for name, rep_id in common_repairs:
            repair_combo.addItem(name, rep_id)
        action_row.addWidget(repair_combo, 1)

        apply_fix_btn = QPushButton("⚡ Apply Remote Fix")
        apply_fix_btn.setStyleSheet(f"background: {ACCENT}; color: white; font-weight: bold; padding: 7px 16px; border-radius: 6px; border: none; font-size: 12px;")
        apply_fix_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_fix_btn.clicked.connect(
            lambda _, seat=client.seat, combo=repair_combo, btn=apply_fix_btn:
                self._lab_remote_repair(seat, combo.currentData(), btn)
        )
        action_row.addWidget(apply_fix_btn)
        maint_layout.addLayout(action_row)
        body_layout.addWidget(maint_card)

        body_layout.addStretch()
        scroll.setWidget(body)
        outer.addWidget(scroll)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"background: {BG_CARD2}; color: {TEXT1}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 18px;")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dlg.accept)
        outer.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        dlg.exec()

    def _lab_remote_repair(self, seat: str, error_id: str, btn: QPushButton):
        """Send a remote repair command to a client PC."""
        if not self._lab_admin:
            return
        btn.setText("Sending…")
        btn.setEnabled(False)

        def on_result(result):
            success = result.get("success", False)
            msg     = result.get("message", "")
            btn.setText("Sent ✓")
            btn.setEnabled(True)
            self._alert_signal.emit({
                "__type__": "lab_repair_result",
                "seat": seat,
                "error_id": error_id,
                "success": success,
                "message": msg,
                "btn_ref": id(btn),
            })
            if self._lab_admin:
                self._lab_admin.poll_client_now(seat)

        self._lab_admin.request_repair(seat, error_id, on_result=on_result)

    def _start_lab_services(self):
        """On startup, auto-resume whichever mode was previously set."""
        mode = get_mode()
        self._lab_mode = mode
        if mode == "admin":
            self._lab_set_admin_mode(skip_auth=True)
        elif mode == "client":
            seat = get_seat_name()
            if seat:
                self._lab_set_client_mode(prompt_seat=False)

    def _setup_tray(self):
        try:
            
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(0, 210, 106)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, 28, 28)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "SF")
            painter.end()

            self.tray = QSystemTrayIcon(QIcon(pixmap), self)
            self.tray.setToolTip("SmartFix AI — Monitoring Active ✓")

            tray_menu = QMenu()
            tray_menu.setStyleSheet(f"""
                QMenu {{
                    background: {BG_CARD};
                    border: 1px solid {BORDER};
                    color: {TEXT1};
                    font-size: 12px;
                    border-radius: 8px;
                }}
                QMenu::item:selected {{ background: {BG_CARD2}; }}
                QMenu::separator {{ background: {BORDER}; height: 1px; margin: 4px 0; }}
            """)

            show_action = QAction("📊 Open Dashboard", self)
            show_action.triggered.connect(self.show_and_raise)
            tray_menu.addAction(show_action)

            demo_action = QAction("🎭 Demo Mode", self)
            demo_action.triggered.connect(lambda: self._nav(3, self._nav_btns[3]))
            tray_menu.addAction(demo_action)

            tray_menu.addSeparator()

            exit_action = QAction("❌ Exit SmartFix", self)
            exit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(exit_action)

            self.tray.setContextMenu(tray_menu)
            self.tray.activated.connect(self._tray_activated)
            self.tray.show()
            if getattr(self, "is_background", False):
                self.tray.showMessage(
                    "SmartFix AI",
                    "SmartFix AI is active and monitoring in the background.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
        except Exception as e:
            logger.error(f"Tray setup failed: {e}")

    def _tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            if self.isVisible() and not self.isMinimized():
                self.show_and_raise()
            else:
                self.show_and_raise()

    def show_and_raise(self):
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        try:
            import ctypes
            hwnd = int(self.winId())
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

    

    def _start_monitor(self):
        self._monitor = BackgroundMonitor(
            on_alert=lambda info: self._alert_signal.emit(info),
            check_interval=30,
        )
        self._monitor.start()
        self._demo = DemoController(
            on_inject_error=self._monitor.inject_demo_error
        )
        self._start_time = time.time()

    def _start_metric_timer(self):
        """Start dedicated Task-Manager-like real-time metric sampling thread."""
        self._metric_worker = MetricWorkerThread(self)
        self._metric_worker.metrics_ready.connect(self._show_alert)
        self._metric_worker.start()

    

    def _show_alert(self, error_info: dict):
        """Called on main thread via signal."""

        # ── Metric update from background thread ───────────────────
        if error_info.get("__type__") == "metric_update":
            def color_val(val, warn=75, crit=90):
                if val >= crit: return RED
                if val >= warn: return ORANGE
                return GREEN

            cpu = error_info.get("cpu", 0)
            cores = error_info.get("cores", 1)
            ram_pct = error_info.get("ram_pct", 0)
            ram_used = error_info.get("ram_used_gb", 0)
            ram_total = error_info.get("ram_total_gb", 0)
            disk_pct = error_info.get("disk_pct", 0)
            disk_free = error_info.get("disk_free_gb", 0)
            svcs_running = error_info.get("svcs_running", 0)
            svcs_total = error_info.get("svcs_total", 5)
            net_ok = error_info.get("net_ok", True)
            uptime_str = error_info.get("uptime_str", "0m")

            # CPU
            self.health_widgets["cpu"].setText(f"{cpu:.1f}%  ({cores} cores)")
            self.health_widgets["cpu"].setStyleSheet(
                f"color: {color_val(cpu)}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

            # Memory
            self.health_widgets["ram"].setText(f"{ram_pct:.1f}%  ({ram_used:.1f} / {ram_total:.1f} GB)")
            self.health_widgets["ram"].setStyleSheet(
                f"color: {color_val(ram_pct)}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

            # Disk
            self.health_widgets["disk"].setText(f"{disk_pct:.1f}%  ({disk_free:.1f} GB free)")
            self.health_widgets["disk"].setStyleSheet(
                f"color: {color_val(disk_pct)}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

            # Network
            net_txt = "Online (Connected)" if net_ok else "No Internet"
            net_col = GREEN if net_ok else RED
            self.health_widgets["net"].setText(net_txt)
            self.health_widgets["net"].setStyleSheet(
                f"color: {net_col}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

            # Critical Services
            if svcs_running == svcs_total:
                svc_txt = f"All {svcs_total} Running (Healthy)"
                svc_col = GREEN
            else:
                svc_txt = f"{svcs_running}/{svcs_total} Running (Degraded)"
                svc_col = ORANGE
            self.health_widgets["svc"].setText(svc_txt)
            self.health_widgets["svc"].setStyleSheet(
                f"color: {svc_col}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

            self.card_uptime.set_value(uptime_str)
            self.card_monitored.set_value(str(len(CATALOG_LIST)))
            self.last_scan_lbl.setText(f"● Live · {datetime.now().strftime('%H:%M:%S')}")
            self.last_scan_lbl.setStyleSheet(f"color: {GREEN}; font-size: 11px; font-weight: 600; background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 6px; padding: 4px 12px;")
            return

        # ── Lab Monitor signals ───────────────────────────────────────────────
        if error_info.get("__type__") == "lab_update":
            clients = error_info.get("clients", [])
            self._lab_update_admin_ui(clients)
            # Also feed fresh metrics to the local agent if in client mode
            if self._lab_mode == "client" and self._lab_agent:
                metrics = {
                    "cpu_percent":    error_info.get("cpu", 0),
                    "memory_percent": error_info.get("ram", 0),
                    "disk_percent":   error_info.get("disk", 0),
                }
                self._lab_agent.update_metrics(metrics)
            return

        if error_info.get("__type__") == "lab_repair_result":
            seat    = error_info.get("seat", "")
            success = error_info.get("success", False)
            message = error_info.get("message", "")
            from PyQt6.QtWidgets import QMessageBox
            if success:
                QMessageBox.information(
                    self, f"Repair on {seat}",
                    f"✅ Repair succeeded on {seat}:\n{message}"
                )
            else:
                QMessageBox.warning(
                    self, f"Repair on {seat}",
                    f"❌ Repair failed on {seat}:\n{message}"
                )
            return

        sig_type = error_info.get("type")

        if sig_type == "net_done":

            res = error_info.get("res", {})
            self.net_btn.setText("Run Network Diagnostics")
            self.net_btn.setEnabled(True)
            self.net_log.clear()
            self.net_log.append(f"Network Diagnostics Complete:\n")
            import json
            self.net_log.append(json.dumps(res, indent=2))
            return
            
        if sig_type == "net_err":
            self.net_btn.setText("Run Network Diagnostics")
            self.net_btn.setEnabled(True)
            self.net_log.append(f"\nError: {error_info.get('err')}")
            return

        self._alert_count += 1
        self._alerts.append(error_info)
        self.card_alerts.set_value(str(self._alert_count))
        self.health_widgets["errors"].setText(f"{self._alert_count} alert(s)")
        self.health_widgets["errors"].setStyleSheet(f"color: {RED}; font-size: 13px; font-weight: 600; background: transparent; border: none;")
        log_detection(error_info)

        # Feed error to lab agent if running in client mode
        if self._lab_mode == "client" and self._lab_agent:
            self._lab_agent.update_errors(list(self._alerts))

        eid = error_info.get("id", "")
        sev = error_info.get("severity", "")
        is_demo = error_info.get("is_demo", False) or eid in DEMO_SCENARIOS

        # If it is a demo, allow it to re-trigger even if previously in active alerts
        if is_demo and eid in self._active_alert_ids:
            for i in range(self.alerts_layout.count()):
                w = self.alerts_layout.itemAt(i).widget()
                if w and hasattr(w, "error_info") and w.error_info.get("id") == eid:
                    w.setParent(None)
                    break
            self._active_alert_ids.discard(eid)
            self._alert_count = max(0, self._alert_count - 1)
        elif eid in self._active_alert_ids:
            self._alert_count = max(0, self._alert_count - 1)
            self.card_alerts.set_value(str(self._alert_count))
            return

        if eid:
            self._active_alert_ids.add(eid)

        self.no_alerts_lbl.setVisible(False)
        alert_item = AlertItem(error_info, self._fix_from_list, self._ignore_from_list)
        self.alerts_layout.insertWidget(0, alert_item)

        # Show popup toast for CRITICAL, HIGH severity or DEMO scenarios
        if is_demo or sev in ("CRITICAL", "HIGH"):
            # Close any previous popup toast so the new alert is immediately visible
            for p in list(self._active_popups):
                try:
                    p.close()
                except Exception:
                    pass
            self._active_popups.clear()
            self._popup_visible = True

            popup = AlertPopup(error_info, self)
            popup.show()
            self._active_popups.append(popup)

    def resolve_alert_from_popup(self, error_info: dict):
        eid = error_info.get("id", "")
        # Remove from active list widget if present
        for i in range(self.alerts_layout.count()):
            w = self.alerts_layout.itemAt(i).widget()
            if w and hasattr(w, "error_info") and w.error_info.get("id") == eid:
                w.setParent(None)
                break
        self._alert_count = max(0, self._alert_count - 1)
        self.card_alerts.set_value(str(self._alert_count))
        if eid:
            self._active_alert_ids.discard(eid)
            if self._monitor:
                self._monitor.mark_resolved(eid, cooldown_seconds=3600)
        # Clean up any active demo simulation (e.g. restore audio/services)
        if self._demo:
            self._demo.cleanup_active()

        self._alerts = [a for a in self._alerts if a.get("id") != eid]
        if self._lab_mode == "client" and self._lab_agent:
            self._lab_agent.update_errors(list(self._alerts))

        if error_info.get("repair_id") == "unknown_error":
            dlg = AIAssistantDialog(error_info, self)
            dlg.exec()
            self._fixed_count += 1
            self.card_fixed.set_value(str(self._fixed_count))
        else:
            dlg = RepairDialog(error_info, self)
            if dlg.exec():
                self._fixed_count += 1
                self.card_fixed.set_value(str(self._fixed_count))
        if self._alert_count == 0:
            self.no_alerts_lbl.setVisible(True)
            self.health_widgets["errors"].setText("None")
            self.health_widgets["errors"].setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

    def _fix_from_list(self, error_info: dict, item_widget: QFrame):
        eid = error_info.get("id", "")
        item_widget.setParent(None)
        self._alert_count = max(0, self._alert_count - 1)
        self.card_alerts.set_value(str(self._alert_count))
        # Allow this error to appear again only after a long cooldown
        if eid:
            self._active_alert_ids.discard(eid)
            # Tell the monitor this error is resolved — suppress re-alerting for 60 min
            if self._monitor:
                self._monitor.mark_resolved(eid, cooldown_seconds=3600)
        # Clean up any active demo simulation (e.g. restore audio/services)
        if self._demo:
            self._demo.cleanup_active()

        self._alerts = [a for a in self._alerts if a.get("id") != eid]
        if self._lab_mode == "client" and self._lab_agent:
            self._lab_agent.update_errors(list(self._alerts))

        if error_info.get("repair_id") == "unknown_error":
            dlg = AIAssistantDialog(error_info, self)
            dlg.exec()
        else:
            dlg = RepairDialog(error_info, self)
            if dlg.exec():
                self._fixed_count += 1
                self.card_fixed.set_value(str(self._fixed_count))
        if self._alert_count == 0:
            self.no_alerts_lbl.setVisible(True)
            self.health_widgets["errors"].setText("None")
            self.health_widgets["errors"].setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

    def _ignore_from_list(self, item_widget: QFrame):
        eid = item_widget.error_info.get("id", "")
        log_ignore(item_widget.error_info)
        item_widget.setParent(None)
        self._alert_count = max(0, self._alert_count - 1)
        self.card_alerts.set_value(str(self._alert_count))
        self._ignored_count += 1
        if eid:
            self._active_alert_ids.discard(eid)
            # Re-enable alerting after standard cooldown
            if self._monitor:
                self._monitor.mark_resolved(eid, cooldown_seconds=600)

        self._alerts = [a for a in self._alerts if a.get("id") != eid]
        if self._lab_mode == "client" and self._lab_agent:
            self._lab_agent.update_errors(list(self._alerts))

        if self._alert_count == 0:
            self.no_alerts_lbl.setVisible(True)
            self.health_widgets["errors"].setText("None")
            self.health_widgets["errors"].setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

    def _clear_all_alerts(self):
        for i in reversed(range(self.alerts_layout.count())):
            w = self.alerts_layout.itemAt(i).widget()
            if w and w is not self.no_alerts_lbl:
                w.setParent(None)
        self._alert_count = 0
        self._active_alert_ids.clear()
        self._alerts.clear()
        if self._lab_mode == "client" and self._lab_agent:
            self._lab_agent.update_errors([])
        if self._demo:
            self._demo.cleanup_active()
        self.card_alerts.set_value("0")
        self.no_alerts_lbl.setVisible(True)
        self.health_widgets["errors"].setText("None")
        self.health_widgets["errors"].setStyleSheet(f"color: {GREEN}; font-size: 13px; font-weight: 600; background: transparent; border: none;")

    

    def _run_demo(self, scenario_id: str, btn: QPushButton):
        original_text = btn.text()
        btn.setText("⏳ Injecting…")
        btn.setEnabled(False)

        def restore():
            btn.setText("✅ " + original_text.lstrip("▶  "))
            btn.setEnabled(True)
            # Reset label back after 3s
            QTimer.singleShot(3000, lambda: btn.setText(original_text))

        if self._demo:
            self._demo.run_demo(scenario_id, delay_seconds=1.5)

        # Re-enable after 4s (enough time for alert to appear)
        QTimer.singleShot(4000, restore)

    def closeEvent(self, event):
        """Minimize to tray instead of closing."""
        event.ignore()
        self.hide()
        if hasattr(self, 'tray'):
            self.tray.showMessage(
                "SmartFix AI",
                "Still running in the system tray. Right-click the tray icon to open or exit.",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )



def _is_admin() -> bool:
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def ensure_windows_autostart():
    """Register SmartFix AI to run silently in background whenever the PC boots.
    Uses Task Scheduler (highest privileges, no UAC prompts at boot), HKCU Run key,
    and the Windows Startup folder as multi-layered redundancy.
    """
    try:
        exe_path = os.path.join(ROOT, "SmartFix AI.exe")
        if not os.path.exists(exe_path):
            exe_path = sys.executable

        # 1. Windows Task Scheduler: ONLOGON with HIGHEST privileges
        try:
            tr_cmd = f'"{exe_path}" --background'
            subprocess.run(
                [
                    "schtasks.exe", "/Create",
                    "/TN", "SmartFix AI Autostart",
                    "/TR", tr_cmd,
                    "/SC", "ONLOGON",
                    "/RL", "HIGHEST",
                    "/F"
                ],
                capture_output=True,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
        except Exception as e:
            logger.debug(f"Task Scheduler setup note: {e}")

        # 2. Registry HKCU Run Key (works without elevation)
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, "SmartFix AI", 0, winreg.REG_SZ, f'"{exe_path}" --background')
        except Exception as e:
            logger.debug(f"HKCU Run key setup note: {e}")

        # 3. Startup Folder Shortcut fallback
        try:
            startup_dir = os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs\Startup"
            )
            if os.path.isdir(startup_dir):
                lnk_path = os.path.join(startup_dir, "SmartFix AI.lnk")
                ps_script = (
                    f'$WshShell = New-Object -ComObject WScript.Shell; '
                    f'$Shortcut = $WshShell.CreateShortcut("{lnk_path}"); '
                    f'$Shortcut.TargetPath = "{exe_path}"; '
                    f'$Shortcut.Arguments = "--background"; '
                    f'$Shortcut.WorkingDirectory = "{ROOT}"; '
                    f'$Shortcut.Description = "SmartFix AI Background Monitor"; '
                    f'$Shortcut.Save()'
                )
                subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    capture_output=True,
                    creationflags=0x08000000
                )
        except Exception as e:
            logger.debug(f"Startup folder shortcut setup note: {e}")

    except Exception as e:
        logger.warning(f"ensure_windows_autostart failed: {e}")


def main():
    # 1. Detect if started in background / autostart mode on PC boot
    is_background = any(
        arg.lower() in ("--background", "--minimized", "--tray", "--autostart")
        for arg in sys.argv
    )

    app = QApplication(sys.argv)
    app.setApplicationName("SmartFix AI")
    app.setOrganizationName("SmartFix")
    app.setQuitOnLastWindowClosed(False)

    # 2. Single-Instance Check via QLocalSocket:
    # If app is already running in background (e.g. from boot) and user double-clicks
    # the desktop shortcut, signal the running instance to show its window and exit cleanly.
    probe = QLocalSocket()
    probe.connectToServer("SmartFixAI_SingleInstance")
    if probe.waitForConnected(400):
        if not is_background:
            probe.write(b"SHOW\n")
            probe.waitForBytesWritten(1000)
        probe.disconnectFromServer()
        sys.exit(0)

    # 3. Verify admin elevation
    if not _is_admin():
        # Allow dev / non-admin bypass via flag or .env setting
        allow_non_admin = any(
            arg.lower() in ("--no-admin", "--dev", "-d") for arg in sys.argv
        ) or os.getenv("SMARTFIX_DEV", "0") in ("1", "true", "True")

        if allow_non_admin:
            logger.warning("[SmartFix] Running in Developer / Non-Admin mode. System repairs will be restricted.")
        else:
            # Automatically request Windows UAC elevation
            try:
                import ctypes
                script_path = os.path.abspath(__file__)
                args_str = " ".join(f'"{a}"' for a in sys.argv[1:])
                params = f'"{script_path}" {args_str}'.strip()
                res = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                if res > 32:
                    # Elevated child process launched successfully
                    sys.exit(0)
            except Exception as e:
                logger.debug(f"Auto-elevation failed: {e}")

            # If elevation was cancelled by user
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "SmartFix AI requires administrator privileges to execute system repairs.\n\n"
                    "To test without administrator privileges, run with '--dev':\n"
                    "python smartfix_app.py --dev",
                    "SmartFix AI — Elevation Required",
                    0x10  # MB_ICONERROR
                )
            except Exception:
                pass
            sys.exit(1)

    try:
        QFontDatabase.addApplicationFont("C:\\Windows\\Fonts\\segoeui.ttf")
        app.setFont(QFont("Segoe UI", 10))
    except Exception:
        pass

    window = MainWindow(is_background=is_background)

    if is_background:
        # Run silently in background / system tray on PC boot
        window.hide()
    else:
        # User explicitly launched app — show and bring to foreground
        window.showNormal()
        window.raise_()
        window.activateWindow()

        # Also schedule a deferred show 500ms after event loop starts
        def _deferred_show():
            window.showNormal()
            window.raise_()
            window.activateWindow()
            try:
                import ctypes
                hwnd = int(window.winId())
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.AllowSetForegroundWindow(-1)
            except Exception:
                pass

        QTimer.singleShot(500, _deferred_show)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
