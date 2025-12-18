from PyQt5.Qt import QFont
from PyQt5.QtCore import *
from Library.timer import timer
from numpy import sort, array, where, nan
from Library.comset import read_settings,read_setttins_with_defaults
from Library.ProjectViewer.standardSettings import standard_table_settings

class MyTableModel(QAbstractTableModel):
	def __init__(self,table,DB,selectedProject,settingsname='project_table_settings',parent=None):
		QAbstractTableModel.__init__(self)
		self.setParent(table)
		self.Ncol, self.order = 0, 1
		self.DB = DB
		self.view = parent
		self.settingsName = settingsname
		self.selected_project = selectedProject
		self.load_table_settings()
		self.load_data(selectedProject)

	def redrawTable(self):
		self.load_table_settings()
		self.set_table_widths()
		self.layoutChanged.emit()
		self.set_fontsize()
		self.sort(self.Ncol,self.order)

	def set_fontsize(self):
		display_settings = read_settings('display_settings')
		fontsize = display_settings['fontsize']
		rowsize = int(fontsize * 2)
		font = QFont()
		font.setPointSize(fontsize)

		for i in range(self.nrows):
			self.parent().setRowHeight(i, rowsize)
		self.parent().setFont(font)

	def set_table_widths(self):
		for i, col in enumerate(self.columns):
			width = self.table_settings[col]['width']
			self.parent().setColumnWidth(i, width)
		self.parent().horizontalHeader().setStretchLastSection(True)

	def load_table_settings(self):
		self.table_settings = read_setttins_with_defaults(self.settingsName,standard_table_settings)
		self.fontsize = read_settings("display_settings")['fontsize']
		self.columns = self.table_settings['columns']
		self.headers = [self.table_settings[key]['Display Name'] for key in self.columns]
		self.ncol = len(self.headers)

	def clear_data_from_Nones(self):
		for key in self.data.keys():
			if None in self.data[key]:
				idx = where(self.data[key] == None)[0]
				self.data[key][idx] = nan
			try:
				self.data[key] = array(self.data[key],dtype=float)
			except:
				self.data[key] = array(self.data[key], dtype=str)

	def load_data(self,selectedProject):
		#query = "SELECT * FROM db_ams.target_v where db_ams.target_v.project_nr = %i;" % selectedProject
		query = read_settings('sql')['projectquery'] % selectedProject
		self.data = DB_call(self.DB, query)
		self.nrows = len(self.data['target_id'])
		self.clear_data_from_Nones()
		self.redrawTable()

	def data(self, index, role=Qt.DisplayRole):
		column = index.column()
		row = index.row()
		colkey = self.columns[column]
		if role == Qt.DisplayRole:
			factor = self.table_settings[colkey]['Multiplier']
			if factor is not None:
				try:
					return self.table_settings[colkey]['Format'] % self.data[colkey][row]*factor
				except:
					return self.table_settings[colkey]['Format'] % self.data[colkey][row]
			else:
				try:
					return self.table_settings[colkey]['Format'] % self.data[colkey][row]
				except:
					return self.data[colkey][row]
		elif role == 1:
			return self.data[colkey][row]
		return None

	def rowCount(self, parent=QModelIndex()):
		return len(self.data['target_id'])

	def headerData(self, col, orientation, role):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(self.headers[col])
		return QVariant()

	def columnCount(self,parent=QModelIndex()):
		return len(self.headers)

	def sort(self, Ncol, order):
		self.order = order
		self.Ncol = Ncol
		sort_column = self.columns[Ncol]
		self.sorted_ind = self.data[sort_column].argsort(kind='stable')
		if order == Qt.DescendingOrder:
			self.sorted_ind = self.sorted_ind[::-1]
		for key in self.data.keys():
			self.data[key] = self.data[key][self.sorted_ind]
		self.layoutChanged.emit()

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