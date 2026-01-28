# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QBrush, QPen


class SlotRenderer:
    """Renders free slots as small pale rectangles."""

    def __init__(self, slot_width=8.0, slot_height=6.0):
        self.slot_width = slot_width
        self.slot_height = slot_height
        self._setup_styles()

    def _setup_styles(self):
        """Setup brushes and pens for slot rendering."""
        self.fill_color = QColor(180, 180, 180, 40)
        self.border_color = QColor(160, 160, 160, 60)

        self.fill_brush = QBrush(self.fill_color)
        self.fill_brush.setStyle(Qt.SolidPattern)

        self.border_pen = QPen(self.border_color)
        self.border_pen.setWidthF(0.5)

        self.canvas_pen = QPen(QColor(255, 100, 100, 150))
        self.canvas_pen.setWidthF(2.0)

    def render(self, painter, slots, scale=1.0, canvas_bounds=None):
        """Render all slots as small pale rectangles."""
        painter.save()
        painter.scale(scale, scale)
        painter.setRenderHint(painter.Antialiasing)

        if canvas_bounds:
            self._draw_canvas_border(painter, canvas_bounds)

        if slots:
            painter.setPen(self.border_pen)
            painter.setBrush(self.fill_brush)
            for slot in slots:
                rect = slot.get_rect(self.slot_width, self.slot_height)
                painter.drawRect(rect)

        painter.restore()

    def _draw_canvas_border(self, painter, bounds):
        """Draw the canvas boundary as a solid line."""
        painter.setPen(self.canvas_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(bounds)

    def set_slot_size(self, width, height):
        """Update the slot rectangle dimensions."""
        self.slot_width = width
        self.slot_height = height
