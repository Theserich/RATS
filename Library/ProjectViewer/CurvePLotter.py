from PyQt5.QtCore import QThread, pyqtSignal, QObject
import pyqtgraph as pg
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout
from PyQt5.uic import loadUi
from Library.timer import timer
from Library.helperFunctions import *
from pathlib import Path
from matplotlib import cm
from Library.comset import *
from numpy import array, sort, linspace, argsort, full, searchsorted, clip
from pandas import DataFrame
import numpy as np


class PlotWorker(QObject):
    data_ready = pyqtSignal(object, object, list)
    error = pyqtSignal(str)

    def __init__(self, db_instance, params):
        super().__init__()
        self.DB = db_instance
        self.params = params

    def run(self):
        try:
            t0, t1, bp, stopped_enabled, sortkey = self.params

            df = self.fetch_data(t0, t1, bp, stopped=False)
            df = calcD14C(df)

            stopped_df = None
            if stopped_enabled:
                stopped_df = self.fetch_data(t0, t1, bp, stopped=True)

            groupkey = sortkey + "_for_grouping"

            if sortkey in ("fm", "rel err", "bp"):
                N = 20
                arr = df[sortkey]
                minv = arr.min()
                maxv = arr.max()
                levels = linspace(minv, maxv, N)
                indices = searchsorted(levels, arr, side="right") - 1
                indices = clip(indices, 0, N - 1)
                df[groupkey] = levels[indices]
            else:
                df[groupkey] = df[sortkey]

            grouped_data = groupdf(df, sortkey=groupkey)
            sorted_keys = list(grouped_data.keys())

            self.data_ready.emit(grouped_data, stopped_df, sorted_keys)
        except Exception as e:
            self.error.emit(str(e))

    def fetch_data(self, t0, t1, bp, stopped):

        if bp:
            t0_ = t0
            t1_ = t1
        else:
            t0_ = 1950 - t0
            t1_ = 1950 - t1

        t0 = min(t0_, t1_)
        t1 = max(t0_, t1_)

        query = (
            f"SELECT sample_nr, target_nr, prep_nr, project, project_nr, magazine, user_label,"
            f"last_name, target_pressed, co2_final, cast(substring_index(user_label_nr,'|',1) as decimal(6,1)) as bp,"
            f"substring_index(user_label,'|',1) as treeid,"
            f"user_label_nr, c14_age, c14_age_sig, fm as fm, fm_sig as fm_sig, dc13, dc13_sig "
            f"FROM db_ams.target_v "
            f"WHERE research='calibration' "
            f"AND stop={int(stopped)} "
            f"AND c14_age IS NOT NULL "
            f"AND CONVERT(user_label_nr,UNSIGNED INTEGER) >= {t0} "
            f"AND CONVERT(user_label_nr,UNSIGNED INTEGER) <= {t1} "
            f"AND user_label != 'OXA 2'"
        )

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

        retdf['target_id'] = array([
            f"{i}.{j}.{k}"
            for i, j, k in zip(df['sample_nr'], df['prep_nr'], df['target_nr'])
        ])

        retdf = calcD14C(retdf)
        retdf['rel err'] = retdf['fm_sig'] / retdf['fm'] * 1000

        return retdf


sortkeys = ['sample_nr', 'target_nr', 'prep_nr', 'project', 'project_nr', 'magazine',
            'user_label', 'last_name', 'target_pressed', 'bp', 'treeid', 'user_label_nr',
            'c14_age', 'c14_age_sig', 'fm', 'fm_sig', 'dc13', 'dc13_sig', 'target_id',
            'co2_final', 'rel err']

allcolormaps = ['Set1', 'Reds', 'cool', 'coolwarm', 'gray', 'hot', 'hot_r', 'jet',
                'jet_r', 'nipy_spectral', 'nipy_spectral_r', 'ocean']

standardsettings = {
    'window': {'size': [2116, 1112], 'pos': [1717, 18]},
    't0': 1500,
    't1': 2000,
    'bp': False,
    'stopped': False,
    'sortkey': 'treeid',
    'colormap': 'nipy_spectral',
    'legend': True
}


