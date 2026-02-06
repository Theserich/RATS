import sys
import os
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QSplashScreen
from Library.ProjectViewer.MainWindow import WidgetMain
from pyqtgraph.Qt import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QPixmap, Qt
from pathlib import Path
import matplotlib
import faulthandler
matplotlib.use("Qt5Agg")
from Library.logging_setup import setupRootLoggerandHandler
faulthandler.enable()


if __name__ == '__main__':
    try:
        root_logger, qt_handler, file_handler = setupRootLoggerandHandler()
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(argv)
        splash = QSplashScreen(QPixmap(str(Path('UIFiles/RATS_splash.png').resolve())))
        splash.show()
        splash.showMessage('Starting up', alignment=Qt.AlignBottom)
        widget = WidgetMain(Path('UIFiles/projectWindow.ui'), qt_handler)
        icon_path = Path("Ratimg.ico").resolve()
        app.setWindowIcon(QIcon(str(icon_path)))
        splash.finish(widget)
        widget.show()
        app.setStyle('Fusion')
        exit(app.exec_())
    except Exception as e:
        root_logger.error(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")



