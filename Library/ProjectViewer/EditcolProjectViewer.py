from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog,QAbstractItemView,QMessageBox, QTableView, QTableWidgetItem, QComboBox
from Library.comset import read_settings, write_settings
from Library.FrontendLogic.SearchCombobox import ExtendedComboBox
from numpy import array
from PyQt5.QtWidgets import QFileDialog
import os
from os.path import join

class WidgetDialog(QDialog):
    def __init__(self, path):
        super(WidgetDialog, self).__init__()
        loadUi(path, self)

class better_table_edit:
    def __init__(self,Mainwindow):
        self.window = Mainwindow
        self.settingsName = 'project_table_settings'
        self.__table = Mainwindow.table
        self.settings = ['Display Name','Format','Multiplier']
        self.N_settings = len(self.settings)
        self.model = self.window.model
        self.table_settings = read_settings(self.settingsName)
        self.columns = self.table_settings['columns']
        self.fill_tablevals()

        self.possible = Mainwindow.model.data.keys()
        self.selected = self.columns
        self.__show()

    def fill_tablevals(self):
        self.N_row = len(self.columns)
        row = ['                         ' for i in range(self.N_settings)]
        self.__tabledata = array([row for i in range(self.N_row)])
        for i, col in enumerate(self.columns):
            if col in self.table_settings.keys():
                for j, key in enumerate(self.settings):
                    self.__tabledata[i][j] = self.table_settings[col][key]
            else:
                for j, key in enumerate(self.settings):
                    if key == 'Display Name':
                        self.__tabledata[i][j] = col
                    if key == 'Format':
                        self.__tabledata[i][j] = '%s'
                    if key == 'Multiplier':
                        self.__tabledata[i][j] = None


    def __show(self):
        path = join('UIFiles','editcol.ui')
        self.mydialog = WidgetDialog(path)
        self.fill_table()

        self.mydialog.pB_Remove.clicked.connect(lambda: self.__remove(self.mydialog))
        self.mydialog.pB_Add.clicked.connect(lambda: self.__insert(self.mydialog))
        self.mydialog.pB_Up.clicked.connect(lambda: self.__shift(dir=-1))
        self.mydialog.pB_Down.clicked.connect(lambda: self.__shift(dir=1))

        self.mydialog.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mydialog.tableWidget.setSelectionMode(QTableView.ContiguousSelection)
        self.mydialog.Cancel_button.clicked.connect(self.cancel)
        self.mydialog.load_button.clicked.connect(self.load_table_settings)
        self.mydialog.save_button.clicked.connect(self.save_table_settings)
        self.mydialog.OK_button.clicked.connect(self.apply)
        self.mydialog.show()
        self.mydialog.exec_()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def cancel(self):
        self.mydialog.close()


    def check_settings(self):
        try:
            self.savesettings = read_settings(self.settingsName)
            self.new_settings = read_settings(self.settingsName)
            for i, col in enumerate(self.columns):
                self.new_settings[col] = {}
                self.new_settings[col]["Display Name"] = self.mydialog.tableWidget.item(i, 1).text()
                self.new_settings[col]["Format"] = self.mydialog.tableWidget.item(i, 2).text()
                mult = self.mydialog.tableWidget.item(i, 3).text()
                if mult == 'None':
                    self.new_settings[col]["Multiplier"] = None
                else:
                    self.new_settings[col]["Multiplier"] = float(mult)
                if "width" in self.new_settings[col].keys():
                    pass
                else:
                    self.new_settings[col]["width"] = 100

            self.new_settings['columns'] = self.columns
            write_settings(self.new_settings, self.settingsName)
            self.model.load_table_settings()
            self.model.layoutChanged.emit()
            return True, 'OK'
        except Exception as e:
            print(e)
            write_settings(self.savesettings, self.settingsName)
            self.model.load_table_settings()
            self.model.layoutChanged.emit()
            return False, e



    def apply(self):
        check, status = self.check_settings()
        if check:
            self.mydialog.close()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error")
            msg.setInformativeText(status)
            msg.setWindowTitle("Error")
            msg.exec_()
            print('Error:',status)

    def __remove(self, widget):
        for id in reversed(widget.tableWidget.selectionModel().selectedRows()):
            widget.tableWidget.removeRow(id.row())
            del self.cbs[id.row()]
            del self.columns[id.row()]

    def fill_table(self):
        self.mydialog.tableWidget.setRowCount(self.N_row)
        self.cbs = []
        for i, text in enumerate(self.selected):
            cb = ExtendedComboBox()
            cb.addItems(self.possible)
            self.mydialog.tableWidget.setCellWidget(i, 0, cb)
            index = cb.findText(text)
            if index >= 0: cb.setCurrentIndex(index)
            cb.currentIndexChanged.connect(self.DB_fieldchanged)
            self.cbs.append(cb)
        for row_number, col_data in enumerate(self.__tabledata):
            for col_number, data in enumerate(col_data):
                self.mydialog.tableWidget.setItem(int(row_number), int(col_number) + 1,
                                                  QTableWidgetItem(str(data)))

    def DB_fieldchanged(self):
        self.selected = []
        for cb in self.cbs:
            self.selected.append(cb.currentText())
        self.columns = []
        for disp_name in self.selected:
            self.columns.append(disp_name)
        self.fill_tablevals()
        self.fill_table()

    def __insert(self, widget):
        id = [i.row() for i in widget.tableWidget.selectionModel().selectedRows()]
        if not id: id = [widget.tableWidget.rowCount()-1]
        widget.tableWidget.insertRow(id[-1]+1)
        cb = ExtendedComboBox()
        cb.addItems(self.possible)
        cb.currentIndexChanged.connect(self.DB_fieldchanged)
        self.cbs.insert(id[-1]+1,cb)
        widget.tableWidget.setCellWidget(id[-1]+1, 0, cb)
        widget.tableWidget.setCurrentCell(id[-1], 0)
        widget.tableWidget.setCurrentCell(id[-1], 1)
        widget.tableWidget.setCurrentCell(id[-1], 2)
        self.DB_fieldchanged()

    def __shift(self, dir):
        table = self.mydialog.tableWidget
        idx = [i.row() for i in table.selectionModel().selectedRows()]
        if len(idx)==0:
            return
        if dir==-1 and idx[0]==0:
            return
        if dir==1 and idx[0]==len(self.columns)-1:
            return
        if dir==1 and idx[-1]==len(self.columns)-1:
            return
        print(table.columnCount())
        for id in idx:
            for i in range(1,table.columnCount()):
                cb1 = self.cbs[id]
                cb2 = self.cbs[id+dir]
                self.cbs[id+dir] = cb1
                self.cbs[id] = cb2
                s1 = table.takeItem(id, i)
                s2 = table.takeItem(id+dir, i)
                table.setItem(id+dir, i, s1)
                table.setItem(id, i, s2)
        self.DB_fieldchanged()
        table.selectRow(idx[-1] + dir)

    def load_table_settings(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self.mydialog, "QFileDialog.getOpenFileName()", "",
                                                  "json Files (*.json)", options=options)
        path = os.path.dirname(os.path.realpath(fileName))
        file = os.path.basename(fileName)
        if fileName:
            if file[-5:] == '.json':
                file = file[:-5]
            self.table_settings = read_settings(file, path=path)
            self.selected = self.table_settings['columns']
            self.columns = self.table_settings['columns']
            self.fill_tablevals()
            self.fill_table()

    def save_table_settings(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self.mydialog, "QFileDialog.getSaveFileName()", "",
                                                  "json Files (*.json)", options=options)
        path = os.path.dirname(os.path.realpath(fileName))
        file = os.path.basename(fileName)
        if fileName:
            self.new_settings = read_settings(self.settingsName)
            for i, col in enumerate(self.columns):
                self.new_settings[col] = {}
                self.new_settings[col]["Display Name"] = self.mydialog.tableWidget.item(i, 1).text()
                self.new_settings[col]["Format"] = self.mydialog.tableWidget.item(i, 2).text()
                mult = self.mydialog.tableWidget.item(i, 3).text()
                if mult == 'None':
                    self.new_settings[col]["Multiplier"] = None
                else:
                    self.new_settings[col]["Multiplier"] = float(mult)
                if "width" in self.new_settings[col].keys():
                    pass
                else:
                    self.new_settings[col]["width"] = 100

            self.new_settings['columns'] = self.columns
            if file[-5:] == '.json':
                file = file[:-5]
            write_settings(self.new_settings, file, path=path)