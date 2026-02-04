import logging


class ModuleFilter(logging.Filter):
    def __init__(self, allowed_prefixes=None):
        super().__init__()
        self.allowed_prefixes = allowed_prefixes or ["Library", "project_viewer"]

    def filter(self, record):
        return any(record.name.startswith(p) for p in self.allowed_prefixes)


def setup_root_logger(qt_handler, file_handler, level=logging.DEBUG):
    """
    Setup the root logger with Qt + file handlers.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.propagate = True

    # Only add handlers once
    if not any(isinstance(h, type(qt_handler)) for h in root_logger.handlers):
        qt_handler.addFilter(ModuleFilter())
        file_handler.addFilter(ModuleFilter())
        root_logger.addHandler(qt_handler)
        root_logger.addHandler(file_handler)

    return root_logger