import threading
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QPushButton, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QColor

from monitor.llm_assistant import analyze_unknown_error
from monitor.learned_repairs import save_learned_error
from monitor.repair_engine import _run_ps

BG_MAIN     = "#090A0F"
BG_CARD     = "#12141D"
BG_CARD2    = "#1A1D27"
BORDER      = "#2D313F"
ACCENT      = "#5A67D8"
GREEN       = "#38A169"
TEXT1       = "#F7FAFC"
TEXT2       = "#A0AEC0"

class AIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, error_info):
        super().__init__()
        self.error_info = error_info

    def run(self):
        result = analyze_unknown_error(self.error_info)
        self.finished.emit(result)

class AIExecutionWorker(QThread):
    finished = pyqtSignal(bool, str)
    def __init__(self, script):
        super().__init__()
        self.script = script
    def run(self):
        success, out = _run_ps(self.script)
        self.finished.emit(success, out)

class AIAssistantDialog(QDialog):
    def __init__(self, error_info: dict, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        self.extracted_script = None
        
        self.setWindowTitle("SmartFix AI — Technical Assistant")
        self.setFixedSize(600, 500)
        self.setStyleSheet(f"background: {BG_MAIN}; color: {TEXT1}; font-family: 'Segoe UI Variable Display', 'Segoe UI', Inter, sans-serif;")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        
        self._build_ui()
        self._start_analysis()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        
        hdr = QHBoxLayout()
        brand = QLabel("🧠 SmartFix AI — Autonomous Diagnosis")
        brand.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 16px;")
        hdr.addWidget(brand)
        hdr.addStretch()
        layout.addLayout(hdr)
        
        
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {BORDER};")
        layout.addWidget(div)

        
        ctx_lbl = QLabel(f"Analyzing unknown error: {self.error_info.get('name', 'Unknown')}")
        ctx_lbl.setStyleSheet(f"color: {TEXT2}; font-size: 12px;")
        ctx_lbl.setWordWrap(True)
        layout.addWidget(ctx_lbl)
        
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {BORDER}; border-radius: 2px; border: none; }}
            QProgressBar::chunk {{ background: {ACCENT}; border-radius: 2px; }}
        """)
        layout.addWidget(self.progress)
        
        self.status_lbl = QLabel("Querying local LLM (Ollama)...")
        self.status_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 11px;")
        layout.addWidget(self.status_lbl)

        
        self.response_box = QTextEdit()
        self.response_box.setReadOnly(True)
        self.response_box.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD2};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 12px;
                color: {TEXT1};
                font-family: 'Segoe UI', Arial;
                font-size: 13px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(self.response_box)

        
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.exec_btn = QPushButton("🤖 Execute AI Generated Fix")
        self.exec_btn.setVisible(False)
        self.exec_btn.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: #00B85C; }}
        """)
        self.exec_btn.clicked.connect(self._execute_script)
        btn_row.addWidget(self.exec_btn)

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
        btn_row.addWidget(self.close_btn)

        layout.addLayout(btn_row)

    def _start_analysis(self):
        self.worker = AIWorker(self.error_info)
        self.worker.finished.connect(self._on_analysis_done)
        self.worker.start()

    def _on_analysis_done(self, result: str):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        
        
        m = re.search(r'```powershell\n(.*?)```', result, re.DOTALL | re.IGNORECASE)
        if m:
            self.extracted_script = m.group(1).strip()
            self.exec_btn.setVisible(True)

        self.progress.setStyleSheet(f"""
            QProgressBar {{ background: {BORDER}; border-radius: 2px; border: none; }}
            QProgressBar::chunk {{ background: {'#00D26A' if not result.startswith('❌') else '#FF3A3A'}; border-radius: 2px; }}
        """)
        
        self.status_lbl.setText("Analysis Complete." if not result.startswith('❌') else "Analysis Failed.")
        self.response_box.setMarkdown(result)
        self.close_btn.setVisible(True)

    def _execute_script(self):
        if not self.extracted_script: return
        self.exec_btn.setEnabled(False)
        self.exec_btn.setText("Executing...")
        self.status_lbl.setText("Executing AI Script...")
        
        self.exec_worker = AIExecutionWorker(self.extracted_script)
        self.exec_worker.finished.connect(self._on_exec_done)
        self.exec_worker.start()

    def _on_exec_done(self, success: bool, output: str):
        if success:
            self.status_lbl.setText("Execution Successful! Learning repair...")
            self.status_lbl.setStyleSheet(f"color: {GREEN}; font-size: 11px;")
            self.response_box.append("\n\n### Execution Output (Success)\n" + output)
            
            save_learned_error(self.error_info, self.extracted_script)
            self.response_box.append("\n\n**🧠 AI learned this repair! It will be handled automatically next time.**")
        else:
            self.status_lbl.setText("Execution Failed.")
            self.status_lbl.setStyleSheet("color: #FF3A3A; font-size: 11px;")
            self.response_box.append("\n\n### Execution Output (Failed)\n" + output)