class CurveWindow(QMainWindow):

    def __init__(self, path=Path("UIFiles/CalibrationPlot.ui"), parent=None):
        self.sortkeys = ['treeid', 'magazine', 'fm']
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

        self.sortBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.colorBox.currentIndexChanged.connect(self.update_params_and_redraw)
        self.legend_checkBox.stateChanged.connect(self.toggle_legend)
        self.t0_edit.editingFinished.connect(self.update_params_and_redraw)
        self.t1_edit.editingFinished.connect(self.update_params_and_redraw)
        self.BP_checkBox.stateChanged.connect(self.update_params_and_redraw)
        self.stopped_checkbox.stateChanged.connect(self.update_params_and_redraw)

        self.hover_text = None

        self.update_params_and_redraw()
        self.show()

    def toggle_legend(self):
        if self.legend_checkBox.isChecked():
            if not hasattr(self, "legend"):
                self.legend = self.plot_view.addLegend()
        else:
            if hasattr(self, "legend"):
                self.plot_view.removeItem(self.legend)
                del self.legend

    def update_params_and_redraw(self):
        if self.thread is not None:
            return

        params = (
            self.t0_edit.value(),
            self.t1_edit.value(),
            self.BP_checkBox.isChecked(),
            self.stopped_checkbox.isChecked(),
            self.sortBox.currentText()
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
        self.thread = None

    @timer
    def on_data_received(self, df, stopped_df, keys):
        self.plot_view.clear()
        self.plot_view.setUpdatesEnabled(False)

        cmap_name = self.colorBox.currentText()
        colormap = cm.get_cmap(cmap_name)

        if self.sortBox.currentText() in ("treeid", "project", "project_np"):
            bps = [df[key]['bp'].min() for key in df]
            sortind = argsort(bps)
            sortedkeys = [list(df.keys())[i] for i in sortind]
        else:
            sortedkeys = sort(keys)



        x_list, y_list, yerr_list, key_index_list = [], [], [], []

        for i, key in enumerate(sortedkeys):
            data = df[key]
            y = data["d14C"]
            y_sig = data["d14C_sig"]
            years = 1950 - data["bp"]

            if self.BP_checkBox.isChecked():
                x = 1950 - years
            else:
                x = convertCalendarToBCE(years)

            x_list.append(x)
            y_list.append(y)
            yerr_list.append(y_sig * 2)
            key_index_list.append(np.full(len(x), i))

        x_all = np.concatenate(x_list)
        y_all = np.concatenate(y_list)
        yerr_all = np.concatenate(yerr_list)
        key_idx_all = np.concatenate(key_index_list)

        colors = (colormap(key_idx_all / max(len(sortedkeys)-1, 1))[:, :3] * 255).astype(np.uint8)

        # ---- LEGEND SETUP ----
        if hasattr(self, "legend"):
            self.legend.clear()

        # Create representative items for legend (1 per group)
        representative_items = []
        start_idx = 0

        for i, key in enumerate(sortedkeys):
            # find correct representative color
            group_color = tuple(colors[start_idx])

            # create 1-point PlotDataItem for legend
            item = pg.PlotDataItem(
                x=[0], y=[0],
                pen=None,
                symbol='o',
                symbolBrush=pg.mkBrush(group_color),
                symbolSize=10,
                name=str(key)
            )

            representative_items.append(item)
            if hasattr(self, "legend"):
                self.legend.addItem(item, key)

            start_idx += len(df[key]["d14C"])

        # --- ERROR BARS RESTORED ---
        err = pg.ErrorBarItem(
            x=x_all,
            y=y_all,
            height=yerr_all,
            beam=0.4,
            pen=pg.mkPen((80, 80, 80), width=1)
        )
        self.plot_view.addItem(err)

        # --- POINTS WITH METADATA ---
        points = []
        total = len(x_all)

        points = []
        counter = 0
        for i, key in enumerate(sortedkeys):
            data = df[key]
            n = len(data["d14C"])
            for j in range(n):
                color = colors[counter]
                points.append({
                    "pos": (x_all[counter], y_all[counter]),
                    "size": 6,
                    "pen": None,
                    "brush": pg.mkBrush(tuple(color)),  # FIXED!
                    "data": {
                        "project": data["project"][j],
                        "user_label": data["user_label"][j],
                        "target_id": data["target_id"][j],
                        "magazine": data["magazine"][j],
                        "rel err": data["rel err"][j],
                        "co2_final": data["co2_final"][j],
                    }
                })

                counter += 1

        scatter = pg.ScatterPlotItem(
            points,
            hoverable=True,
            hoverPen=pg.mkPen('y', width=2),
            hoverBrush=pg.mkBrush(255, 255, 0, 120),
            symbolSize = 10
        )
        scatter.sigHovered.connect(self.on_point_hover)

        self.plot_view.addItem(scatter)
        self.plot_view.setUpdatesEnabled(True)

    def on_point_hover(self, scatter, points):
        if points.size == 0:
            return
        p = points[0]
        d = p.data()

        txt = (
            f"Project: {d['project']}\n"
            f"user label: {d['user_label']}\n"
            f"target_id: {d['target_id']}\n"
            f"Magazine: {d['magazine']}\n"
            f"relative err: {d['rel err']:.1f}‰\n"
            f"CO₂: {d['co2_final']}"
        )

        if self.hover_text:
            self.plot_view.removeItem(self.hover_text)

        self.hover_text = pg.TextItem(txt, anchor=(0, 1), color="black")
        self.plot_view.addItem(self.hover_text)
        self.hover_text.setPos(*p.pos())

    def load_settings(self):
        settings = read_setttings_with_defaults('curve_settings', standardsettings)
        self.resize(*settings["window"]["size"])
        self.move(*settings["window"]["pos"])
        self.t0_edit.setValue(settings["t0"])
        self.t1_edit.setValue(settings["t1"])
        self.BP_checkBox.setChecked(settings["bp"])
        self.stopped_checkbox.setChecked(settings["stopped"])

        sortkey = settings["sortkey"]
        if sortkey in self.sortkeys:
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