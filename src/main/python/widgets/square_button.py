# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QPushButton, QLabel, QHBoxLayout

class SquareButton(QPushButton):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scale = 1.2
        self.label = None
        self.word_wrap = False
        self.text = ""
        self.size_hint_base = None

    def setRelSize(self, ratio):
        self.scale = ratio
        self.updateGeometry()

    def setWordWrap(self, state):
        self.word_wrap = state
        self.setText(self.text)

    def sizeHint(self):
        base_height = self.size_hint_base if self.size_hint_base is not None else self.fontMetrics().height()
        size = int(round(base_height * self.scale))
        return QSize(size, size)

    # Override setText to facilitate automatic word wrapping
    def setText(self, text):
        self.text = text
        if self.word_wrap:
            super().setText("")
            if self.label is None:
                self.label = QLabel(text, self)
                self.label.setWordWrap(True)
                self.label.setAlignment(Qt.AlignCenter)
                layout = QHBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.label,0,Qt.AlignCenter)
            else:
                self.label.setText(text)
        else:
            if self.label is not None:
                self.label.hide()
                self.label.deleteLater()
            super().setText(text)

    def setSizeHintBase(self, base_height=None):
        if base_height is None:
            base_height = self.fontMetrics().height()
        self.size_hint_base = base_height
        self.updateGeometry()
