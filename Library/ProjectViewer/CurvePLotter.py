from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from matplotlib.pyplot import Figure, cm
from pathlib import Path
from Library.comset import *
from PyQt5.uic import loadUi
from Library.comset import read_settings
import matplotlib.colors as colors
from matplotlib import collections
from matplotlib.colors import ListedColormap
from Library.timer import timer
from Library.helperFunctions import *
from numpy import where, array, sort, linspace,argsort, full
from pandas import DataFrame
from matplotlib.ticker import FixedLocator, FuncFormatter
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import mplcursors

import math

class NaNSentinel:
    def __repr__(self):
        return "NaN"
    def __eq__(self, other):
        return isinstance(other, NaNSentinel)
    def __hash__(self):
        return hash("NaNSentinel")

NAN_KEY = NaNSentinel()

allcolormaps = ['Set1','Reds','cool', 'coolwarm', 'gray', 'hot','hot_r', 'jet','jet_r', 'nipy_spectral','nipy_spectral_r', 'ocean']


class CurveWindow(QMainWindow):
    def __init__(self, path=Path("UIFiles/CalibrationPlot.ui"), parent=None):
        self.sortkeys = ['sample_nr', 'target_nr', 'prep_nr', 'project', 'project_nr', 'magazine', 'user_label', 'last_name',
                         'target_pressed', 'bp', 'treeid', 'user_label_nr', 'c14_age', 'c14_age_sig', 'fm', 'fm_sig', 'dc13',
                         'dc13_sig', 'target_id','co2_final','rel err']
        self.standardsettings = {'window': {'size': [2116, 1112], 'pos': [1717, 18]}, 't0': 1000, 't1': 2000, 'bp': False, 'stopped': False, 'sortkey': 'c14_age_sig','colormap':'nipy_spectral'}
        self.widget = parent
        self.DB = parent.DB

        self.settingsWindow = False
        super(QWidget, self).__init__(parent)
        loadUi(path, self)

        self.intcalData = getIntcalData()
        self.sortBox.addItems(self.sortkeys)
        self.colorBox.addItems(allcolormaps)
        self.load_settings()
        self.sortBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.colorBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.t0_edit.editingFinished.connect(self.update_params_and_redraw)
        self.t1_edit.editingFinished.connect(self.update_params_and_redraw)
        self.BP_checkBox.stateChanged.connect(self.update_params_and_redraw)
        self.stopped_checkbox.stateChanged.connect(self.update_params_and_redraw)
        self.initialize_plot()
        self.update_params_and_redraw()
        self.show()

    def load_settings(self):
        settings = read_settings('curve_settings')
        if settings is not None:
            self.resize(*settings["window"]["size"])
            self.move(*settings["window"]["pos"])
            self.t0_edit.setValue(settings.get("t0",self.standardsettings['t0']))
            self.t1_edit.setValue(settings["t1"])
            self.BP_checkBox.setChecked(settings["bp"])
            self.stopped_checkbox.setChecked(settings["stopped"])
            sortkey = settings.get("sortkey",self.standardsettings['sortkey'])
            if settings["sortkey"] in self.sortkeys:
                self.sortBox.setCurrentIndex(self.sortkeys.index(sortkey))
                index = self.sortBox.currentIndex()
            colormap = settings.get("colormap",self.standardsettings['colormap'])
            if colormap in allcolormaps:
                self.colorBox.setCurrentIndex(allcolormaps.index(colormap))

    def initialize_plot(self):
        plot_layout = self.plot_widget.layout()
        if plot_layout is None:
            plot_layout = QVBoxLayout(self.plot_widget)
            self.plot_widget.setLayout(plot_layout)

        self.fig = Figure(figsize=(16,16))
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        self.ax = self.fig.subplots()
        self.ax.set_yticks([])
        self.fig.subplots_adjust(left=0.1, top=0.95, right=0.9, bottom=0.05)

    def update_params_and_redraw(self):
        """Grab UI values and redraw the plot."""
        self.t0 = self.t0_edit.value()
        self.t1 = self.t1_edit.value()
        self.bp = self.BP_checkBox.isChecked()
        self.sortkey = self.sortBox.currentText()
        self.stopped = self.stopped_checkbox.isChecked()
        self.colormap = self.colorBox.currentText()
        self.df = self.getData()
        self.stoppeddf = self.getData(stopped=True)
        self.draw_plot()

    @timer
    def draw_plot(self):
        """Main plotting logic (adapted from your standalone script)."""
        # clear previous
        self.fig.clear()
        ax = self.fig.subplots()

        # parameters
        fontsize = 15
        markersize = 6
        linewidth = 0.2
        alph = 0.7
        markeredgecolor = "w"
        capsize = 3
        intcaldf = self.intcalData.copy()
        searcht0 = min(self.t0, self.t1)
        searcht1 = max(self.t0, self.t1)
        if not self.bp:
            intcaldf['Time'] = 1950 - intcaldf['Time']
        ind = where((intcaldf['Time'] > searcht0) & (intcaldf['Time'] < searcht1))[0]
        for key in intcaldf.keys():
            intcaldf[key] = intcaldf[key][ind]
        data = groupdf(self.df, sortkey=self.sortkey)

        fmts = ["^", "D", "x", "p", "o"]
        allcolors = [f"C{i}" for i in range(10)]
        ncolors = len(allcolors)

        cursors = []
        annotations = []

        # stopped data
        if self.stopped:
            y, y_sig, years = (
                self.stoppeddf["d14C"],
                self.stoppeddf["d14C_sig"],
                1950 - self.stoppeddf["bp"],
            )
            if self.bp:
                x = 1950-years
            else:
                x = convertCalendarToBCE(years)
            errorbar = ax.errorbar(
                x,
                y,
                yerr=y_sig,
                fmt=".",
                capsize=capsize,
                label="Rejected data",
                ecolor=colors.to_rgba("grey", alph),
                color="grey",
                markerfacecolor=markeredgecolor,
                markersize=markersize,
            )
            cursor = mplcursors.cursor(errorbar.lines[0], hover=True)
            cursors.append(cursor)
            @cursor.connect("add")
            def on_add(sel, dataset=self.stoppeddf):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                c02 = dataset["co2_final"][index]
                relerr = dataset["rel err"][index]
                sel.annotation.set_text(
                    f"Project: {project}\ntarget_id: {target_id}\nMagazine: {magazine}\n relative err: {relerr:.1f}‰\nC0$_2$: {c02}"
                )
                annotations.append(sel.annotation)

        y, y_sig, years = self.df["d14C"], self.df["d14C_sig"], 1950 - self.df["bp"]
        if self.bp:
            x = 1950-years
        else:
            x = convertCalendarToBCE(years)
        scatter = ax.scatter(x,y,alpha=0)
        scatter.dataset = self.df
        def only_points(sel):
            return isinstance(sel.artist, collections.PathCollection)
        cursor = mplcursors.cursor(scatter, hover=True)
        cursors.append(cursor)
        @cursor.connect("add")
        def on_add(sel,dataset=self.df):
            for annotation in annotations:
                annotation.set_visible(False)
            index = sel.index
            target_id = dataset["target_id"][index]
            project = dataset["project"][index]
            magazine = dataset["magazine"][index]
            c02 = dataset["co2_final"][index]
            relerr = dataset["rel err"][index]
            sel.annotation.set_text(
                f"Project: {project}\ntarget_id: {target_id}\nMagazine: {magazine}\n relative err: {relerr:.1f}‰\nC0$_2$: {c02}"
            )
            annotations.append(sel.annotation)

        def sort_key(x):
            return (1, 0) if x is NAN_KEY else (0, x)
        if self.sortkey == "treeid" or self.sortkey == "project" or self.sortkey == "project_np":
            bps = [min(data[key]['bp']) for key in data.keys()]
            sortind = argsort(bps)
            keys_list = list(data.keys())
            sortedkeys = [keys_list[i] for i in sortind]
        else:
            sortedkeys = sorted(data.keys(), key=sort_key)

        num_colors = len(sortedkeys)
        colormap = cm.__dict__[self.colormap]
        # Create a ListedColormap with discrete colors
        allcolors = colormap(linspace(0, 1, num_colors))
        # convert to hex if needed
        allcolors = [colors.to_hex(c) for c in allcolors]
        for i, key in enumerate(sortedkeys):
            colindex = i % num_colors
            fmtindex = i % len(fmts)
            dat = data[key]
            color = allcolors[colindex]
            ecolor = colors.to_rgba(color, alph)
            #y, y_sig, years = dat["d14C"], dat["d14C_sig"], 1950 - dat["bp"]
            #x = convertCalendarToBCE(years) if self.bp else 1950 - years
            y, y_sig, years = (
                dat["d14C"],
                dat["d14C_sig"],
                1950 - dat["bp"],
            )
            if self.bp:
                x = 1950 - years
            else:
                x = convertCalendarToBCE(years)
            errorbar = ax.errorbar(
                x,
                y,
                yerr=y_sig,
                fmt=fmts[fmtindex],
                capsize=capsize,
                label=key,
                ecolor=ecolor,
                color=color,
                markerfacecolor=markeredgecolor,
                markersize=markersize,
            )
        x = 1950 - intcaldf["years"] if self.bp else convertCalendarToBCE(intcaldf["years"])
        ax.fill_between(
            x,
            intcaldf["delta"] - intcaldf["delta_sig"],
            intcaldf["delta"] + intcaldf["delta_sig"],
            alpha=0.3,
            color="k",
            lw=0,
            label="IntCal20",
        )
        #ax.legend(frameon=False)
        if self.bp:
            ax.set_xlabel("year bp")
        else:
            ax.xaxis.set_major_formatter(FuncFormatter(CE_BCE_format))
        ax.set_ylabel(r"$\Delta^{14}$C (‰)")
        ax.grid(ls=":")
        self.canvas.draw()


    def getData(self,stopped=False):
        if self.bp:
            t0_ = self.t0
            t1_ = self.t1
        if self.bp == False:
            t0_ = 1950 - self.t0
            t1_ = 1950 - self.t1
        t0 = min(t0_, t1_)
        t1 = max(t0_, t1_)
        query = (f"SELECT sample_nr, target_nr, prep_nr, project,project_nr ,magazine,user_label,"
                 f"last_name, target_pressed,co2_final, cast(substring_index(user_label_nr,'|',1) as decimal(6,1)) as bp,"
                 f" substring_index(user_label,'|',1) as treeid,"
                 f"  user_label_nr ,c14_age,c14_age_sig, fm as fm,fm_sig as fm_sig, dc13, dc13_sig FROM db_ams.target_v"
                 f" WHERE research='calibration' and stop={int(stopped)} and c14_age is not null and CONVERT(user_label_nr,UNSIGNED INTEGER) >= {t0}"
                 f" and CONVERT(user_label_nr,UNSIGNED INTEGER)<= {t1} AND user_label !=  'OXA 2'")
        cnx = self.DB.getConnection()
        if cnx is None:
            return
        cursor = cnx.cursor()
        cursor.execute(query)
        df = DataFrame(cursor.fetchall())
        df.columns = [name[0] for name in cursor.description]
        cursor.close()
        cnx.close()
        retdf = {}
        for key in df.keys():
            retdf[key] = array(df[key])
        retdf['target_id'] = [str(i) + '.' + str(j) + '.' + str(k) for i, j, k in
                              zip(df['sample_nr'], df['prep_nr'], df['target_nr'])]
        retdf['target_id'] = array(retdf['target_id'])
        retdf = calcD14C(retdf)
        retdf['rel err'] = retdf['fm_sig'] / retdf['fm']*1000
        return retdf

    def closeEvent(self, event):
        settings = {
            "window": {
                "size": [self.size().width(), self.size().height()],
                "pos": [self.pos().x(), self.pos().y()]
            },
            "t0": self.t0_edit.value(),
            "t1": self.t1_edit.value(),
            "bp": self.BP_checkBox.isChecked(),
            "stopped": self.stopped_checkbox.isChecked(),
            "sortkey": self.sortBox.currentText(),
            "colormap": self.colorBox.currentText()
        }
        write_settings(settings, 'curve_settings')

