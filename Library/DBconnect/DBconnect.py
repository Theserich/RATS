from xml.etree.ElementTree import parse, ElementTree, Element, SubElement
from base64 import b64decode, b64encode
from mysql.connector import connect, Error
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from os.path import dirname, abspath, join, exists
from os import makedirs
from PyQt5.QtWidgets import QApplication
import keyring
from Library.comset import read_settings
from PyQt5.QtWidgets import QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QGridLayout, QFormLayout, QWidget
from Library.timer import timer

# NEW: widgets used for dynamic host injection (safe even if you later edit the .ui)
from PyQt5.QtWidgets import QLabel, QLineEdit, QHBoxLayout, QVBoxLayout


class DBconnect():
    def __init__(self):
        self.sql_settings = read_settings('sql')
        self.__myhost = self.sql_settings.get('myhost', '')  # default '' if missing
        self.__ok = True
        self.__username, self.__password = '', ''
        self.__remember = False  # default

        # Load stored credentials (and host if previously remembered)
        self.__getCredentials()

    def getConnection(self):
        if self.__ok:
            try:
                cnx = connect(user=self.__username,
                              password=self.__password,
                              host=self.__myhost)
            except Error as err:
                # Error codes: 1045 = access denied, 1130 = host not allowed/connection issue, etc.
                if getattr(err, "errno", None) == 1045:
                    self.__showLoginWindow(warning='wrong username or password')
                elif getattr(err, "errno", None) == 1130:
                    self.__showLoginWindow(warning='no connection to DB')
                else:
                    self.__showLoginWindow(warning=f'unknown mysql.connector error: {getattr(err, "errno", "n/a")}')

                # If user pressed OK, optionally store credentials
                if self.__ok:
                    self.__storeCredentials()
                return self.getConnection()
            else:
                return cnx
        else:
            # user canceled
            self.__ok = True
            return None

    def __getCredentials(self):
        """Load username/password (and host if present) from system keyring."""
        # Username stored under fixed account 'username'
        stored_username = keyring.get_password("myapp-db", "username")
        if stored_username:
            self.__username = stored_username

            # Password stored under the username key
            stored_pw = keyring.get_password("myapp-db", self.__username)
            if stored_pw:
                self.__password = stored_pw

        # Host optionally stored under 'host'
        stored_host = keyring.get_password("myapp-db", "host")
        if stored_host:
            self.__myhost = stored_host  # override settings with remembered host

    def __storeCredentials(self):
        """Save username/password/host to system keyring if 'Remember' is checked."""
        if self.__remember:
            if self.__username:
                keyring.set_password("myapp-db", "username", self.__username)
                keyring.set_password("myapp-db", self.__username, self.__password or "")
            # Store host too so next time user gets the same host pre-filled
            if self.__myhost:
                keyring.set_password("myapp-db", "host", self.__myhost)

    def change_user(self):
        self.__username = ''
        self.__password = ''
        self.getConnection()

    def get_user(self):
        return self.__username

    def __showLoginWindow(self, warning):
        self.__ok = False
        self.__window = loadui(join("Library", "DBconnect", 'UILogin.ui'))

        # Show the warning in red text
        self.__window.label_warning.setText(
            '<html><head/><body><p align="center"><span style=" color:#c80000;">%s</span></p></body></html>' % warning
        )

        # Ensure we have a Host line edit (either from .ui or injected dynamically)
        self.__ensure_host_field(self.__window)

        # Pre-fill host / username / password
        self.__window.lineEdit_Host.setText(self.__myhost or "")
        self.__window.lineEdit_User.setText(self.__username or "")
        self.__window.lineEdit_PW.setText(self.__password or "")

        # Wire buttons
        self.__window.pushButton_OK.clicked.connect(self.__pressedOK)
        self.__window.pushButton_Cancel.clicked.connect(self.__pressedCancel)
        self.__window.lineEdit_User.returnPressed.connect(self.__pressedOK)
        self.__window.lineEdit_PW.returnPressed.connect(self.__pressedOK)
        self.__window.lineEdit_Host.returnPressed.connect(self.__pressedOK)

        # Show as modal dialog
        self.__window.show()
        self.__window.exec_()
        return None

    def __pressedOK(self):
        self.__username = self.__window.lineEdit_User.text().strip()
        self.__password = self.__window.lineEdit_PW.text()
        self.__myhost   = self.__window.lineEdit_Host.text().strip()
        # If the UI has a 'Remember' checkbox, keep using it
        if hasattr(self.__window, 'cB_Remember'):
            self.__remember = self.__window.cB_Remember.isChecked()
        self.__ok = True
        self.__window.close()

    def __pressedCancel(self):
        # keep __ok False (set before showing) so getConnection() returns None
        self.__window.close()

    def __ensure_host_field(self, dlg: QDialog):
        if hasattr(dlg, 'lineEdit_Host') and dlg.lineEdit_Host is not None:
            return
        layout = dlg.layout()
        if layout is None:
            # No layout at all: create a simple vertical layout
            layout = QVBoxLayout(dlg)
            dlg.setLayout(layout)
        lbl = QLabel("Host:", dlg)
        host_edit = QLineEdit(dlg)
        host_edit.setObjectName("lineEdit_Host")
        dlg.lineEdit_Host = host_edit
        row = QHBoxLayout()
        row.addWidget(lbl)
        row.addWidget(host_edit)
        if isinstance(layout, QFormLayout):
            if hasattr(layout, "insertRow"):
                layout.insertRow(0, lbl, host_edit)
            else:
                layout.addRow(lbl, host_edit)
        elif isinstance(layout, QGridLayout):
            # Append to the bottom row and span all columns (or 1 if unknown)
            r = layout.rowCount()
            try:
                cspan = max(1, layout.columnCount())
            except Exception:
                cspan = 1
            layout.addLayout(row, r, 0, 1, cspan)
        elif isinstance(layout, QVBoxLayout):
            layout.insertLayout(0, row)
        elif isinstance(layout, QHBoxLayout):
            layout.addWidget(lbl)
            layout.addWidget(host_edit)
        else:
            # Generic fallback:
            # Try to append the row; if that fails, wrap the old layout under a new VBox.
            try:
                layout.addLayout(row)  # works for many QLayout subclasses
            except AttributeError:
                # Last-resort: reparent the old layout under a container and install a new VBox on the dialog
                vbox = QVBoxLayout()
                vbox.addLayout(row)
                container = QWidget(dlg)
                # Move the existing layout into the container
                container.setLayout(layout)
                vbox.addWidget(container)
                dlg.setLayout(vbox)

    def set_stopped(self):
        self.__ok = False

def execute(self, query, parameters=None, multi=False):
        """
        Execute a query (or list of queries if multi=True).
        `parameters` can be a tuple for single query,
        or an iterable of tuples for multi=True.
        """
        cnx = self.getConnection()
        if cnx is None:
            # user cancelled or connection impossible right now
            return

        cursor = cnx.cursor()
        try:
            if multi:
                parameters = parameters or []
                for q, p in zip(query, parameters):
                    cursor.execute(q, tuple(p))
            else:
                cursor.execute(query, parameters or ())
            cnx.commit()
        finally:
            cursor.close()
            cnx.close()


class loadui(QDialog):
    def __init__(self, path):
        super().__init__()
        loadUi(path, self)
