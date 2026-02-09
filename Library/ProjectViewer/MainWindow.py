from PyQt5.uic import loadUi
from PyQt5.Qt import Qt,QTimer
from Library.comset import read_settings, write_settings, read_setttings_with_defaults
from PyQt5.QtWidgets import QMenu
from numpy import array, where
from Library.FrontendLogic.SearchCombobox import ExtendedComboBox
from Library.ProjectViewer.EditcolProjectViewer import better_table_edit
from Library.ProjectViewer.CopyPasteClass import CopySelectedCellsAction, copy_cells_to_clipboard
from Library.ProjectViewer.plotwindow import PlotWindow
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QCheckBox
from Library.ProjectViewer.model import MyTableModel
from Library.zoomAction import init_zoom_action
from Library.SignalEmitter import redrawSignal
from Library.ProjectViewer.Header import HeaderView
from Library.DBconnect.DBconnect import DBconnect
from Library.ProjectViewer.windowSizes import set_label_size
from Library.ProjectViewer.USBConnector import USBConnector
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from pandas import DataFrame
from Library.ProjectViewer.CurvePLotter import CurveWindow
from PyQt5.QtCore import QSignalBlocker
from Library.timer import timer
from Library.Settings.standardSettings import standard_display_settings, standard_table_settings
import logging
from Library.QtlogHandler import LoggerWindow





logger = logging.getLogger("project_viewer")

