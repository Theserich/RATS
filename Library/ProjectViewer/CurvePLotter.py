from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from matplotlib.pyplot import Figure
from pathlib import Path
from PyQt5.Qt import QComboBox, Qt, QKeySequence
from PyQt5.uic import loadUi
from Library.comset import read_settings
from numpy import where, array

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from Library.ProjectViewer.Plotsettings import SettingsWindow


class PlotWindow(QMainWindow):
    def __init__(self,data, path=Path('UIFiles/Project_plotter.ui'), parent=None):
        self.data = data
        self.widget = parent
        self.settingsWindow = False
        super(QWidget, self).__init__(parent)
        loadUi(path, self)
        self.allaxes = []
        self.colors = ['orange', 'red', 'blue', 'green',
                       'mediumspringgreen', 'forestgreen', 'yellowgreen',
                       'khaki', 'darkorange', 'indianred']







