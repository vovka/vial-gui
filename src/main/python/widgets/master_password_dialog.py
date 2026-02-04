# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QCheckBox)
from PyQt5.QtCore import Qt


class MasterPasswordDialog(QDialog):
    """
    Dialog for master password entry.

    Has two modes:
    - Setup mode: For first-time setup, requires password confirmation
    - Unlock mode: For returning users, just needs password entry
    """

    MODE_SETUP = "setup"
    MODE_UNLOCK = "unlock"

    def __init__(self, parent=None, mode=MODE_UNLOCK):
        super().__init__(parent)
        self._mode = mode
        self._password = ""

        if mode == self.MODE_SETUP:
            self.setWindowTitle("Set Master Password")
        else:
            self.setWindowTitle("Unlock Password Session")

        self.setModal(True)
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()

        # Instructions
        if self._mode == self.MODE_SETUP:
            instructions = (
                "Set a master password to protect your password macros.\n"
                "This password will be required to unlock password macros\n"
                "each time you connect your keyboard."
            )
        else:
            instructions = (
                "Enter your master password to unlock password macros.\n"
                "Password macros cannot be used until unlocked."
            )

        lbl_instructions = QLabel(instructions)
        lbl_instructions.setWordWrap(True)
        layout.addWidget(lbl_instructions)

        # Password field
        lbl_password = QLabel("Master Password:")
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setPlaceholderText("Enter master password")
        self.txt_password.textChanged.connect(self._validate)
        self.txt_password.returnPressed.connect(self._on_return_pressed)

        layout.addWidget(lbl_password)
        layout.addWidget(self.txt_password)

        # Confirm password field (setup mode only)
        if self._mode == self.MODE_SETUP:
            lbl_confirm = QLabel("Confirm Password:")
            self.txt_confirm = QLineEdit()
            self.txt_confirm.setEchoMode(QLineEdit.Password)
            self.txt_confirm.setPlaceholderText("Confirm master password")
            self.txt_confirm.textChanged.connect(self._validate)
            self.txt_confirm.returnPressed.connect(self._on_return_pressed)
            layout.addWidget(lbl_confirm)
            layout.addWidget(self.txt_confirm)
        else:
            self.txt_confirm = None

        # Show password checkbox
        self.chk_show = QCheckBox("Show password")
        self.chk_show.stateChanged.connect(self._toggle_visibility)
        layout.addWidget(self.chk_show)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("QLabel { color: red; }")
        layout.addWidget(self.lbl_error)

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

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _toggle_visibility(self, state):
        mode = QLineEdit.Normal if state == Qt.Checked else QLineEdit.Password
        self.txt_password.setEchoMode(mode)
        if self.txt_confirm:
            self.txt_confirm.setEchoMode(mode)

    def _validate(self):
        password = self.txt_password.text()

        if not password:
            self.lbl_error.setText("")
            self.btn_ok.setEnabled(False)
            return

        if len(password) < 4:
            self.lbl_error.setText("Password must be at least 4 characters")
            self.btn_ok.setEnabled(False)
            return

        if self._mode == self.MODE_SETUP:
            confirm = self.txt_confirm.text() if self.txt_confirm else ""
            if password != confirm:
                self.lbl_error.setText("Passwords do not match")
                self.btn_ok.setEnabled(False)
                return

        self.lbl_error.setText("")
        self.btn_ok.setEnabled(True)

    def _on_return_pressed(self):
        if self.btn_ok.isEnabled():
            self.accept()

    def get_password(self) -> str:
        """Return the entered password."""
        return self.txt_password.text()

    def set_error(self, message: str):
        """Set an error message (e.g., for invalid password)."""
        self.lbl_error.setText(message)
