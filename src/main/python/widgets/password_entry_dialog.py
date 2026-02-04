# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt


class PasswordEntryDialog(QDialog):
    """Dialog for entering/editing a password for a password macro."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Password")
        self.setModal(True)
        self.setMinimumWidth(300)

        self._password = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Password field
        lbl_password = QLabel("Password:")
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("Enter password")
        self.txt_password.textChanged.connect(self._validate)

        # Confirm password field
        lbl_confirm = QLabel("Confirm password:")
        self.txt_confirm = QLineEdit()
        self.txt_confirm.setEchoMode(QLineEdit.Password)
        self.txt_confirm.setPlaceholderText("Confirm password")
        self.txt_confirm.textChanged.connect(self._validate)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("QLabel { color: red; }")

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addWidget(lbl_password)
        layout.addWidget(self.txt_password)
        layout.addWidget(lbl_confirm)
        layout.addWidget(self.txt_confirm)
        layout.addWidget(self.lbl_error)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _validate(self):
        password = self.txt_password.text()
        confirm = self.txt_confirm.text()

        if not password:
            self.lbl_error.setText("")
            self.btn_ok.setEnabled(False)
            return

        if password != confirm:
            self.lbl_error.setText("Passwords do not match")
            self.btn_ok.setEnabled(False)
            return

        self.lbl_error.setText("")
        self.btn_ok.setEnabled(True)

    def get_password(self) -> str:
        """Return the entered password."""
        return self.txt_password.text()
