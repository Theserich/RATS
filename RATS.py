import sys
import os
import requests
import webbrowser

if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')

from sys import argv, exit
from PyQt5.QtWidgets import QApplication, QSplashScreen, QMessageBox
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


CURRENT_VERSION = os.getenv("APP_VERSION", "v1.0.10")
GITHUB_REPO = "Theserich/RATS"


# Use QThread instead of threading.Thread for Qt thread-safety
class UpdateCheckerThread(QtCore.QThread):
    update_available = QtCore.pyqtSignal(str, str)
    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "RATS-App"}
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                latest_tag = data.get("tag_name")
                release_url = data.get("html_url")
                if latest_tag and latest_tag.lstrip('v') != CURRENT_VERSION.lstrip('v'):
                    self.update_available.emit(latest_tag, release_url)
        except Exception:
            pass  # Ignore network issues during startup update check


def prompt_for_update(version, url):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Update Available")
    msg.setText(f"A new version ({version}) of RATS is available.")
    msg.setInformativeText("Would you like to open the download page?")
    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    if msg.exec_() == QMessageBox.Yes:
        webbrowser.open(url)


if __name__ == '__main__':
    try:
        root_logger, qt_handler, file_handler = setupRootLoggerandHandler()
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QApplication(argv)

        # Show splash screen immediately
        splash = QSplashScreen(QPixmap(str(Path('UIFiles/RATS_splash.png').resolve())))
        splash.show()
        splash.showMessage('Starting up', alignment=Qt.AlignBottom)
        app.processEvents()  # force the splash to paint before we do anything else

        # Now kick off the update checker (runs in background, won't block splash)
        update_thread = UpdateCheckerThread(app)
        update_thread.update_available.connect(prompt_for_update)
        update_thread.start()

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