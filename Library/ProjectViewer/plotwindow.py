from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from matplotlib.pyplot import Figure
from pathlib import Path
from PyQt5.Qt import Qt
from PyQt5.uic import loadUi
from Library.comset import read_settings
from numpy import array
import mplcursors
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar
)
from Library.ProjectViewer.Plotsettings import SettingsWindow


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
        self.initialize_plot()
        self.plot()
        self.settings_button.clicked.connect(self.open_settings)
        QTimer.singleShot(100, self.adjust_initial_layout)

    def open_settings(self):
        self.settingsWindow = SettingsWindow(self.data, parent=self)
        self.settingsWindow.show()

    def closeEvent(self, event):
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

    def plot(self):
        """
        Main plotting routine. Creates a twin y-axis for each ykey and positions
        their right spine 'outward' so tick labels + ylabel do not overlap.
        """

        if getattr(self, "_resizing", False):
            return
        self.load_plot_settings()
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

        if self.x_key == '':
            return

        x = self.data[self.x_key]
        try:
            x = array([float(v) for v in x])
        except Exception:
            if self.x_key == 'timedat':
                from datetime import datetime
                x = [datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                     for val in self.data[self.x_key]]
            else:
                x = self.data[self.x_key]

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
            line, = ax.plot(x, y, self.forms[i], color=self.colors[i], label=y_key)
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

            # set y-limits if provided
            self.set_ylimits(ax, self.ymins[i], self.ymaxs[i])

            # draw canvas to ensure text objects have positions (renderer required)
            # this is necessary to measure ticklabel and ylabel bounding boxes
            self.fig.canvas.draw()

            # get renderer
            renderer = self.fig.canvas.get_renderer()

            # compute width of tick labels + ylabel for this axis in pixels
            bbox_pixels = None

            # measure y tick labels (only those with text)
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
            self.plot_stddev_errorbars(x, y, self.x_key, y_key, i, ax)

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

            errorbar = ax.errorbar(x, y, fmt=self.forms[i], xerr=xsig, yerr=ysig, color=self.colors[i], capsize=3)
            cursor = mplcursors.cursor(errorbar.lines[0], hover=True)

            @cursor.connect("add")
            def on_add(sel, dataset=self.data):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                stopped = dataset["stop"][index]
                c02 = dataset["co2_final"][index]
                sel.annotation.set_text(
                    f"Project: {project}\ntarget_id: {target_id}\nMagazine: {magazine}\n C0$_2$: {c02}\nStopped: {stopped}"
                )
                annotations.append(sel.annotation)
                sel.annotation.get_figure().canvas.draw_idle()

        elif ysig_key in keys:
            ysig = self.data[ysig_key]
            try:
                ysig = array([float(val) for val in ysig])
            except Exception:
                ysig = self.data[ysig_key]

            errorbar = ax.errorbar(x, y, fmt=self.forms[i], yerr=ysig, color=self.colors[i], capsize=3)
            cursor = mplcursors.cursor(errorbar.lines[0], hover=True)

            @cursor.connect("add")
            def on_add(sel, dataset=self.data):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                stopped = int(dataset["stop"][index])
                c02 = dataset["co2_final"][index]
                sel.annotation.set_text(
                    f"Project: {project}\ntarget_id: {target_id}\nMagazine: {magazine}\n C0$_2$: {c02}\nStop: {stopped}"
                )
                annotations.append(sel.annotation)

    def initialize_plot(self):
        p = self.plot_widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        plot_layout = QVBoxLayout(self.plot_widget)

        self.fig = Figure()
        canvas = FigureCanvas(self.fig)
        self.addToolBar(Qt.BottomToolBarArea, NavigationToolbar(canvas, self))

        plot_layout.addWidget(canvas)

        # create a single host axis (standard Matplotlib Axes)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_yticks([])

        self.fig.subplots_adjust(left=0.1, top=0.95, right=0.9, bottom=0.05)

    def resizeEvent(self, event):
        self._resizing = True
        super().resizeEvent(event)

        try:
            self.fig.tight_layout()
            self.fig.canvas.draw_idle()
        finally:
            self._resizing = False



