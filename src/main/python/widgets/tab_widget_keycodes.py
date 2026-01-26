# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QTabWidget, QTabBar, QStyle, QStyleOptionTab, QStylePainter, QToolTip

from tabbed_keycodes import TabbedKeycodes


# Tab states
TAB_STATE_USED = 0        # Normal, configured and used
TAB_STATE_FREE = 1        # Empty/unconfigured (italic)
TAB_STATE_ATTENTION = 2   # Configured but needs attention (has "!" suffix)


class TabWidgetWithKeycodes(QTabWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabBar(FreeSlotTabBar())
        self.currentChanged.connect(self.on_changed)

    def mouseReleaseEvent(self, ev):
        TabbedKeycodes.close_tray()

    def on_changed(self, index):
        TabbedKeycodes.close_tray()

    def set_tab_label(self, index, text, is_free=False, needs_attention=False, attention_tooltip=None):
        """
        Set tab label with optional state indicators.

        Args:
            index: Tab index
            text: Tab label text
            is_free: If True, show as free/empty slot (italic text)
            needs_attention: If True, show "!" suffix to indicate needs attention
            attention_tooltip: Tooltip explaining why the item needs attention
        """
        self.setTabText(index, text)
        tab_bar = self.tabBar()
        if isinstance(tab_bar, FreeSlotTabBar):
            if is_free:
                tab_bar.set_tab_state(index, TAB_STATE_FREE)
            elif needs_attention:
                tab_bar.set_tab_state(index, TAB_STATE_ATTENTION, attention_tooltip)
            else:
                tab_bar.set_tab_state(index, TAB_STATE_USED)


class FreeSlotTabBar(QTabBar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tab_tooltips = {}
        self.setMouseTracking(True)

    def set_tab_free(self, index, is_free):
        """Legacy method for backward compatibility."""
        self.set_tab_state(index, TAB_STATE_FREE if is_free else TAB_STATE_USED)

    def set_tab_state(self, index, state, tooltip=None):
        """
        Set tab state and optional tooltip.

        Args:
            index: Tab index
            state: TAB_STATE_USED, TAB_STATE_FREE, or TAB_STATE_ATTENTION
            tooltip: Optional tooltip for attention state
        """
        self.setTabData(index, state)
        if tooltip:
            self._tab_tooltips[index] = tooltip
        elif index in self._tab_tooltips:
            del self._tab_tooltips[index]
        self.update()

    def event(self, event):
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.ToolTip:
            index = self.tabAt(event.pos())
            if index >= 0 and index in self._tab_tooltips:
                QToolTip.showText(event.globalPos(), self._tab_tooltips[index], self)
                return True
            else:
                QToolTip.hideText()
        return super().event(event)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()
        for index in range(self.count()):
            self.initStyleOption(option, index)
            painter.drawControl(QStyle.CE_TabBarTabShape, option)
            state = self.tabData(index)
            if state == TAB_STATE_FREE:
                # Free/empty slot - italic text
                painter.save()
                font = painter.font()
                font.setItalic(True)
                painter.setFont(font)
                try:
                    option.fontMetrics = QFontMetrics(font)
                except Exception:
                    pass
                painter.drawControl(QStyle.CE_TabBarTabLabel, option)
                painter.restore()
            elif state == TAB_STATE_ATTENTION:
                # Needs attention - add "!" suffix
                painter.save()
                original_text = option.text
                if not original_text.endswith("!"):
                    option.text = original_text + "!"
                painter.drawControl(QStyle.CE_TabBarTabLabel, option)
                painter.restore()
            else:
                # Normal used state
                painter.drawControl(QStyle.CE_TabBarTabLabel, option)
