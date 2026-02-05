from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
import logging



class LogModel(QAbstractTableModel):
    def __init__(self, logs=None):
        super().__init__()
        self._all_logs = logs or []
        self._filtered_logs = []
        self._headers = ["Time", "Level", "Module", "Message"]
        self.current_level = 0  # DEBUG
        self.apply_filter()

    def update_level(self, level):
        self.current_level = level
        self.apply_filter()

    def apply_filter(self):
        self.beginResetModel()
        self._filtered_logs = [
            log for log in self._all_logs
            if log.get("levelno", 0) >= self.current_level
        ]
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._filtered_logs)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        log = self._filtered_logs[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            if col == 0: return log.get("time", "")
            if col == 1: return log.get("level", "")
            if col == 2: return log.get("module", "")
            if col == 3:
                msg = log.get("message", "").replace('\n','')
                exc = log.get("exception", "").replace('\n',' ')
                return msg+': '+ exc
        if role == Qt.ToolTipRole:
            msg = log.get("message", "")
            exc = log.get("exception", "")
            if exc:
                return f"{msg}\n\nFULL EXCEPTION:\n{exc}"
            return msg
        if role == Qt.BackgroundRole:
            level = log.get("level", "")
            if level in ["ERROR", "CRITICAL"]: return Qt.red
            if level == "WARNING":
                return Qt.yellow
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def add_log(self, log_entry):
        if "levelno" not in log_entry:
            log_entry["levelno"] = getattr(logging, log_entry.get("level", "DEBUG"), 0)

        self._all_logs.append(log_entry)
        if log_entry["levelno"] >= self.current_level:
            self.beginInsertRows(QModelIndex(), len(self._filtered_logs), len(self._filtered_logs))
            self._filtered_logs.append(log_entry)
            self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self._all_logs.clear()
        self._filtered_logs.clear()
        self.endResetModel()