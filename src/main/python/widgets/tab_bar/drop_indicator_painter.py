# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtGui import QPainter, QPen

from widgets.tab_bar.constants import DROP_INDICATOR_COLOR, SWAP_HIGHLIGHT_COLOR


class DropIndicatorPainter:
    """Paints drop indicators for tab reordering."""

    def __init__(self, tab_bar):
        self._tab_bar = tab_bar

    def paint(self, drop_zone):
        """Paint drop indicator based on current drop zone."""
        if drop_zone.is_swap and drop_zone.target_index >= 0:
            self._paint_swap_highlight(drop_zone.target_index)
        elif drop_zone.indicator_index >= 0:
            self._paint_insert_indicator(drop_zone.indicator_index)

    def _paint_swap_highlight(self, target_index):
        painter = QPainter(self._tab_bar)
        painter.save()
        rect = self._tab_bar.tabRect(target_index)
        painter.fillRect(rect, SWAP_HIGHLIGHT_COLOR)
        pen = QPen(DROP_INDICATOR_COLOR, 2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.restore()

    def _paint_insert_indicator(self, indicator_index):
        painter = QPainter(self._tab_bar)
        painter.save()
        pen = QPen(DROP_INDICATOR_COLOR, 3)
        painter.setPen(pen)
        x = self._calculate_indicator_x(indicator_index)
        painter.drawLine(x, 0, x, self._tab_bar.height())
        painter.restore()

    def _calculate_indicator_x(self, indicator_index):
        if indicator_index < self._tab_bar.count():
            return self._tab_bar.tabRect(indicator_index).left()
        return self._tab_bar.tabRect(self._tab_bar.count() - 1).right()
