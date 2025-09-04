import sys
from copy import copy
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Library.comset import read_settings, write_settings

class HeaderView(QHeaderView):
    def __init__(self, table):
        super(HeaderView, self).__init__(Qt.Horizontal, table)
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.setMinimumSectionSize(10)


    def mouseReleaseEvent(self, event):
        model = self.parent().model()
        for i, col in enumerate(model.columns):
            width = self.parent().columnWidth(i)
            if width != model.table_settings[col]['width']:
                model.table_settings[col]['width'] = width
        write_settings(model.table_settings,model.settingsName)
        super(HeaderView, self).mouseReleaseEvent(event)

