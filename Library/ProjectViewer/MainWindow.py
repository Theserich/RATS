from PyQt5.uic import loadUi
from PyQt5.Qt import QFont, Qt,QTimer
from Library.comset import read_settings, write_settings
from PyQt5.QtWidgets import QMenu
from numpy import array, where, nan
from Library.FrontendLogic.SearchCombobox import ExtendedComboBox
from Library.ProjectViewer.EditcolProjectViewer import better_table_edit
from Library.ProjectViewer.CopyPasteClass import CopySelectedCellsAction, copy_cells_to_clipboard
from Library.ProjectViewer.plotwindow import PlotWindow
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QCheckBox
from Library.ProjectViewer.model import MyTableModel
from Library.zoomAction import init_zoom_action
from Library.timer import timer
from Library.SignalEmitter import redrawSignal
from Library.ProjectViewer.Header import HeaderView
from Library.DBconnect.DBconnect import DBconnect
from Library.ProjectViewer.windowSizes import set_label_size,resize_window
from Library.ProjectViewer.USBConnector import USBConnector

standardSettings = {'startProj': [2913, 9214], 'DefMag': ['C200824NB', 'C14'], 'fontsize': 15, 'height': 25, 'windowheight': 1065, 'windowwidth': 1487, 'userbool':True}


class WidgetMain(QMainWindow):
	def __init__(self, path):
		self.settingsName = 'project_table_settings'
		super(WidgetMain, self).__init__()
		loadUi(path, self)
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

		self.grid_layout = QGridLayout()
		self.widget.setLayout(self.grid_layout)
		self.grid_layout.addWidget(self.UserNameBox, 0, 1)
		self.grid_layout.addWidget(self.user_checkbox, 0, 2)
		self.grid_layout.addWidget(self.UserNrBox, 0, 0)
		self.grid_layout.addWidget(self.ProjectNameBox, 1, 1)
		self.grid_layout.addWidget(self.ProjectNrBox, 1, 0)

		self.ProjectNameBox.currentIndexChanged.connect(lambda: self.project_field_changed(self.ProjectNameBox))
		self.ProjectNrBox.currentIndexChanged.connect(lambda: self.project_field_changed(self.ProjectNrBox))
		self.UserNrBox.currentIndexChanged.connect(lambda: self.user_field_changed(self.UserNrBox))
		self.UserNameBox.currentIndexChanged.connect(lambda: self.user_field_changed(self.UserNameBox))
		self.user_checkbox.toggled.connect(self.user_checkbox_toggled)
		ctrlc = CopySelectedCellsAction(self)
		self.addAction(ctrlc)
		self.model = MyTableModel(self.table, self.DB, self.start_proj_nr)
		self.table.setContextMenuPolicy(Qt.CustomContextMenu)
		self.table.customContextMenuRequested.connect(self.open_Menu)
		userindex = self.UserNrBox.findText(str(self.start_user_nr))
		self.UserNrBox.setCurrentIndex(userindex)
		#project_index = self.ProjectNrBox.findText(str(self.start_proj_nr))
		#print(project_index)
		#self.ProjectNrBox.setCurrentIndex(project_index)
		self.plotButton.clicked.connect(self.openPLotter)
		self.table.setModel(self.model)

		header = HeaderView(self.table)
		self.table.setHorizontalHeader(header)
		redrawSignal.signal.connect(self.model.redrawTable)
		redrawSignal.signal.connect(lambda: set_label_size(self,'Mainwindow'))
		redrawSignal.signal.connect(lambda: set_label_size(self,'Mainwindow'))
		self.model.redrawTable()
		h = self.UserNrBox.height()
		w = self.UserNameBox.width()

		self.groupBox.setMaximumHeight(8*h)
		self.groupBox.setMaximumWidth(5* w)
		self.projectLabel.setText(self.ProjectNameBox.currentText())
		self.searchButton.clicked.connect(self.searchSample)
		self.user_checkbox_toggled()
		set_label_size(self,'Mainwindow')

	def loadSettings(self):
		self.settings = read_settings('display_settings')
		if self.settings is None:
			self.settings = standardSettings
		for key in self.settings.keys():
			if key not in standardSettings:
				self.settings.pop(key)
		for key in standardSettings.keys():
			if key not in self.settings.keys():
				self.settings[key] = standardSettings[key]
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
		table_settings = read_settings(self.settingsName)
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
		print('test')
		self.projectLabel.setText(self.ProjectNameBox.currentText())

	def user_field_changed(self, combobox):
		if self.user_changing:
			return
		self.user_changing = True
		index = combobox.currentIndex()
		try:
			self.user_id = int(self.user_nr[index])
			self.UserNrBox.setCurrentIndex(index)
			self.UserNameBox.setCurrentIndex(index)
		except:
			pass
		project_indexes = where(self.projects['user_nr'] == self.user_id)[0]
		project_nrs = self.project_nr[project_indexes]
		project_names = self.project_names[project_indexes]
		self.ProjectNameBox.clear()
		self.ProjectNrBox.clear()
		self.ProjectNameBox.addItems(project_names)
		self.ProjectNrBox.addItems(project_nrs)
		try:
			self.selected_project = int(self.ProjectNrBox.currentText())
		except:
			self.selected_project = 0
		self.get_project_data()
		self.user_changing = False
		self.projectLabel.setText(self.ProjectNameBox.currentText())

	def project_field_changed(self, combobox):
		if self.user_changing:
			return
		if self.project_changing:
			return
		self.project_changing = True
		text = combobox.currentText()
		index = combobox.findText(text)
		self.ProjectNrBox.setCurrentIndex(index)
		self.ProjectNameBox.setCurrentIndex(index)
		try:
			self.selected_project = int(self.ProjectNrBox.currentText())
		except:
			self.selected_project = 0
		self.get_project_data()
		self.project_changing = False
		self.projectLabel.setText(self.ProjectNameBox.currentText())

	def get_project_data(self):
		savedata = read_settings('display_settings')
		savedata['startProj'] = [self.user_id,self.selected_project]
		write_settings(savedata,'display_settings')
		self.model.load_data(self.selected_project)


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


def get_all_projects(DB):
	query = 'SELECT * FROM db_ams.project_t;'
	data = DB_call(DB,query)
	return data


def get_all_Users(DB):
	query = 'SELECT * FROM db_ams.user_t;'
	data = DB_call(DB,query)
	return data


