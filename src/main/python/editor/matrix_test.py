# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QWidget, QHBoxLayout, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer

import math

from editor.basic_editor import BasicEditor
from editor.key_fade_manager import KeyFadeManager
from editor.matrix_layer_manager import MatrixLayerManager
from protocol.constants import VIAL_PROTOCOL_MATRIX_TESTER
from widgets.keyboard_widget import KeyboardWidget
from widgets.square_button import SquareButton
from util import tr, KeycodeDisplay
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
        self.show_keycodes_checkbox = QCheckBox(tr("MatrixTest", "Show keycodes"))
        self.show_keycodes_checkbox.setToolTip(
            tr("MatrixTest", "Display actual keycodes on keys for the current layer")
        )
        self.show_keycodes_checkbox.setChecked(True)
        self.show_keycodes_checkbox.stateChanged.connect(self.on_show_keycodes_changed)

        self.fade_manager = KeyFadeManager(fade_duration=2.0)
        self.layer_manager = MatrixLayerManager()
        self.previous_pressed = {}

        self.layer_buttons = []
        self.layout_layers = QHBoxLayout()
        layer_label = QLabel(tr("MatrixTest", "Layer"))

        layout = QVBoxLayout()
        layout.addWidget(self.keyboardWidget)
        layout.setAlignment(self.keyboardWidget, Qt.AlignCenter)

        self.addLayout(layout)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(layer_label)
        btn_layout.addLayout(self.layout_layers)
        btn_layout.addStretch()
        self.unlock_lbl = QLabel(tr("MatrixTest", "Unlock the keyboard before testing:"))
        btn_layout.addWidget(self.unlock_lbl)
        btn_layout.addWidget(self.unlock_btn)
        btn_layout.addWidget(self.reset_btn)
        btn_layout.addWidget(self.fade_checkbox)
        btn_layout.addWidget(self.show_keycodes_checkbox)
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
            self.layer_manager.set_keyboard(self.keyboard)

            self.keyboardWidget.set_keys(self.keyboard.keys, self.keyboard.encoders)
            self.rebuild_layer_buttons()
            self.refresh_keycodes_display()
        self.keyboardWidget.setEnabled(self.valid())

    def rebuild_layer_buttons(self):
        for btn in self.layer_buttons:
            btn.hide()
            btn.deleteLater()
        self.layer_buttons = []

        for x in range(self.keyboard.layers):
            btn = SquareButton(str(x))
            btn.setFocusPolicy(Qt.NoFocus)
            btn.setRelSize(1.667)
            btn.setCheckable(True)
            btn.clicked.connect(lambda state, idx=x: self.switch_layer(idx))
            self.layout_layers.addWidget(btn)
            self.layer_buttons.append(btn)

        self.update_layer_buttons()

    def switch_layer(self, idx):
        self.layer_manager.current_layer = idx
        self.update_layer_buttons()
        self.refresh_keycodes_display()

    def update_layer_buttons(self):
        current = self.layer_manager.current_layer
        for idx, btn in enumerate(self.layer_buttons):
            btn.setEnabled(idx != current)
            btn.setChecked(idx == current)

    def refresh_keycodes_display(self):
        if not self.keyboard or not self.show_keycodes_checkbox.isChecked():
            self.clear_keycodes_display()
            return

        for widget in self.keyboardWidget.widgets:
            code = self.layer_manager.get_keycode_for_widget(widget)
            if code:
                KeycodeDisplay.display_keycode(widget, code)

        self.keyboardWidget.update()

    def clear_keycodes_display(self):
        for widget in self.keyboardWidget.widgets:
            widget.setText("")
            widget.setMaskText("")
            widget.setToolTip("")
            widget.masked = False
        self.keyboardWidget.update()

    def on_show_keycodes_changed(self, state):
        self.refresh_keycodes_display()

    def valid(self):
        # Check if vial protocol is v3 or later
        return isinstance(self.device, VialKeyboard) and \
               (self.device.keyboard and self.device.keyboard.vial_protocol >= VIAL_PROTOCOL_MATRIX_TESTER) and \
               ((self.device.keyboard.cols // 8 + 1) * self.device.keyboard.rows <= 28)

    def reset_keyboard_widget(self):
        self.fade_manager.reset()
        self.layer_manager.reset()
        self.previous_pressed.clear()
        for w in self.keyboardWidget.widgets:
            w.setPressed(False)
            w.setOn(False)
            w.setHighlightIntensity(0.0)

        self.update_layer_buttons()
        self.refresh_keycodes_display()
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
        layer_changed = False

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

                    # Detect layer key state changes
                    if is_pressed != was_pressed:
                        if self.layer_manager.process_key_press(w, is_pressed):
                            layer_changed = True

                    self.previous_pressed[w] = is_pressed

        self.fade_manager.update()

        if layer_changed:
            self.update_layer_buttons()
            self.refresh_keycodes_display()
        else:
            self.keyboardWidget.update()

    def unlock(self):
        Unlocker.unlock(self.keyboard)

    def activate(self):
        self.grabber.grabKeyboard()
        self.timer.start(20)

    def deactivate(self):
        self.grabber.releaseKeyboard()
        self.timer.stop()
