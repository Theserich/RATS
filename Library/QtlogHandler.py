import logging
import time
import json
import os
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QLabel, QHBoxLayout

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
        self.log_signal.emit(log_entry)

class LoggerWindow(QMainWindow):
    def __init__(self, handler, log_file="application.log", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Logs")
        self.resize(900, 450)
        self.handler = handler
        self.handler.log_signal.connect(self.add_log)

        self.all_logs = []
        self.current_level = logging.DEBUG
        self.log_file = log_file

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Controls
        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)
        control_layout.addWidget(QLabel("Log Level:"))
        self.levelBox = QComboBox()
        self.levelBox.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.levelBox.setCurrentText("DEBUG")
        self.levelBox.currentTextChanged.connect(self.change_level)
        control_layout.addWidget(self.levelBox)
        self.clearButton = QPushButton("Clear")
        self.clearButton.clicked.connect(self.clear_logs)
        control_layout.addWidget(self.clearButton)
        control_layout.addStretch()

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Time", "Level", "Module", "Message"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Load logs from file
        self.prune_old_logs()
        self.load_recent_logs()

    def add_log(self, log_entry):
        if "levelno" not in log_entry:
            log_entry["levelno"] = getattr(logging, log_entry["level"])
        self.all_logs.append(log_entry)
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        for log in self.all_logs:
            if log["levelno"] >= self.current_level:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(log["time"]))
                self.table.setItem(row, 1, QTableWidgetItem(log["level"]))
                self.table.setItem(row, 2, QTableWidgetItem(log["module"]))
                self.table.setItem(row, 3, QTableWidgetItem(log["message"]))
                color = None
                if log["level"] == "ERROR":
                    color = Qt.red
                elif log["level"] == "WARNING":
                    color = Qt.yellow
                if color:
                    for col in range(4):
                        item = self.table.item(row, col)
                        if item:
                            item.setBackground(color)
        self.table.scrollToBottom()

    def clear_logs(self):
        self.all_logs.clear()
        self.table.setRowCount(0)

    def change_level(self, level_text):
        self.current_level = getattr(logging, level_text)
        logging.getLogger().setLevel(self.current_level)
        self.refresh_table()

    def load_recent_logs(self):
        if not os.path.exists(self.log_file):
            return
        now = time.time()
        one_day_ago = now - 86400
        with open(self.log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    log = json.loads(line)
                    if log["timestamp"] >= one_day_ago:
                        self.all_logs.append(log)
                except Exception:
                    continue
        self.refresh_table()

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