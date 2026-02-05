import logging
import time
import json
import os
import traceback
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableView, QTextEdit, QSplitter, QHeaderView, QHBoxLayout,QComboBox,QPushButton, QLabel, QAbstractItemView
from Library.LogTableModel import LogModel

class ModuleFilter(logging.Filter):
    def __init__(self, allowed_prefixes=None):
        super().__init__()
        self.allowed_prefixes = allowed_prefixes or ["Library", "project_viewer"]

    def filter(self, record):
        return any(record.name.startswith(p) for p in self.allowed_prefixes)

class JsonFileHandler(logging.Handler):
    def __init__(self, filename="application.log"):
        super().__init__()
        self.filename = filename

    def emit(self, record):
        log_entry = {
            "timestamp": record.created,
            "time": time.strftime("%H:%M:%S", time.localtime(record.created)),
            "level": record.levelname,
            "levelno": record.levelno,
            "module": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_entry["exception"] = "".join(
                traceback.format_exception(*record.exc_info)
            )

        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass

class QtLogHandler(logging.Handler, QObject):
    log_signal = pyqtSignal(dict)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        formatter = logging.Formatter(fmt="%(asctime)s", datefmt="%H:%M:%S")
        self.setFormatter(formatter)

    def emit(self, record):
        log_entry = {
            "time": self.format(record),
            "level": record.levelname,
            "levelno": record.levelno,
            "message": record.getMessage(),
            "module": record.name,
        }

        if record.exc_info:
            import traceback
            log_entry["message"] += "\n" + "".join(
                traceback.format_exception(*record.exc_info)
            )

        self.log_signal.emit(log_entry)

class LoggerWindow(QMainWindow):
    def __init__(self, handler, log_file="application.log", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(1100, 600)
        self.handler = handler
        self.log_file = log_file
        self.model = LogModel()
        self.handler.log_signal.connect(self.add_log)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 1. Controls (Level Box & Clear)
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Log Level:"))
        self.levelBox = QComboBox()
        self.levelBox.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.levelBox.currentTextChanged.connect(self.change_level)
        control_layout.addWidget(self.levelBox)

        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.clear_logs)
        control_layout.addWidget(self.clearButton)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 2. Setup the Table View
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setWordWrap(False)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.verticalHeader().setDefaultSectionSize(25)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # Configure Header STRETCH
        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h_header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.table_view.clicked.connect(self.display_log_detail)

        # 3. Setup Detail Box
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setStyleSheet("background-color: #f0f0f0; font-family: Consolas, monospace;")

        # 4. CRASH FIX: Create Splitter and add widgets here ONLY
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.table_view)
        self.splitter.addWidget(self.detail_view)
        self.splitter.setStretchFactor(0, 3)  # Table gets more space
        self.splitter.setStretchFactor(1, 1)  # Box gets less space

        # Add ONLY the splitter to the main layout
        layout.addWidget(self.splitter)

        self.load_recent_logs()
        self.prune_old_logs()

    def display_log_detail(self, index):
        # We need to get the log from the FILTERED list in the model
        log = self.model._filtered_logs[index.row()]
        msg = log.get("message", "")
        exc = log.get("exception", "")
        self.detail_view.setPlainText(f"{msg}\n\n{exc}" if exc else msg)

    def change_level(self, level_text):
        new_level = getattr(logging, level_text)
        logging.getLogger().setLevel(new_level)
        self.model.update_level(new_level)  # Update model filter

    def add_log(self, log_entry):
        self.model.add_log(log_entry)
        self.table_view.scrollToBottom()

    def clear_logs(self):
        self.model.clear()
        self.detail_view.clear()
        if os.path.exists(self.log_file):
            open(self.log_file, 'w').close()

    def load_recent_logs(self):
        if not os.path.exists(self.log_file): return
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    self.model.add_log(json.loads(line))
                except:
                    continue

    def prune_old_logs(self):
        if not os.path.exists(self.log_file):
            return
        now = time.time()
        one_day_ago = now - 86400
        new_lines = []
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log = json.loads(line)
                    if log["timestamp"] >= one_day_ago:
                        new_lines.append(line)
                except Exception:
                    continue
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)