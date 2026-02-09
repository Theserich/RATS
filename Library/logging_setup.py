import logging
import threading
import sys
import traceback
from Library.QtlogHandler import QtLogHandler, JsonFileHandler

class ModuleFilter(logging.Filter):
    def __init__(self, allowed_prefixes=None):
        super().__init__()
        self.allowed_prefixes = allowed_prefixes or ["Library", "project_viewer"]

    def filter(self, record):
        # Always allow ERROR or CRITICAL logs regardless of the module name
        if record.levelno >= logging.ERROR:
            return True
        return any(record.name.startswith(p) for p in self.allowed_prefixes)


def setupRootLoggerandHandler():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.propagate = True

    console_handler = logging.StreamHandler(sys.__stdout__)  # Use __stdout__ to bypass devnull
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    console_handler.setFormatter(formatter)

    qt_handler = QtLogHandler()
    file_handler = JsonFileHandler("application.log")
    log_filter = ModuleFilter(["Library", "project_viewer"])
    qt_handler.addFilter(log_filter)
    file_handler.addFilter(log_filter)
    console_handler.addFilter(log_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(qt_handler)
    root_logger.addHandler(file_handler)

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception
    return root_logger, qt_handler, file_handler

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("project_viewer").critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

def handle_thread_exception(args):
    # args.exc_info provides the (type, value, traceback) tuple
    logging.getLogger("project_viewer").critical(
        "Uncaught thread exception",
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
    )