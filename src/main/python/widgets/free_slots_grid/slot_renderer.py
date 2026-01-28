# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QPen


class SlotRenderer:
    """Renders free slots as small pale rectangles."""

    def __init__(self, slot_width=8.0, slot_height=6.0):
        self.slot_width = slot_width
        self.slot_height = slot_height
        self._setup_styles()

    def _setup_styles(self):
        """Setup brushes and pens for slot rendering."""
        self.fill_color = QColor(180, 180, 180, 40)  # Very pale light gray
        self.border_color = QColor(160, 160, 160, 60)  # Slightly darker border

        self.fill_brush = QBrush(self.fill_color)
        self.fill_brush.setStyle(Qt.SolidPattern)

        self.border_pen = QPen(self.border_color)
        self.border_pen.setWidthF(0.5)

    def render(self, painter, slots, scale=1.0):
        """Render all slots as small pale rectangles."""
        if not slots:
            return

        painter.save()
        painter.scale(scale, scale)
        painter.setRenderHint(painter.Antialiasing)

        painter.setPen(self.border_pen)
        painter.setBrush(self.fill_brush)

        for slot in slots:
            rect = slot.get_rect(self.slot_width, self.slot_height)
            painter.drawRect(rect)

        painter.restore()

    def set_slot_size(self, width, height):
        """Update the slot rectangle dimensions."""
        self.slot_width = width
        self.slot_height = height

    def set_colors(self, fill_color, border_color):
        """Update the rendering colors."""
        self.fill_color = fill_color
        self.border_color = border_color
        self._setup_styles()
