from Library.FrontendLogic.SearchCombobox import ExtendedComboBox
from PyQt5.QtWidgets import QMainWindow,QVBoxLayout, QGridLayout, QWidget,QFileDialog, QLineEdit,QMessageBox
from PyQt5.QtGui import QStandardItem, QPixmap, QIcon, QColor
from Library.comset import read_settings, write_settings
from PyQt5.uic import loadUi
from numpy import array, where
import os
from pathlib import Path
from json import dump as dump_js, load as load_js


class SettingsWindow(QMainWindow):
	def __init__(self,data,parent=None,path=Path('UIFiles/plotSettingsWindow.ui')):
		self.allcolors = ['orange', 'red', 'blue', 'green',
						  'mediumspringgreen', 'forestgreen', 'yellowgreen',
						  'khaki', 'darkorange', 'indianred']
		self.allforms = ['o','x', '^','s']
		self.makeColors()
		self.parent = parent
		super(QWidget, self).__init__(parent)
		loadUi(path, self)
		self.data = data
		self.datakeys = array([k for k in data.keys()])
		self.cancelButton.clicked.connect(self.cancel)
		self.displaySettings = array(self.datakeys)
		self.saveasButton.clicked.connect(self.saveAs)
		self.loadButton.clicked.connect(self.load_settings)
		self.possible_keys = array(self.datakeys)
		self.plotSettings = read_settings('proj_plot_Settings')
		self.get_Combobox_indexes()

		self.display_keys = array(self.datakeys)
		self.saveButton.clicked.connect(self.write_settings)
		self.xCombobox.addItems(self.possible_keys)
		self.xindex = self.xCombobox.findText(self.plotSettings['xkey'])
		self.xCombobox.setCurrentIndex(self.xindex)
		self.xCombobox.currentIndexChanged.connect(self.DBfield_changed)
		self.remove_button.clicked.connect(self.remove_row)
		self.grid_layout = QGridLayout()
		self.add_button.clicked.connect(self.add_row)
		self.xlabeledit.textEdited.connect(self.display_field_changed)
		self.xmin.textEdited.connect(self.display_field_changed)
		self.xmax.textEdited.connect(self.display_field_changed)
		self.yComboboxes = []
		self.colorboxes = []
		self.formboxes = []
		self.ylabel_fields = []
		self.y_min_lim_fields = []
		self.y_max_lim_fields = []
		self.n = 0
		for i in range(len(self.plotSettings['ykeys'])):
			self.add_row()
		self.settings_widget.setLayout(self.grid_layout)
		self.copySettings()
		self.xlabeledit.setText(self.parent.xlabel)
		self.xmin.setText(str(self.parent.xmin))
		self.xmax.setText(str(self.parent.xmax))
		for i, yBox in enumerate(self.yComboboxes):
			self.ylabel_fields[i].setText(self.parent.ylabels[i])

	def get_Combobox_indexes(self):
		self.init_indexes = []
		for key in self.plotSettings['ykeys']:
			self.init_indexes.append(where(self.possible_keys == key)[0][0])
		self.colorIndexes = []
		for color in self.plotSettings['ycolors']:
			for i, c in enumerate(self.allcolors):
				if color == c:
					self.colorIndexes.append(i)
					continue
		self.formIndexes = []
		for form in self.plotSettings['forms']:
			for i, f in enumerate(self.allforms):
				if form == f:
					self.formIndexes.append(i)
					continue

	def makeColors(self):
		self.colors  = []
		for color in self.allcolors:
			pixmap = QPixmap(10,10)
			pixmap.fill(QColor(color))
			icon = QIcon(pixmap)
			self.colors.append([icon,color])

	def add_row(self):
		if self.n<5:
			self.yComboboxes.append(ExtendedComboBox())
			self.formboxes.append(ExtendedComboBox())
			self.ylabel_fields.append(QLineEdit())
			self.y_min_lim_fields.append(QLineEdit())
			self.y_max_lim_fields.append(QLineEdit())
			self.colorboxes.append(ExtendedComboBox())
			self.grid_layout.addWidget(self.yComboboxes[-1], self.n, 0)
			self.grid_layout.addWidget(self.ylabel_fields[-1], self.n, 1)
			self.grid_layout.addWidget(self.y_min_lim_fields[-1], self.n, 2)
			self.grid_layout.addWidget(self.y_max_lim_fields[-1], self.n, 3)
			self.grid_layout.addWidget(self.colorboxes[-1], self.n, 4)
			self.grid_layout.addWidget(self.formboxes[-1], self.n, 5)
			self.yComboboxes[-1].addItems(self.possible_keys)
			model = self.formboxes[-1].model()
			for form in self.allforms:
				item = QStandardItem(form)
				item.setForeground(QColor('white'))
				pixmap = QPixmap()
				pixmap.load(str(Path('UIFiles/Symbols/'+form + '.png')))
				icon = QIcon()
				icon.addPixmap(pixmap)
				item.setIcon(icon)
				model.appendRow(item)
			for color in self.colors:
				self.colorboxes[-1].addItem(color[0],'')
			if self.n < len(self.plotSettings['ykeys']):
				self.yComboboxes[-1].setCurrentIndex(self.init_indexes[self.n])
				self.colorboxes[-1].setCurrentIndex(self.colorIndexes[self.n])
				self.formboxes[-1].setCurrentIndex(self.formIndexes[self.n])
				self.ylabel_fields[-1].setText(self.display_keys[self.yComboboxes[-1].currentIndex()])
				if self.yComboboxes[-1].currentText() in self.plotSettings['ykeys']:
					self.y_min_lim_fields[-1].setText(str(self.plotSettings['ymins'][self.n]))
					self.y_max_lim_fields[-1].setText(str(self.plotSettings['ymaxs'][self.n]))
				else:
					self.y_min_lim_fields[-1].setText('auto')
					self.y_max_lim_fields[-1].setText('auto')
			else:
				self.yComboboxes[-1].setCurrentIndex(1)
				self.ylabel_fields[-1].setText(self.display_keys[self.yComboboxes[-1].currentIndex()])
				self.y_min_lim_fields[-1].setText('auto')
				self.y_max_lim_fields[-1].setText('auto')
			self.yComboboxes[-1].currentIndexChanged.connect(self.DBfield_changed)
			self.y_min_lim_fields[-1].textEdited.connect(self.display_field_changed)
			self.colorboxes[-1].currentIndexChanged.connect(self.display_field_changed)
			self.formboxes[-1].currentIndexChanged.connect(self.display_field_changed)
			self.y_max_lim_fields[-1].textEdited.connect(self.display_field_changed)
			self.ylabel_fields[-1].textEdited.connect(self.display_field_changed)
			self.n += 1
		self.read_fields()
		self.parent.plot()


	def read_fields(self):
		self.parent.xkey = self.xCombobox.currentText()
		self.parent.xlabel = self.xlabeledit.text()
		try:
			self.parent.xlimmin = float(self.xmin.text())
		except:
			self.parent.xlimmin = self.xmin.text()
			if self.parent.xlimmin == 'auto':
				pass
			else:
				self.parent.xlimmin = 'auto'
		try:
			self.parent.xlimmax = float(self.xmax.text())
		except:
			self.parent.xlimmax = self.xmax.text()
			if self.parent.xlimmin == 'auto':
				pass
			else:
				self.parent.xlimmax = 'auto'
		self.parent.ykeys = []
		self.parent.ylabels = []
		self.parent.ymins = []
		self.parent.ymaxs = []
		self.parent.ycolors = []
		self.parent.forms = []
		for i, yBox in enumerate(self.yComboboxes):
			ykey = yBox.currentText()
			self.parent.ykeys.append(ykey)
			ylabel = self.ylabel_fields[i].text()
			self.parent.ylabels.append(ylabel)
			colorindex = self.colorboxes[i].currentIndex()
			self.parent.ycolors.append(self.colors[colorindex][1])
			form = self.formboxes[i].currentText()
			self.parent.forms.append(form)
			try:
				self.parent.ymins.append(float(self.y_min_lim_fields[i].text()))
			except:
				self.parent.ymins.append('auto')
			try:
				self.parent.ymaxs.append(float(self.y_max_lim_fields[i].text()))
			except:
				self.parent.ymaxs.append('auto')

	def copySettings(self):
		for key in self.plotSettings.keys():
			self.parent.__setattr__(key, self.plotSettings[key])

	def saveAs(self):
		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
												  "json Files (*.json)", options=options)
		path = os.path.dirname(os.path.realpath(fileName))
		file = os.path.basename(fileName)
		if fileName:
			if fileName[-5:] == '.json':
				pass
			else:
				fileName+='.json'

			self.read_fields()
			newsettings = self.overwrite_settings()
			with open(fileName, 'w') as outfile:
				dump_js(newsettings, outfile, indent=4)
			write_settings(newsettings, 'proj_plot_Settings')

	def overwrite_settings(self):
		newsettings = read_settings('proj_plot_Settings')
		for key in newsettings.keys():
			newsettings[key] = self.parent.__getattribute__(key)
		return newsettings

	def load_settings(self):
		try:
			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
													  "json Files (*.json)", options=options)
			path = os.path.dirname(os.path.realpath(fileName))
			file = os.path.basename(fileName)
			if fileName:
				with open(fileName, 'r') as outfile:
					self.plotSettings = load_js(outfile)
				self.plotSettings = self.plotSettings
		except Exception as e:
			self.plotSettings = read_settings('proj_plot_Settings')
		try:
			self.copySettings()
		except:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Critical)
			msg.setText("Error")
			msg.setInformativeText('The selected file has not the correct formating')
			msg.setWindowTitle("Error")
			msg.exec_()
			self.plotSettings = read_settings('proj_plot_Settings')
			self.copySettings()
		self.get_Combobox_indexes()
		self.xindex = self.xCombobox.findText(self.plotSettings['xkey'])
		self.xCombobox.setCurrentIndex(self.xindex)
		for i in range(self.n):
			self.yComboboxes[i].setParent(None)
			self.ylabel_fields[i].setParent(None)
			self.y_max_lim_fields[i].setParent(None)
			self.y_min_lim_fields[i].setParent(None)
			self.colorboxes[i].setParent(None)
			self.formboxes[i].setParent(None)
		self.n = 0
		self.yComboboxes = []
		self.ylabel_fields = []
		self.y_min_lim_fields = []
		self.y_max_lim_fields = []
		self.colorboxes = []
		self.formboxes = []
		self.xmin.setText(str(self.xmin))
		self.xmax.setText(str(self.xmax))
		for i in range(len(self.plotSettings['ykeys'])):
			self.add_row()
		for i, yBox in enumerate(self.yComboboxes):
			self.ylabel_fields[i].setText(self.parent.ylabels[i])

	def cancel(self):
		self.plotSettings = read_settings('proj_plot_Settings')
		self.copySettings()
		self.parent.load_plot_settings()
		self.parent.plot()
		self.close()

	def write_settings(self):
		self.read_fields()
		newsettings = self.overwrite_settings()
		write_settings(newsettings, 'proj_plot_Settings')
		self.close()


	def DBfield_changed(self):
		self.xlabeledit.setText(self.display_keys[self.xCombobox.currentIndex()])
		for i, yBox in enumerate(self.yComboboxes):
			self.ylabel_fields[i].setText(self.display_keys[yBox.currentIndex()])
		self.read_fields()
		self.parent.plot()

	def display_field_changed(self):
		self.read_fields()
		self.parent.plot()

	def remove_row(self):
		if self.n>1:
			self.grid_layout.removeWidget(self.yComboboxes[-1])
			self.n-=1
			self.yComboboxes[-1].setParent(None)
			self.colorboxes[-1].setParent(None)
			self.formboxes[-1].setParent(None)
			self.ylabel_fields[-1].setParent(None)
			self.y_max_lim_fields[-1].setParent(None)
			self.y_min_lim_fields[-1].setParent(None)
			del self.y_max_lim_fields[-1]
			del self.y_min_lim_fields[-1]
			del self.yComboboxes[-1]
			del self.colorboxes[-1]
			del self.ylabel_fields[-1]
			del self.formboxes[-1]
		self.read_fields()
		self.parent.plot()