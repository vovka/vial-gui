# SPDX-License-Identifier: GPL-2.0-or-later
from widgets.tab_bar.constants import SWAP_ZONE_RATIO


class DropZone:
    """Represents a calculated drop zone result."""

    def __init__(self, is_swap=False, target_index=-1, indicator_index=-1):
        self.is_swap = is_swap
        self.target_index = target_index      # For swap mode
        self.indicator_index = indicator_index  # For insert mode


class DropZoneCalculator:
    """Calculates drop zone (swap vs insert) based on cursor position."""

    def __init__(self, tab_bar):
        self._tab_bar = tab_bar

    def calculate(self, pos):
        """Calculate drop zone for the given position."""
        tab_index = self._tab_bar.tabAt(pos)
        if tab_index < 0:
            return self._end_zone()
        return self._calculate_for_tab(pos, tab_index)

    def _end_zone(self):
        """Return drop zone for dropping at the end."""
        return DropZone(indicator_index=self._tab_bar.count())

    def _calculate_for_tab(self, pos, tab_index):
        tab_rect = self._tab_bar.tabRect(tab_index)
        tab_center = tab_rect.center().x()
        swap_zone_margin = tab_rect.width() * SWAP_ZONE_RATIO

        if self._is_in_swap_zone(pos.x(), tab_center, swap_zone_margin):
            return DropZone(is_swap=True, target_index=tab_index)
        return self._insert_zone(pos.x(), tab_center, tab_index)

    def _is_in_swap_zone(self, x, center, margin):
        return abs(x - center) < margin

    def _insert_zone(self, x, tab_center, tab_index):
        if x < tab_center:
            return DropZone(indicator_index=tab_index)
        return DropZone(indicator_index=tab_index + 1)
