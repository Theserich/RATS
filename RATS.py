from sys import argv, exit
from PyQt5.QtWidgets import QApplication
from Library.ProjectViewer.MainWindow import WidgetMain


if __name__ == '__main__':
    app = QApplication(argv)
    widget = WidgetMain('UIFiles/projectWindow.ui')
    widget.show()
    exit(app.exec_())

