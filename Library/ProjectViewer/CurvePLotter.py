from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from matplotlib.pyplot import Figure
from pathlib import Path
from Library.comset import *
from PyQt5.Qt import QComboBox, Qt, QKeySequence
from PyQt5.uic import loadUi
from Library.comset import read_settings
import matplotlib.colors as colors
from Library.helperFunctions import *
from pandas import DataFrame
from matplotlib.ticker import FixedLocator, FuncFormatter
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import mplcursors



class CurveWindow(QMainWindow):
    def __init__(self, path=Path("UIFiles/CalibrationPlot.ui"), parent=None):
        self.sortkeys = ['sample_nr', 'target_nr', 'prep_nr', 'project', 'project_nr', 'magazine', 'user_label', 'last_name',
                         'target_pressed', 'bp', 'treeid', 'user_label_nr', 'c14_age', 'c14_age_sig', 'fm', 'fm_sig', 'dc13',
                         'dc13_sig', 'target_id']
        self.widget = parent
        self.DB = parent.DB
        self.settingsWindow = False
        super(QWidget, self).__init__(parent)
        loadUi(path, self)
        self.load_settings()
        self.intcalData = getIntcalData()
        self.sortBox.addItems(self.sortkeys)
        self.sortBox.setCurrentIndex(self.sortkeys.index('treeid'))
        self.sortBox.currentIndexChanged.connect(self.update_params_and_redraw)
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
            self.t0_edit.setValue(settings["t0"])
            self.t1_edit.setValue(settings["t1"])
            self.BP_checkBox.setChecked(settings["bp"])
            self.stopped_checkbox.setChecked(settings["stopped"])
            if settings["sortkey"] in self.sortkeys:
                self.sortBox.setCurrentIndex(self.sortkeys.index(settings["sortkey"]))

    def initialize_plot(self):
        p = self.plot_widget.palette()
        p.setColor(self.backgroundRole(), Qt.white)
        self.setPalette(p)

        # get existing layout from UI (instead of overwriting with a new one)
        plot_layout = self.plot_widget.layout()
        if plot_layout is None:
            plot_layout = QVBoxLayout(self.plot_widget)
            self.plot_widget.setLayout(plot_layout)

        self.fig = Figure(figsize=(16, 9))
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
        self.draw_plot()

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


        # get data
        df = self.getData()
        df = calcD14C(df)
        intcaldf = self.intcalData.copy()
        searcht0 = min(self.t0, self.t1)
        searcht1 = max(self.t0, self.t1)
        if not self.bp:
            intcaldf['Time'] = 1950 - intcaldf['Time']
        ind = where((intcaldf['Time'] > searcht0) & (intcaldf['Time'] < searcht1))[0]
        for key in intcaldf.keys():
            intcaldf[key] = intcaldf[key][ind]


        data = groupdf(df, sortkey=self.sortkey)

        fmts = ["^", "D", "x", "p", "o"]
        allcolors = [f"C{i}" for i in range(10)]
        ncolors = len(allcolors)

        cursors = []
        annotations = []

        # stopped data
        if self.stopped:
            stoppeddf = self.getData(stopped=True)
            stoppeddf = calcD14C(stoppeddf)
            y, y_sig, years = (
                stoppeddf["d14C"],
                stoppeddf["d14C_sig"],
                1950 - stoppeddf["bp"],
            )
            errorbar = ax.errorbar(
                convertCalendarToBCE(years),
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
            def on_add(sel, dataset=stoppeddf):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                sel.annotation.set_text(
                    f"Project: {project}, target_id: {target_id}, Magazine: {magazine}"
                )
                annotations.append(sel.annotation)

        # main grouped data
        for i, key in enumerate(data):
            colindex = i % ncolors
            fmtindex = i % len(fmts)
            dat = data[key]
            color = allcolors[colindex]
            ecolor = colors.to_rgba(color, alph)
            y, y_sig, years = dat["d14C"], dat["d14C_sig"], 1950 - dat["bp"]

            errorbar = ax.errorbar(
                convertCalendarToBCE(years),
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
            cursor = mplcursors.cursor(errorbar.lines[0], hover=True)
            cursors.append(cursor)

            @cursor.connect("add")
            def on_add(sel, dataset=dat):
                for annotation in annotations:
                    annotation.set_visible(False)
                index = sel.index
                target_id = dataset["target_id"][index]
                project = dataset["project"][index]
                magazine = dataset["magazine"][index]
                sel.annotation.set_text(
                    f"Project: {project}, target_id: {target_id}, Magazine: {magazine}"
                )
                annotations.append(sel.annotation)

        # add intcal band
        ax.fill_between(
            convertCalendarToBCE(intcaldf["years"]),
            intcaldf["delta"] - intcaldf["delta_sig"],
            intcaldf["delta"] + intcaldf["delta_sig"],
            alpha=0.3,
            color="k",
            lw=0,
            label="IntCal20",
        )
        #ax.legend(frameon=False)
        ax.xaxis.set_major_formatter(FuncFormatter(CE_BCE_format))
        ax.set_ylabel(r"$\Delta^{14}$C (‰)")
        ax.grid(ls=":")

        # redraw
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
        query = (f"SELECT sample_nr as sample_nr,target_nr as target_nr,prep_nr, project,project_nr ,magazine,user_label,"
                 f"last_name, target_pressed, cast(substring_index(user_label_nr,'|',1) as decimal(6,1)) as bp,"
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
        }
        write_settings(settings, 'curve_settings')







