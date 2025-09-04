from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from matplotlib.pyplot import Figure
from Library.timer import timer
from PyQt5.Qt import QComboBox, Qt, QKeySequence
from PyQt5.uic import loadUi
from Library.comset import read_settings
from numpy import where, array

from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from Library.ProjectViewer.Plotsettings import SettingsWindow


class PlotWindow(QMainWindow):
    def __init__(self,data, path='UIFiles/Project_plotter.ui', parent=None):
        self.data = data
        self.widget = parent
        self.settingsWindow = False
        super(QWidget, self).__init__(parent)
        loadUi(path, self)
        self.allaxes = []
        self.colors = ['orange', 'red', 'blue', 'green',
                       'mediumspringgreen', 'forestgreen', 'yellowgreen',
                       'khaki', 'darkorange', 'indianred']
        self.initialize_plot()
        self.plot()
        self.settings_button.clicked.connect(self.open_settings)


    def open_settings(self):
        self.settingsWindow = SettingsWindow(self.data,parent=self)
        self.settingsWindow.show()

    def closeEvent(self, event):
        if self.settingsWindow:
            self.settingsWindow.close()
            self.settingsWindow = False


    def load_plot_settings(self):
        self.display_settings =read_settings('display_settings')
        if not self.settingsWindow:
            plotKeys = read_settings('proj_plot_Settings')
            self.x_key = plotKeys['xkey']
            self.xlabel = plotKeys['xlabel']
            self.ylabels = plotKeys['ylabels']
            self.ykeys = plotKeys['ykeys']
            self.ymins = plotKeys['ymins']
            self.ymaxs = plotKeys['ymaxs']
            self.xmin = plotKeys['xmin']
            self.xmax = plotKeys['xmax']
            self.colors = plotKeys['ycolors']
            self.forms = plotKeys['forms']
        else:
            self.x_key = self.settingsWindow.xkey
            self.xlabel = self.settingsWindow.xlabel
            self.ylabels = self.settingsWindow.ylabels
            self.ykeys = self.settingsWindow.ykeys
            self.ymins = self.settingsWindow.ymins
            self.ymaxs = self.settingsWindow.ymaxs
            self.xmin = self.settingsWindow.xlimmin
            self.xmax = self.settingsWindow.xlimmax
            self.colors = self.settingsWindow.ycolors
            self.forms = self.settingsWindow.forms

    def set_xlimits(self):
        if self.xmin == 'auto' and self.xmax == 'auto':
            pass
        elif self.xmin == 'auto':
            self.ax.set_xlim(right=self.xmax)
        elif self.xmax == 'auto':
            self.ax.set_xlim(left=self.xmin)
        else:
            self.ax.set_xlim(left=self.xmin, right=self.xmax)

    def set_ylimits(self, ax, min, max):
        if min == 'auto' and max == 'auto':
            pass
        elif min == 'auto':
            ax.set_ylim(top=max)
        elif max == 'auto':
            ax.set_ylim(bottom=min)
        else:
            ax.set_ylim(bottom=min, top=max)

    def plot(self):
        self.load_plot_settings()
        fontsize = self.display_settings['fontsize']
        self.ax.clear()
        for i in self.allaxes: i.remove()
        self.allaxes = []
        if self.x_key == '':
            return
        x = self.data[self.x_key]


        try:
            x = array([float(v) for v in x])
        except:
            if self.x_key == 'timedat':
                from datetime import datetime
                x = []
                for i,val in enumerate(self.data[self.x_key]):
                        x.append(datetime.strptime(val,'%Y-%m-%d %H:%M:%S'))
            else:
                x = self.data[self.x_key]


        lines = []
        names = []
        for i, y_key in enumerate(self.ykeys):
            if y_key == '':
                continue
            y = self.data[y_key]
            try:
                y = array([float(val) for val in y])
            except:
                y = self.data[y_key]
            name = y_key
            ax = self.ax.twinx()
            if i == 'asdasda':
                ax.grid(ls=':')
                self.ax.grid(ls=':')
            line, = ax.plot(x, y, self.forms[i], color=self.colors[i], label=name)
            lines.append(line)
            self.plot_stddev_errorbars(x, y, self.x_key, y_key, i, ax)
            names.append(name)
            ax.spines['right'].set_position(('outward', 60 * i))
            ax.yaxis.label.set_color(line.get_color())
            ax.set_ylabel(self.ylabels[i],fontsize=fontsize)
            ax.tick_params(axis='y', which='major', labelsize=fontsize)
            self.set_ylimits(ax, self.ymins[i], self.ymaxs[i])
            self.allaxes.append(ax)
        self.ax.set_xlabel(self.xlabel,fontsize=fontsize)
        self.fig.subplots_adjust(left=0.001, top=1, right=1 - len(self.ykeys) / 11, bottom=0.2)
        self.ax.set_yticks([])
        self.ax.tick_params(axis='x', which='major', labelsize=fontsize, rotation=90)
        self.set_xlimits()
        try:
            self.fig.canvas.draw()
        except:
            self.ax.clear()
            self.fig.canvas.draw()

    def plot_stddev_errorbars(self, x, y, x_key, y_key, i, ax):
        xsig_key = x_key + '_sig'
        ysig_key = y_key + '_sig'
        keys = self.data.keys()
        if xsig_key in keys and ysig_key in keys:
            xsig = self.data[xsig_key]
            ysig = self.data[ysig_key]
            try:
                xsig = array([float(val) for val in xsig])
            except:
                xsig = self.data[xsig_key]
            try:
                ysig = array([float(val) for val in ysig])
            except:
                ysig = self.data[ysig_key]
            ax.errorbar(x, y, fmt=self.forms[i], xerr=xsig, yerr=ysig, color=self.colors[i], capsize=3)
        elif ysig_key in keys:
            ysig = self.data[ysig_key]
            try:
                ysig = array([float(val) for val in ysig])
            except:
                ysig = self.data[ysig_key]
            ax.errorbar(x, y, fmt=self.forms[i], yerr=ysig, color=self.colors[i], capsize=3)


    def initialize_plot(self):
        p = self.plot_widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)
        plot_layout = QVBoxLayout(self.plot_widget)
        self.fig = Figure()
        canvas = FigureCanvas(self.fig)
        self.addToolBar(Qt.BottomToolBarArea, NavigationToolbar(canvas, self))
        plot_layout.addWidget(canvas)
        self.ax = canvas.figure.subplots()
        self.ax.set_yticks([])
        self.fig.subplots_adjust(left=0.1, top=0.95, right=0.9, bottom=0.05)


