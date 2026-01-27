# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer

import math

from editor.basic_editor import BasicEditor
from editor.key_fade_manager import KeyFadeManager
from protocol.constants import VIAL_PROTOCOL_MATRIX_TESTER
from widgets.keyboard_widget import KeyboardWidget
from util import tr
from vial_device import VialKeyboard
from unlocker import Unlocker


class MatrixTest(BasicEditor):

    def __init__(self, layout_editor):
        super().__init__()

        self.layout_editor = layout_editor

        self.keyboardWidget = KeyboardWidget(layout_editor)
        self.keyboardWidget.set_enabled(False)

        self.unlock_btn = QPushButton("Unlock")
        self.reset_btn = QPushButton("Reset")
        self.fade_checkbox = QCheckBox(tr("MatrixTest", "Fade effect"))
        self.fade_checkbox.setToolTip(
            tr("MatrixTest", "When enabled, key highlights fade out after release")
        )

        self.fade_manager = KeyFadeManager(fade_duration=2.0)
        self.previous_pressed = {}

        layout = QVBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)

        self.addLayout(layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.unlock_lbl = QLabel(tr("MatrixTest", "Unlock the keyboard before testing:"))
        btn_layout.addWidget(self.unlock_lbl)
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.fade_checkbox)
        self.addLayout(btn_layout)

        self.keyboard = None
        self.device = None
        self.polling = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.matrix_poller)

        self.unlock_btn.clicked.connect(self.unlock)
        self.reset_btn.clicked.connect(self.reset_keyboard_widget)

        self.grabber = QWidget()

    def rebuild(self, device):
        super().rebuild(device)
        if self.valid():
            self.keyboard = device.keyboard

            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
        self.keyboardWidget.setEnabled(self.valid())

    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.vial_protocol >= VIAL_PROTOCOL_MATRIX_TESTER) and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

    def reset_keyboard_widget(self):
        self.fade_manager.reset()
        self.previous_pressed.clear()
        for w in self.keyboardWidget.widgets:
            w.setPressed(False)
            w.setOn(False)
            w.setHighlightIntensity(0.0)

        self.keyboardWidget.update_layout()
        self.keyboardWidget.update()
        self.keyboardWidget.updateGeometry()

    def matrix_poller(self):
        if not self.valid():
            self.timer.stop()
            return

        try:
            unlocked = self.keyboard.get_unlock_status(3)
        except (RuntimeError, ValueError):
            self.timer.stop()
            return

        if not unlocked:
            self.unlock_btn.show()
            self.unlock_lbl.show()
            return

        # we're unlocked, so hide unlock button and label
        self.unlock_btn.hide()
        self.unlock_lbl.hide()

        # Get size for matrix
        rows = self.keyboard.rows
        cols = self.keyboard.cols
        # Generate 2d array of matrix
        matrix = [[None] * cols for x in range(rows)]

        # Get matrix data from keyboard
        try:
            data = self.keyboard.matrix_poll()
        except (RuntimeError, ValueError):
            self.timer.stop()
            return

        # Calculate the amount of bytes belong to 1 row, each bit is 1 key, so per 8 keys in a row,
        # a byte is needed for the row.
        row_size = math.ceil(cols / 8)

        for row in range(rows):
            # Make slice of bytes for the row (skip first 2 bytes, they're for VIAL)
            row_data_start = 2 + (row * row_size)
            row_data_end = row_data_start + row_size
            row_data = data[row_data_start:row_data_end]

            # Get each bit representing pressed state for col
            for col in range(cols):
                # row_data is array of bytes, calculate in which byte the col is located
                col_byte = len(row_data) - 1 - math.floor(col / 8)
                # since we select a single byte as slice of byte, mod 8 to get nth pos of byte
                col_mod = (col % 8)
                # write to matrix array
                matrix[row][col] = (row_data[col_byte] >> col_mod) & 1

        # write matrix state to keyboard widget
        fade_enabled = self.fade_checkbox.isChecked()
        for w in self.keyboardWidget.widgets:
            if w.desc.row is not None and w.desc.col is not None:
                row = w.desc.row
                col = w.desc.col

                if row < len(matrix) and col < len(matrix[row]):
                    is_pressed = matrix[row][col]
                    was_pressed = self.previous_pressed.get(w, False)
                    w.setPressed(is_pressed)

                    if is_pressed:
                        w.setOn(True)
                        w.setHighlightIntensity(1.0)
                        self.fade_manager.stop_fade(w)
                    elif fade_enabled and was_pressed and not is_pressed:
                        self.fade_manager.start_fade(w)

                    self.previous_pressed[w] = is_pressed

        self.fade_manager.update()
        self.keyboardWidget.update()

    def unlock(self):
        Unlocker.unlock(self.keyboard)

    def activate(self):
        self.grabber.grabKeyboard()
        self.timer.start(20)

    def deactivate(self):
        self.grabber.releaseKeyboard()
        self.timer.stop()
