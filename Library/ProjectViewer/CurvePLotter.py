from PyQt5.QtCore import QThread, pyqtSignal, QObject
import pyqtgraph as pg
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from PyQt5.uic import loadUi
from Library.timer import timer
from Library.helperFunctions import *
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QGridLayout, QWidget, QFileDialog, QAction
from pathlib import Path
from matplotlib import cm
from Library.comset import *
from PyQt5.uic import loadUi
from Library.comset import read_settings
from Library.timer import timer
from Library.helperFunctions import *
from numpy import where, array, sort, linspace,argsort, full
from pandas import DataFrame

class PlotWorker(QObject):
    # Signals to send data back to the UI
    data_ready = pyqtSignal(object, object, list)  # (df, stopped_df, sorted_keys)
    error = pyqtSignal(str)
    def __init__(self, db_instance, params):
        super().__init__()
        self.DB = db_instance
        self.params = params

    def run(self):
        try:
            # Extract params for clarity
            t0, t1, bp, stopped_enabled,sortkey = self.params
            # Perform heavy DB calls (Logic from your existing getData)
            df = self.fetch_data(t0, t1, bp, stopped=False)
            df = calcD14C(df)
            stopped_df = None
            if stopped_enabled:
                stopped_df = self.fetch_data(t0, t1, bp, stopped=True)
            grouped_data = groupdf(df, sortkey=sortkey)
            sorted_keys = list(grouped_data.keys())
            self.data_ready.emit(grouped_data, stopped_df, sorted_keys)
        except Exception as e:
            self.error.emit(str(e))

    def fetch_data(self, t0, t1, bp, stopped):
        # Your existing SQL query logic from getData() goes here
        if bp:
            t0_ = t0
            t1_ = t1
        if bp == False:
            t0_ = 1950 - t0
            t1_ = 1950 - t1
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

sortkeys = ['sample_nr', 'target_nr', 'prep_nr', 'project', 'project_nr', 'magazine', 'user_label',
                         'last_name',
                         'target_pressed', 'bp', 'treeid', 'user_label_nr', 'c14_age', 'c14_age_sig', 'fm', 'fm_sig',
                         'dc13',
                         'dc13_sig', 'target_id', 'co2_final', 'rel err']
allcolormaps = ['Set1','Reds','cool', 'coolwarm', 'gray', 'hot','hot_r', 'jet','jet_r', 'nipy_spectral','nipy_spectral_r', 'ocean']
standardsettings = {'window': {'size': [2116, 1112], 'pos': [1717, 18]}, 't0': 1500, 't1': 2000, 'bp': False, 'stopped': False, 'sortkey': 'treeid','colormap':'nipy_spectral','legend':True}

