import serial
import serial.tools.list_ports
from Library.timer import timer

class USBConnector:
	def __init__(self):
		self.connection = self.getConnection()

	def getConnection(self):
		myports = [tuple(p) for p in list(serial.tools.list_ports.comports())]
		comport = None
		for port in myports:
			if 'USB VID:PID=0C2E:090A' in port[2]:
				comport = port[0]
		if comport is not None:
			try:
				connection = serial.Serial(port=comport, baudrate=9600, bytesize=8, timeout=2)
			except:
				connection = None
		else:
			connection = None
		return connection

	def checkConnection(self):
		if self.connection is None:
			self.connection = self.getConnection()


	def readLine(self):
		if self.connection is not None:
			if self.connection.is_open:
				try:
					line = self.connection.read(self.connection.in_waiting)
				except:
					line = None
					self.connection = None
			else:
				line= None
			return line