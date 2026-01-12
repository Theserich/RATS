from Library.comset import read_settings, write_settings
from os.path import join
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QComboBox,QApplication,QSizePolicy


def set_label_size(window,name,factor=1):
    fontsize = read_settings('display_settings')['fontsize'] * factor
    font = QFont()
    font.setPointSize(int(fontsize * 0.8))

    # Apply font to all labels from settings
    path = 'windowsizes'
    settings = read_settings(path)
    for label in settings[name]['labels']:
        if hasattr(window, label):
            window.__dict__[label].setFont(font)

    # For main window, adjust combos + group box
    if name == 'Mainwindow':
        combos = [
            window.ProjectNrBox,
            window.UserNrBox,
            window.ProjectNameBox,
            window.UserNameBox,
        ]
        for combo in combos:
            combo.setFont(font)
            # Let combo box resize automatically to its contents
            combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # Use sizeHint() instead of current width/height
        h = window.UserNrBox.sizeHint().height()
        w = window.UserNameBox.sizeHint().width()

        window.groupBox.setMaximumHeight(8 * h)
        window.groupBox.setMaximumWidth(5 * w)

    # Tell Qt to recalc the layout after font changes
    if window.layout():
        window.layout().activate()
