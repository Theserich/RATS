from xml.etree.ElementTree import parse, ElementTree, Element, SubElement
from base64 import b64decode, b64encode
from mysql.connector import connect, Error
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from os.path import dirname, abspath, join, exists
from os import makedirs
from PyQt5.QtWidgets import QApplication
from sys import argv, exit
from Library.comset import read_settings
from Library.timer import timer


class DBconnect():
	def __init__(self):
		myhost = read_settings('sql')
		myhost = read_settings('sql')['myhost']
		self.__myhost = myhost
		self.__ok = True
		self.__username, self.__password = '', ''
		self.__path = join("Library","Settings", "cred.xml")
		self.__getCredentialsFromFile(self.__path)

	def getConnection(self):
		if self.__ok:
			try:
				cnx = connect(user=self.__username, password=self.__password, host=self.__myhost)
			except Error as err:
				if err.errno == 1045:
					self.__showLoginWindow(warning='wrong username or password')
				elif err.errno == 1130:
					self.__showLoginWindow(warning='no connection to DB')
				else:
					self.__showLoginWindow(warning='unknown mysql.connector error: %i' % err.errno)
				if self.__ok: self.__writeCredentialsToFile(file=self.__path)
				return self.getConnection()
			else:
				return cnx
		else:
			self.__ok = True
			return None

	def __showLoginWindow(self, warning):
		self.__ok = False
		#app = QApplication(argv)
		self.__window = loadui(join("Library", "DBconnect", 'UILogin.ui'))
		self.__window.label_warning.setText(
			'<html><head/><body><p align=\"center\"><span style=\" color:#c80000;\">%s</span></p></body></html>' % (
			warning,))
		self.__window.lineEdit_User.setText(self.__username)
		self.__window.lineEdit_PW.setText(self.__password)
		self.__window.pushButton_OK.clicked.connect(lambda: self.__pressedOK())
		self.__window.pushButton_Cancel.clicked.connect(lambda: self.__pressedCancel())
		self.__window.lineEdit_User.returnPressed.connect(lambda: self.__pressedOK())
		self.__window.lineEdit_PW.returnPressed.connect(lambda: self.__pressedOK())
		# capsloockevent
		# self.__window.lineEdit_User.keyPressEvent.connect(lambda: self.__keyup(warning = warning))
		self.__window.show()
		self.__window.exec_()
		return None

	def __pressedOK(self):
		self.__username = self.__window.lineEdit_User.text()
		self.__password = self.__window.lineEdit_PW.text()
		self.__remember = self.__window.cB_Remember.isChecked()
		self.__ok = True
		self.__window.close()

	def __pressedCancel(self):
		self.__window.close()

	def __keyup(self, warning):
		pass
		# if getModifierState("CapsLock"):
		#    self.__window.label_warning.setText('<html><head/><body><p align=\"center\"><span style=\" color:#c80000;\">Caps Lock on</span></p></body></html>')
		# else:
		#    self.__window.label_warning.setText('<html><head/><body><p align=\"center\"><span style=\" color:#c80000;\">%s</span></p></body></html>'%(warning,))
		# return None

	def __getCredentialsFromFile(self, file):
		try:
			configTree = parse(file)
			for login in configTree.iterfind('login'):
				self.__username = login.find("username").text
				self.__password = b64decode(login.find("password").text).decode()
		except:
			pass

	def get_possible_Isotopes(self):
		sql_settings = read_settings('sql')
		possibleISOS = []
		for ISO in sql_settings.keys():
			try:
				cnx = self.getConnection()
				cursor = cnx.cursor()
				cursor.execute(sql_settings[ISO]['TEST'])
				possibleISOS.append(ISO)
			except Exception as e:
				pass
		if cnx != None: cnx.close()
		return possibleISOS

	def change_user(self):
		self.__username=''
		self.__password = ''
		self.getConnection()

	def get_user(self):
		return self.__username

	def __writeCredentialsToFile(self, file):
		root = Element("config")
		login = SubElement(root, "login")
		SubElement(login, "username").text = self.__username
		if self.__remember: SubElement(login, "password").text = b64encode(self.__password.encode()).decode()
		tree = ElementTree(root)
		try:
			if not exists('Settings'): makedirs('Settings')
			print(file)
			tree.write(file)
		except:
			print("PASSINWRITE")
			pass

	def checkExisting(self,table,condition,parameters):
		cnx = self.getConnection()
		cursor = cnx.cursor()
		checkExistingQuery = "SELECT EXISTS(SELECT * FROM "+ table + " WHERE "+ condition+");"
		cursor.execute(checkExistingQuery,parameters)
		existing = bool(cursor.fetchall()[0][0])
		if cnx is None:
			return True
		cursor.close()
		if cnx != None: cnx.close()
		return existing

	def execute(self,query,parameters,multi=False):
		cnx = self.getConnection()
		cursor = cnx.cursor()
		#print(query)
		#print(parameters)
		if multi:
			for q,p in zip(query,parameters):
				cursor.execute(q, tuple(p))
		else:
			cursor.execute(query,parameters)
		if cnx is None:
			self.execute(self,query,parameters,multi=multi)
		cnx.commit()
		cursor.close()
		if cnx != None: cnx.close()



class loadui(QDialog):
	def __init__(self, path):
		super().__init__()
		loadUi(path, self)
