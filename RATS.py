import sys
import os
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
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
from Library.logging_setup import ModuleFilter, setupRootLoggerandHandler

root_logger,qt_handler,file_handler = setupRootLoggerandHandler()

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