class CurveWindow(QMainWindow):
    def __init__(self, path=Path("UIFiles/CalibrationPlot.ui"), parent=None):
        self.sortkeys = ['treeid','magazine']
        super(CurveWindow, self).__init__(parent)
        loadUi(path, self)
        self.thread = None
        self.worker = None
        self.DB = parent.DB
        self.plot_view = pg.PlotWidget()
        self.plot_view.setBackground('w')
        self.intcalData = getIntcalData()
        self.load_settings()
        if self.plot_widget.layout() is None:
            layout = QVBoxLayout(self.plot_widget)
            self.plot_widget.setLayout(layout)
        self.plot_widget.layout().addWidget(self.plot_view)
        self.sortBox.addItems(self.sortkeys)
        self.colorBox.addItems(allcolormaps)
        #self.legend_checkBox.stateChanged.connect(self.toggle_legend)
        self.sortBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.colorBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.t0_edit.editingFinished.connect(self.update_params_and_redraw)
        self.t1_edit.editingFinished.connect(self.update_params_and_redraw)
        self.BP_checkBox.stateChanged.connect(self.update_params_and_redraw)
        self.stopped_checkbox.stateChanged.connect(self.update_params_and_redraw)
        self.update_params_and_redraw()
        self.show()

    def update_params_and_redraw(self):
        self.bp = self.BP_checkBox.isChecked()
        self.t0 = self.t0_edit.value()
        self.t1 = self.t1_edit.value()
        if self.thread is not None:
            return\

        self.sortkey = self.sortBox.currentText()
        params = (self.t0_edit.value(), self.t1_edit.value(),
                  self.BP_checkBox.isChecked(), self.stopped_checkbox.isChecked(),self.sortkey
                  )
        self.thread = QThread()
        self.worker = PlotWorker(self.DB, params)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.data_ready.connect(self.on_data_received)
        self.worker.data_ready.connect(self.thread.quit)
        self.worker.data_ready.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.cleanup_thread_ref)
        self.thread.start()

    def cleanup_thread_ref(self):
        """Reset the reference so the next update can start a new thread."""
        self.thread = None

    def handle_worker_error(self, error_msg):
        print(f"Worker Error: {error_msg}")
        # Use your logging system here

    @timer
    def on_data_received(self, df, stopped_df, keys):
        self.plot_view.clear()
        cmap_name = self.colorBox.currentText()
        colormap = cm.get_cmap(cmap_name)
        num_keys = len(keys)
        # Optional: Add IntCal background here if needed
        for i, key in enumerate(keys):
            color_idx = i / (num_keys - 1) if num_keys > 1 else 0.5
            rgba = colormap(color_idx)
            color = tuple(int(c * 255) for c in rgba[:3])
            print(color)
            data = df[key]
            y = data["d14C"]
            y_sig = data["d14C_sig"]
            years = 1950 - data["bp"]

            if self.bp:
                x = 1950 - years
            else:
                x = convertCalendarToBCE(years)
            err = pg.ErrorBarItem(x=x, y=y, height=y_sig * 2, beam=0.5, pen=pg.mkPen(color))
            self.plot_view.addItem(err)
            self.plot_view.plot(x, y, pen=None, symbol='o', symbolSize=7, symbolBrush=pg.mkBrush(color))

        if self.intcalData is not None:
            intcaldf = self.intcalData.copy()
            if not self.bp:
                intcaldf['Time'] = 1950 - intcaldf['Time']
            searcht0 = min(self.t0, self.t1)
            searcht1 = max(self.t0, self.t1)
            ind = where((intcaldf['Time'] > searcht0) & (intcaldf['Time'] < searcht1))[0]
            for key in intcaldf.keys():
                intcaldf[key] = intcaldf[key][ind]
            # Create the top and bottom bounds
            x = 1950 - intcaldf["years"] if self.bp else convertCalendarToBCE(intcaldf["years"])
            y=intcaldf["delta"]
            y_sig = intcaldf["delta_sig"]
            c_top = pg.PlotDataItem(x, y + y_sig)
            c_bottom = pg.PlotDataItem(x, y - y_sig)
            # Create the fill (light grey with transparency)
            fill = pg.FillBetweenItem(c_bottom, c_top, brush=(200, 200, 200, 100))
            self.plot_view.addItem(fill)
            # Optionally plot the center line

    def load_settings(self):
        settings = read_setttings_with_defaults('curve_settings', standardsettings)
        self.resize(*settings["window"]["size"])
        self.move(*settings["window"]["pos"])
        self.t0_edit.setValue(settings["t0"])
        self.t1_edit.setValue(settings["t1"])
        self.BP_checkBox.setChecked(settings["bp"])
        self.stopped_checkbox.setChecked(settings["stopped"])
        sortkey = settings["sortkey"]
        if settings["sortkey"] in self.sortkeys:
            self.sortBox.setCurrentIndex(self.sortkeys.index(sortkey))
        colormap = settings["colormap"]
        if colormap in allcolormaps:
            self.colorBox.setCurrentIndex(allcolormaps.index(colormap))

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
            "colormap": self.colorBox.currentText(),
            "legend": self.legend_checkBox.isChecked()
        }
        write_settings(settings, 'curve_settings')