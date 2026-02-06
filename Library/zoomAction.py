from PyQt5.QtWidgets import QAction
from Library.comset import read_settings, write_settings
from Library.SignalEmitter import redrawSignal
from Library.timer import timer

@timer
def init_zoom_action(widget,plotwindow=False):
	zoom_in_Action = QAction('zoom',widget)
	zoom_in_Action.setShortcut('Ctrl++')
	zoom_out_Action = QAction('zoom', widget)
	zoom_out_Action.setShortcut('Ctrl+-')
	zoom_in_Action.triggered.connect(lambda : zoom(1))
	zoom_out_Action.triggered.connect(lambda: zoom(-1))
	widget.addAction(zoom_in_Action)
	widget.addAction(zoom_out_Action)


def zoom(incr):
	settings = read_settings('display_settings')
	fontsize = settings['fontsize']
	if fontsize>5: fontsize +=incr
	elif incr>0: fontsize +=incr
	settings['fontsize'] = fontsize
	write_settings(settings,'display_settings')
	redrawSignal.signal.emit()