class WidgetMain(QMainWindow):
	@timer
	def __init__(self, path, qt_handler):
		self.settingsName = 'project_table_settings'
		super(WidgetMain, self).__init__()
		loadUi(path, self)
		self.loggerWindow = LoggerWindow(qt_handler, log_file="application.log", parent=self)
		self.actionShowLogs.triggered.connect(self.loggerWindow.show)
		self.DB = DBconnect()
		self.loadSettings()
		self.scanner = USBConnector()
		self.checkThreadTimer = QTimer(self)
		self.checkThreadTimer.setInterval(500)  # .5 seconds
		self.checkThreadTimer.timeout.connect(self.getConnectionLine)
		self.checkThreadTimer.start()

		self.user_changing = False
		self.project_changing = False
		self.projects = get_all_projects(self.DB)
		self.userdata = get_all_Users(self.DB)

		self.project_names = self.projects['project']
		self.project_nr = self.projects['project_nr']
		self.user_nr = self.userdata['user_nr']
		self.project_nr = array([str(i) for i in self.project_nr])
		self.user_nr = array([str(i) for i in self.user_nr])
		self.user = array(
			[str(j) + ' ' + str(k) for (j, k) in zip(self.userdata['first_name'], self.userdata['last_name'])])
		self.grid_layout = QGridLayout()
		self.user_id = int(self.user_nr[0])

		self.UserNrBox = ExtendedComboBox()
		self.UserNameBox = ExtendedComboBox()

		init_zoom_action(self)
		self.UserNrBox.addItems(self.user_nr)
		self.UserNameBox.addItems(self.user)
		self.editButton.clicked.connect(lambda: better_table_edit(self))
		self.widthButton.clicked.connect(self.autoAdjustWidths)

		self.user_checkbox = QCheckBox()
		self.user_checkbox.setChecked(self.settings['userbool'])
		self.ProjectNrBox = ExtendedComboBox()
		self.ProjectNameBox = ExtendedComboBox()

		self.ProjectNameBox.addItems(self.project_names)
		self.ProjectNrBox.addItems(self.project_nr)

		userindex = self.UserNrBox.findText(str(self.start_user_nr))
		self.user_id = self.start_user_nr
		self.UserNrBox.setCurrentIndex(userindex)
		self.UserNameBox.setCurrentIndex(userindex)
		projectindex = self.ProjectNrBox.findText(str(self.start_proj_nr))
		self.ProjectNrBox.setCurrentIndex(projectindex)
		self.ProjectNameBox.setCurrentIndex(projectindex)

		self.grid_layout = QGridLayout()
		self.widget.setLayout(self.grid_layout)
		self.grid_layout.addWidget(self.UserNameBox, 0, 1)
		self.grid_layout.addWidget(self.user_checkbox, 0, 2)
		self.grid_layout.addWidget(self.UserNrBox, 0, 0)
		self.grid_layout.addWidget(self.ProjectNameBox, 1, 1)
		self.grid_layout.addWidget(self.ProjectNrBox, 1, 0)


		self.model = MyTableModel(self.table, self.DB, self.start_proj_nr)

		self.plotButton.clicked.connect(self.openPLotter)
		self.curveButton.clicked.connect(lambda: CurveWindow(parent=self))
		self.actionSave_to_xlsx.triggered.connect(self.save_to_excel)
		self.table.setModel(self.model)

		header = HeaderView(self.table)
		self.table.setHorizontalHeader(header)
		redrawSignal.signal.connect(self.model.redrawTable)
		redrawSignal.signal.connect(lambda: set_label_size(self, 'Mainwindow'))
		redrawSignal.signal.connect(lambda: set_label_size(self, 'Mainwindow'))
		self.model.redrawTable()
		h = self.UserNrBox.height()
		w = self.UserNameBox.width()

		self.groupBox.setMaximumHeight(8 * h)
		self.groupBox.setMaximumWidth(5 * w)
		self.projectLabel.setText(self.ProjectNameBox.currentText())
		self.searchButton.clicked.connect(self.searchSample)
		if self.user_checkbox.isChecked():
			project_indexes = where(self.projects['user_nr'] == self.user_id)[0]
			project_nrs = self.project_nr[project_indexes]
			project_names = self.project_names[project_indexes]
			self.ProjectNameBox.clear()
			self.ProjectNrBox.clear()
			self.ProjectNameBox.addItems(project_names)
			self.ProjectNrBox.addItems(project_nrs)
			projectindex = self.ProjectNrBox.findText(str(self.start_proj_nr))
			self.ProjectNrBox.setCurrentIndex(projectindex)
			self.ProjectNameBox.setCurrentIndex(projectindex)
		else:
			self.UserNrBox.setEnabled(False)
			self.UserNameBox.setEnabled(False)
		set_label_size(self, 'Mainwindow')
		self.ProjectNameBox.currentIndexChanged.connect(lambda: self.project_field_changed(self.ProjectNameBox))
		self.ProjectNrBox.currentIndexChanged.connect(lambda: self.project_field_changed(self.ProjectNrBox))
		self.UserNrBox.currentIndexChanged.connect(lambda: self.user_field_changed(self.UserNrBox))
		self.UserNameBox.currentIndexChanged.connect(lambda: self.user_field_changed(self.UserNameBox))
		self.table.clicked.connect(self.model.tableClicked)
		self.user_checkbox.toggled.connect(self.user_checkbox_toggled)
		ctrlc = CopySelectedCellsAction(self)
		self.addAction(ctrlc)
		self.table.setContextMenuPolicy(Qt.CustomContextMenu)
		self.table.customContextMenuRequested.connect(self.open_Menu)
		logger.info("ProjectViewer started")



	def save_to_excel(self):
		# Open save dialog
		file_path, _ = QFileDialog.getSaveFileName(
			self,
			"Save as Excel",
			"",
			"Excel Files (*.xlsx);;All Files (*)"
		)
		if not file_path:  # user cancelled
			return
		try:
			# Convert dict -> DataFrame -> Excel
			datadict = self.model.data.copy()
			exceldata = {}
			for i, column in enumerate(self.model.columns):
				exceldata[self.model.headers[i]] = datadict[column]
			df = DataFrame.from_dict(exceldata)
			df.to_excel(file_path, index=False)
			QMessageBox.information(self, "Success", f"Data saved to:\n{file_path}")
		except Exception as e:
			QMessageBox.critical(self, "Error", f"Failed to save Excel file:\n{e}")


	def loadSettings(self):
		self.settings = read_setttings_with_defaults('display_settings', standard_display_settings)
		for key in self.settings.keys():
			if key not in standard_display_settings:
				self.settings.pop(key)
		for key in standard_display_settings.keys():
			if key not in self.settings.keys():
				self.settings[key] = standard_display_settings[key]
		[self.start_user_nr, self.start_proj_nr] = self.settings['startProj']
		self.selected_project = int(self.start_proj_nr)
		height = self.settings['windowheight']
		width = self.settings['windowwidth']
		self.resize(width,height)


	def showEvent(self, event):
		super().showEvent(event)
		# Connect screenChanged once, after the window handle exists
		handle = self.windowHandle()
		if handle and not hasattr(self, '_screen_changed_connected'):
			handle.screenChanged.connect(
				lambda screen: set_label_size(self, 'Mainwindow')
			)
			self._screen_changed_connected = True


	def getConnectionLine(self):
		self.scanner.checkConnection()
		sample = self.scanner.readLine()
		if sample is not None:
			sample = sample.decode("utf-8")
			if sample != '':
				self.sampleEdit.setText(sample)
				self.searchSample()

	def searchSample(self):
		samplenr = self.sampleEdit.text()
		samplenr.replace(" ", "")
		samplenr = samplenr.split('.')[0]
		target_id = str(samplenr)+'.1.1'
		project_nr,user_nr = self.get_project_nr(target_id)
		userindex = self.UserNrBox.findText(str(user_nr))

		self.UserNrBox.setCurrentIndex(userindex)
		project_index = self.ProjectNrBox.findText(str(project_nr))
		self.ProjectNrBox.setCurrentIndex(project_index)

	def autoAdjustWidths(self):
		self.table.resizeColumnsToContents()
		self.table.horizontalHeader().setStretchLastSection(True)
		self.change_width_settings()

	def closeEvent(self, event):
		w = self.width()
		h = self.height()
		self.settings = read_settings('display_settings')
		self.settings['windowheight'] = h
		self.settings['windowwidth'] = w
		self.settings['startProj'] = [self.user_id, self.selected_project]
		self.settings['userbool'] = self.user_checkbox.isChecked()
		write_settings(self.settings, 'display_settings')
		redrawSignal.signal.disconnect(self.model.redrawTable)
		super().closeEvent(event)

	def change_width_settings(self):
		table_settings = read_setttings_with_defaults(self.settingsName, standard_table_settings)
		for i, col in enumerate(self.model.columns):
			width = self.table.columnWidth(i)
			table_settings[col]['width'] = width
		write_settings(table_settings, self.settingsName)

	def open_Menu(self, event):
		menu = QMenu()
		clear_action = menu.addAction("Clear Selection")
		plot_action = menu.addAction("Plot selected")
		copy_action = menu.addAction("Copy")
		action = menu.exec_(self.table.mapToGlobal(event.__pos__()))
		if action == clear_action:
			self.table.clearSelection()
		elif action == copy_action:
			copy_cells_to_clipboard(self.table)
		elif action == plot_action:
			self.plot_selected()

	def plot_selected(self):
		ind = []
		if len(self.table.selectionModel().selectedIndexes()) > 0:
			previous = self.table.selectionModel().selectedIndexes()[0]
			ind.append(previous.row())
			for index in self.table.selectionModel().selectedIndexes():
				row = index.row()
				if previous.row() != row:
					ind.append(row)
				previous = index
			ind = array(ind)
			plotdata = {}
			for key in self.model.data.keys():
				plotdata[key] = self.model.data[key][ind]
			self.plotWindow = PlotWindow(plotdata, parent=self)
			self.plotWindow.show()

	def openPLotter(self):
		self.plotWindow = PlotWindow(self.model.data, parent=self)
		self.plotWindow.show()

	def user_checkbox_toggled(self):
		checked = self.user_checkbox.isChecked()
		self.UserNrBox.setEnabled(checked)
		self.UserNameBox.setEnabled(checked)
		if checked:
			self.user_field_changed(self.UserNrBox)
		else:
			self.user_changing = True
			projectname = self.ProjectNameBox.currentText()
			projectnr = self.ProjectNrBox.currentText()
			self.ProjectNameBox.clear()
			self.ProjectNrBox.clear()
			self.ProjectNameBox.addItems(self.project_names)
			self.ProjectNrBox.addItems(self.project_nr)
			nameindex = self.ProjectNameBox.findText(projectname)
			nrindex = self.ProjectNrBox.findText(projectnr)
			self.ProjectNameBox.setCurrentIndex(nameindex)
			self.ProjectNrBox.setCurrentIndex(nrindex)
			self.user_changing = False
		self.projectLabel.setText(self.ProjectNameBox.currentText())

	def user_field_changed(self, combobox):
		if self.user_changing:
			return

		self.user_changing = True

		try:
			index = combobox.currentIndex()
			if index < 0:
				self.user_changing = False
				return

			# Update user id
			self.user_id = int(self.user_nr[index])

			# Sync both user comboboxes without triggering signals
			with QSignalBlocker(self.UserNrBox), QSignalBlocker(self.UserNameBox):
				self.UserNrBox.setCurrentIndex(index)
				self.UserNameBox.setCurrentIndex(index)

			# Filter projects belonging to this user
			project_indexes = where(self.projects['user_nr'] == self.user_id)[0]
			project_nrs = self.project_nr[project_indexes]
			project_names = self.project_names[project_indexes]

			# Repopulate project comboboxes safely
			with QSignalBlocker(self.ProjectNameBox), QSignalBlocker(self.ProjectNrBox):
				self.ProjectNameBox.clear()
				self.ProjectNrBox.clear()
				self.ProjectNameBox.addItems(project_names)
				self.ProjectNrBox.addItems(project_nrs)

				# Try to keep previous project if possible
				if len(project_nrs) > 0:
					self.ProjectNrBox.setCurrentIndex(0)
					self.ProjectNameBox.setCurrentIndex(0)
					self.selected_project = int(self.ProjectNrBox.currentText())
				else:
					self.selected_project = 0

			# Load project data
			self.get_project_data()

			self.projectLabel.setText(self.ProjectNameBox.currentText())

		except Exception as e:
			logger.exception("Error in project_field_changed")

		self.user_changing = False

	@timer
	def project_field_changed(self, combobox):
		if self.user_changing or self.project_changing:
			return
		self.project_changing = True
		try:
			text = combobox.currentText()
			index = combobox.findText(text)

			if index < 0:
				self.project_changing = False
				return
			# Sync both project comboboxes safely
			with QSignalBlocker(self.ProjectNrBox), QSignalBlocker(self.ProjectNameBox):
				self.ProjectNrBox.setCurrentIndex(index)
				self.ProjectNameBox.setCurrentIndex(index)
			# Update selected project
			try:
				self.selected_project = int(self.ProjectNrBox.currentText())
			except:
				self.selected_project = 0
			projindex = where(self.projects['project_nr'] == self.selected_project)[0]
			if len(projindex) > 0:
				projindex = projindex[0]
				usernr = self.projects['user_nr'][projindex]

				userindex = self.UserNrBox.findText(str(usernr))
				if userindex >= 0:
					with QSignalBlocker(self.UserNrBox), QSignalBlocker(self.UserNameBox):
						self.UserNrBox.setCurrentIndex(userindex)
						self.UserNameBox.setCurrentIndex(userindex)
					self.user_id = int(usernr)
			self.get_project_data()
			self.projectLabel.setText(self.ProjectNameBox.currentText())
		except Exception as e:
			logger.exception("Error in project_field_changed")
		self.project_changing = False

	@timer
	def get_project_data(self):
		savedata = read_settings('display_settings')
		savedata['startProj'] = [self.user_id,self.selected_project]
		write_settings(savedata,'display_settings')
		self.model.load_data(self.selected_project)

	@timer
	def get_project_nr(self, target_id):
		query = "SELECT db_ams.target_v.project_nr, db_ams.target_v.user_nr FROM db_ams.target_v where db_ams.target_v.sample_id = '"+ str(target_id)+"';"
		cnx = self.DB.getConnection()
		if cnx is None:
			return
		project_nr = 1
		user_nr = 1
		cursor = cnx.cursor()
		cursor.execute(query)
		b = cursor.fetchall()
		a = array(b).T
		if a.size != 0:
			for i, colname in enumerate([name[0] for name in cursor.description]):
				if colname == 'project_nr':
					project_nr = a[i][0]
				if colname == 'user_nr':
					user_nr = a[i][0]
		if cnx is None:
			return
		cursor = cnx.cursor()
		cursor.close()
		if cnx != None: cnx.close()
		return project_nr,user_nr

def DB_call(DB,query,parameters=None):
	result = {}
	cnx = DB.getConnection()
	if cnx is None:
		return
	cursor = cnx.cursor()
	if parameters is None:
		cursor.execute(query)
	else:
		cursor.execute(query,parameters)
	b = cursor.fetchall()
	a = array(b).T
	if a.size != 0:
		for i, colname in enumerate([name[0] for name in cursor.description]):
			result[str(colname)] = a[i]
	else:
		for i, colname in enumerate([name[0] for name in cursor.description]):
			result[str(colname)] = array([])
	cursor.close()
	if cnx != None: cnx.close()
	return result

@timer
def get_all_projects(DB):
	query = 'SELECT * FROM db_ams.project_t;'
	data = DB_call(DB,query)
	return data


def get_all_Users(DB):
	query = 'SELECT * FROM db_ams.user_t;'
	data = DB_call(DB,query)
	return data


