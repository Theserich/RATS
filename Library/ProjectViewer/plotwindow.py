from copy import deepcopy
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.pyplot import Figure
from pathlib import Path
from PyQt5.Qt import Qt
from PyQt5.uic import loadUi
from Library.Settings.standardSettings import standard_proj_plot_Settings, windowsizes
from Library.comset import read_settings, read_setttins_with_defaults, write_settings
from numpy import array,isnan, where, nan
import mplcursors
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar
)
from Library.ProjectViewer.Plotsettings import SettingsWindow
from Library.helperFunctions import outlierTest


class PlotWindow(QMainWindow):
    def __init__(self, data, path=Path('UIFiles/Project_plotter.ui'), parent=None):
        self.data = data
        self.widget = parent
        self.settingsWindow = False
        self.active_annotations = []
        super(QWidget, self).__init__(parent)
        loadUi(path, self)

        self.allaxes = []
        self.colors = ['orange', 'red', 'blue', 'green',
                       'mediumspringgreen', 'forestgreen', 'yellowgreen',
                       'khaki', 'darkorange', 'indianred']

        print(self.Errorlabel.text())
        self.load_plot_settings()
        self.initialize_plot()
        self.setOutliervalues()
        self.plot()
        self.settings_button.clicked.connect(self.open_settings)
        self.OutlierCheck.toggled.connect(self.plot)
        self.pval_edit.editingFinished.connect(self.plot)
        self.Windowlen_edit.editingFinished.connect(self.plot)
        self.zscore_edit.editingFinished.connect(self.plot)
        QTimer.singleShot(100, self.adjust_initial_layout)

    def setOutliervalues(self):
        self.OutlierCheck.setChecked(self.Outliertest)
        self.pval_edit.setValue(self.pval)
        self.Windowlen_edit.setValue(self.lenwindow)
        self.zscore_edit.setValue(self.zfactor)

    def getOutlierValues(self):
        self.Outliertest = self.OutlierCheck.isChecked()
        self.pval = self.pval_edit.value()
        self.lenwindow = self.Windowlen_edit.value()
        self.zfactor = self.zscore_edit.value()




    def open_settings(self):
        self.settingsWindow = SettingsWindow(self.data, parent=self)
        self.settingsWindow.show()

    def closeEvent(self, event):
        windowsettings = read_setttins_with_defaults('windowsizes', windowsizes)
        windowsettings['plotwindow']['height'] = self.height()
        windowsettings['plotwindow']['width'] = self.width()
        write_settings(windowsettings,'windowsizes')
        settings = read_settings('proj_plot_Settings')
        for key in settings:
            settings[key] = self.__dict__[key]
        write_settings(settings,'proj_plot_Settings')
        if self.settingsWindow:
            self.settingsWindow.close()
            self.settingsWindow = False

    def adjust_initial_layout(self):
        try:
            self.fig.tight_layout()
            self.fig.canvas.draw_idle()
        except Exception as e:
            print(f"Layout adjustment failed: {e}")


    def load_plot_settings(self):
        self.display_settings = read_settings('display_settings')
        self.windowsettings = read_setttins_with_defaults('windowsizes',windowsizes)
        height = self.windowsettings['plotwindow']['height']
        width = self.windowsettings['plotwindow']['width']
        self.resize(width, height)
        settings = read_setttins_with_defaults('proj_plot_Settings', standard_proj_plot_Settings)
        for key in settings:
            self.__dict__[key] = settings[key]

    def set_xlimits(self):
        if self.xmin == 'auto' and self.xmax == 'auto':
            return
        if self.xmin == 'auto':
            self.ax.set_xlim(right=self.xmax)
        elif self.xmax == 'auto':
            self.ax.set_xlim(left=self.xmin)
        else:
            self.ax.set_xlim(left=self.xmin, right=self.xmax)

    def set_ylimits(self, ax, min, max):
        if min == 'auto' and max == 'auto':
            return
        if min == 'auto':
            ax.set_ylim(top=max)
        elif max == 'auto':
            ax.set_ylim(bottom=min)
        else:
            ax.set_ylim(bottom=min, top=max)

    def plotOutliers(self):

        testdata = deepcopy(self.data)
        for key in ['fm','fm_sig','user_label_nr']:
            for i, value in enumerate(testdata[key]):
                try:
                    testdata[key][i] = float(value)
                except:
                    testdata[key][i] = nan
            testdata[key] = array(testdata[key],dtype=float)

        x = self.x
        for major_key in ['fm','fm_sig','user_label_nr']:
            nonaninds = where(~isnan(testdata[major_key]))[0]
            x = x[nonaninds]
            for key in self.data:
                testdata[key] = testdata[key][nonaninds]
        try:
            badinds = outlierTest(testdata, self.lenwindow,self.pval, self.zfactor,ratio=0.7)
            if len(badinds) > 0:
                self.baddata = {}
                for key in testdata:
                    self.baddata[key] = testdata[key][badinds]
                for i, y_key in enumerate(self.ykeys):
                    if y_key == '':
                        continue
                    y = self.baddata[y_key]
                    try:
                        y = array([float(val) for val in y])
                    except Exception:
                        y = self.baddata[y_key]
                    self.allaxes[i].plot(x[badinds],y,self.forms[i],color='k',zorder=1000,markersize=10)
        except Exception as e:
            self.Errorlabel.setText(f"Error: {e}")
            pass


    def plot(self):
        """
        Main plotting routine. Creates a twin y-axis for each ykey and positions
        their right spine 'outward' so tick labels + ylabel do not overlap.
        """
        self.getOutlierValues()
        if getattr(self, "_resizing", False):
            return

        fontsize = self.display_settings.get('fontsize', 10)
        for ann in getattr(self, "active_annotations", []):
            try:
                ann.set_visible(False)
            except:
                pass
        self.active_annotations.clear()
        # clear host axis
        self.ax.clear()

        # remove previously created twin axes
        for ax in self.allaxes:
            try:
                ax.remove()
            except Exception:
                pass
        self.allaxes.clear()
        if self.xkey == '':
            return

        self.x = self.data[self.xkey]
        try:
            self.x = array([float(v) for v in self.x])
        except Exception:
            if self.xkey == 'timedat':
                from datetime import datetime
                self.x = [datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                     for val in self.data[self.xkey]]
            else:
                self.x = self.data[self.xkey]

        # cumulative outward offset (in points). we'll increment it after measuring each axis.
        cumulative_offset_points = 0.0
        # small base padding (points) to keep distance from main plot
        base_padding_points = 6.0

        for i, y_key in enumerate(self.ykeys):
            if y_key == '':
                continue
            y = self.data[y_key]
            try:
                y = array([float(val) for val in y])
            except Exception:
                y = self.data[y_key]

            # create a new twin y-axis
            ax = self.ax.twinx()
            self.allaxes.append(ax)

            # plot the data
            line, = ax.plot(self.x, y, self.forms[i], color=self.ycolors[i], label=y_key)
            cursor = mplcursors.cursor(line, hover=True)
            annotations = self.active_annotations
            @cursor.connect("add")
            def on_add(sel, dataset=self.data):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                c02 = dataset["co2_final"][index]
                sel.annotation.set_text(
                    f"Project: {project}\ntarget_id: {target_id}\nMagazine: {magazine}\n C0$_2$: {c02}"
                )
                annotations.append(sel.annotation)
                sel.annotation.get_figure().canvas.draw_idle()
            # set label color, text and tick font size
            ax.yaxis.label.set_color(line.get_color())
            ax.set_ylabel(self.ylabels[i], fontsize=fontsize)
            ax.tick_params(axis='y', which='major', labelsize=fontsize)
            self.set_ylimits(ax, self.ymins[i], self.ymaxs[i])
            self.fig.canvas.draw()
            renderer = self.fig.canvas.get_renderer()
            bbox_pixels = None
            yticks = ax.get_yticklabels()
            for tl in yticks:
                text = tl.get_text()
                if text is None or text == '':
                    # sometimes ticklabels are blank before renderer updates; measure visible ones
                    # use get_window_extent anyway; it will reflect text layout
                    pass
                try:
                    bb = tl.get_window_extent(renderer=renderer)
                    bbox_pixels = bb if bbox_pixels is None else bbox_pixels.union(bb)
                except Exception:
                    pass

            # measure ylabel
            ylabel = ax.yaxis.get_label()
            try:
                bb_label = ylabel.get_window_extent(renderer=renderer)
                bbox_pixels = bb_label if bbox_pixels is None else bbox_pixels.union(bb_label)
            except Exception:
                pass

            # fallback if nothing measured (rare)
            if bbox_pixels is None:
                # make a minimal bbox in pixels
                bbox_pixels = type('B', (), {'width': 0.0})()

            # add padding in pixels (convert a small point padding to pixels)
            padding_pixels = (base_padding_points * self.fig.dpi) / 72.0  # points -> pixels
            width_pixels = getattr(bbox_pixels, "width", 0.0) + padding_pixels

            # convert pixels -> points (Matplotlib 'outward' amount is in points)
            width_points = width_pixels * 72.0 / self.fig.dpi

            # compute the offset to set for this axis's spine
            # we want this axis to be placed outward by cumulative_offset + width of previous axes
            # so for the first created twin axis we add base padding as well
            offset_points = cumulative_offset_points + base_padding_points

            # set the spine position outward by offset_points (units: points)
            try:
                ax.spines['right'].set_position(('outward', offset_points+i*fontsize*1.5))
            except Exception:
                # Some Matplotlib configurations may not allow direct spine move; ignore gracefully
                pass

            # after positioning, update cumulative_offset for the next axis:
            cumulative_offset_points += width_points
            # attach errorbars & mplcursors if available
            self.plot_stddev_errorbars(self.x, y, self.xkey, y_key, i, ax)
        self.Errorlabel.setText("")
        if self.Outliertest:
            try:
                self.plotOutliers()
            except Exception as e:
                print(f"Error plotting outliers: {e}")
        # host axis final formatting
        self.ax.set_xlabel(self.xlabel, fontsize=fontsize)
        self.ax.set_yticks([])
        self.ax.tick_params(axis='x', which='major', labelsize=fontsize, rotation=90)

        self.set_xlimits()

        # final draw

        try:
            self.fig.canvas.draw()
        except Exception:
            self.ax.clear()
            self.fig.canvas.draw()

        self.fig.tight_layout()
        self.fig.canvas.draw_idle()


    def plot_stddev_errorbars(self, x, y, x_key, y_key, i, ax):
        annotations = self.active_annotations
        xsig_key = x_key + '_sig'
        ysig_key = y_key + '_sig'
        keys = self.data.keys()
        if xsig_key in keys and ysig_key in keys:
            xsig = self.data[xsig_key]
            ysig = self.data[ysig_key]
            try:
                xsig = array([float(val) for val in xsig])
            except Exception:
                xsig = self.data[xsig_key]
            try:
                ysig = array([float(val) for val in ysig])
            except Exception:
                ysig = self.data[ysig_key]
            ax.errorbar(x, y, fmt=self.forms[i], xerr=xsig, yerr=ysig, color=self.ycolors[i], capsize=3)
        elif ysig_key in keys:
            ysig = self.data[ysig_key]
            try:
                ysig = array([float(val) for val in ysig])
            except Exception:
                ysig = self.data[ysig_key]

            ax.errorbar(x, y, fmt=self.forms[i], yerr=ysig, color=self.ycolors[i], capsize=3)

    def initialize_plot(self):
        p = self.plot_widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        plot_layout = QVBoxLayout(self.plot_widget)

        self.fig = Figure()
        canvas = FigureCanvas(self.fig)
        self.addToolBar(Qt.BottomToolBarArea, NavigationToolbar(canvas, self))
        canvas.mpl_connect("button_press_event", self.clear_annotations)
        plot_layout.addWidget(canvas)

        # create a single host axis (standard Matplotlib Axes)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_yticks([])

        self.fig.subplots_adjust(left=0.1, top=0.95, right=0.9, bottom=0.05)

    def clear_annotations(self, event=None):
        for ann in self.active_annotations:
            try:
                ann.set_visible(False)
            except:
                pass
        self.active_annotations.clear()
        self.fig.canvas.draw_idle()

    def resizeEvent(self, event):
        self._resizing = True
        super().resizeEvent(event)

        try:
            self.fig.tight_layout()
            self.fig.canvas.draw_idle()
        finally:
            self._resizing = False



