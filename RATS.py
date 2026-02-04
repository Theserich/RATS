from sys import argv, exit
from PyQt5.QtWidgets import QApplication
from Library.ProjectViewer.MainWindow import WidgetMain
from pyqtgraph.Qt import QtCore
from PyQt5.QtGui import QIcon
from pathlib import Path
import matplotlib
import faulthandler
faulthandler.enable()
matplotlib.use("Qt5Agg")
import logging
from Library.logging_setup import setup_root_logger, ModuleFilter
from Library.QtlogHandler import QtLogHandler, JsonFileHandler

qt_handler = QtLogHandler()
file_handler = JsonFileHandler("application.log")

# Add ModuleFilter to allow only your modules
qt_handler.addFilter(ModuleFilter(["Library", "project_viewer"]))
file_handler.addFilter(ModuleFilter(["Library", "project_viewer"]))

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.propagate = True

root_logger.addHandler(qt_handler)
root_logger.addHandler(file_handler)

if __name__ == '__main__':
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(argv)
        widget = WidgetMain(Path('UIFiles/projectWindow.ui'), qt_handler)
        icon_path = Path("Ratimg.ico").resolve()
        app.setWindowIcon(QIcon(str(icon_path)))
        widget.show()
        app.setStyle('Fusion')
        exit(app.exec_())
    except Exception as e:
        root_logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")



