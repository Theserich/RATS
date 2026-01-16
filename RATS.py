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

if __name__ == '__main__':
    try:
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(argv)
        widget = WidgetMain(Path('UIFiles/projectWindow.ui'))
        icon_path = Path("Ratimg.ico").resolve()
        app.setWindowIcon(QIcon(str(icon_path)))
        widget.show()
        app.setStyle('Fusion')
        exit(app.exec_())
    except Exception as e:
        print(f"\n An error occurred: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")



