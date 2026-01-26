# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTabWidget

from tabbed_keycodes import TabbedKeycodes
from widgets.tab_bar import (
    TAB_STATE_USED,
    TAB_STATE_FREE,
    TAB_STATE_ATTENTION,
    FreeSlotTabBar,
    ReorderableTabBar,
)


class TabWidgetWithKeycodes(QTabWidget):
    """Tab widget that closes keycode tray on interaction and supports reordering."""

    tabs_reordered = pyqtSignal(int, int, bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabBar(ReorderableTabBar())
        self.currentChanged.connect(self._on_changed)
        self.tabBar().tabs_reordered.connect(self._on_tabs_reordered)

    def _on_tabs_reordered(self, from_index, to_index, is_swap):
        self.tabs_reordered.emit(from_index, to_index, is_swap)

    def mouseReleaseEvent(self, ev):
        TabbedKeycodes.close_tray()

    def _on_changed(self, index):
        TabbedKeycodes.close_tray()

    def set_tab_label(self, index, text, is_free=False, needs_attention=False, attention_tooltip=None):
        """Set tab label with optional state indicators."""
        self.setTabText(index, text)
        tab_bar = self.tabBar()
        if isinstance(tab_bar, FreeSlotTabBar):
            state = self._determine_state(is_free, needs_attention)
            tooltip = attention_tooltip if needs_attention else None
            tab_bar.set_tab_state(index, state, tooltip)

    def _determine_state(self, is_free, needs_attention):
        if is_free:
            return TAB_STATE_FREE
        if needs_attention:
            return TAB_STATE_ATTENTION
        return TAB_STATE_USED
