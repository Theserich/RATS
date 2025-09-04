from PyQt5.QtWidgets import QAction, QTableWidget, QApplication
from PyQt5.QtCore import QMimeData, QByteArray
from PyQt5.QtGui import QPixmap, QImage, QClipboard, QPainter


class CopySelectedCellsAction(QAction):
	def __init__(self,widget):
		super(CopySelectedCellsAction, self).__init__("Copy", widget)
		self.setShortcut('Ctrl+C')
		self.triggered.connect(self.copy_cells_to_clipboard)
		self.table_widget = widget.tables
		self.widget=widget

	def copy_cells_to_clipboard(self):
		table_widget = self.table_widget[self.widget.tabWidget.currentIndex()]
		if len(table_widget.selectionModel().selectedIndexes()) > 0:
			# sort select indexes into rows and columns
			previous = table_widget.selectionModel().selectedIndexes()[0]
			columns = []
			rows = []
			for index in table_widget.selectionModel().selectedIndexes():
				if previous.row() != index.row():
					columns.append(rows)
					rows = []
				rows.append(index.data(role=1))
				previous = index
			columns.append(rows)
			clipboard = ""
			data = QMimeData()
			clipboard2 = QByteArray()
			ncols = len(columns[0])
			nrows = len(columns)
			images = []
			for r in range(nrows):
				for c in range(ncols):
					cell = columns[r][c]
					if type(cell) == QPixmap:
						clipboard += str(cell)
						clipboard2.append(str(cell))
						images.append(QImage(cell))
					else:
						clipboard += str(cell)
						clipboard2.append(str(cell))
					if c != (ncols-1):
						clipboard += '\t'
						clipboard2.append('\t')
				clipboard += '\n'
				if r != (nrows-1):
					clipboard2.append('\n')
			data.setData('text/plain',clipboard2)
			sys_clip = QApplication.clipboard()

			sys_clip.setMimeData(data)

