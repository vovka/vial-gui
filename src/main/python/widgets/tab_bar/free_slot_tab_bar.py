# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QTabBar, QStyle, QStyleOptionTab, QStylePainter, QToolTip

from widgets.tab_bar.constants import TAB_STATE_USED, TAB_STATE_FREE, TAB_STATE_ATTENTION


class FreeSlotTabBar(QTabBar):
    """Tab bar that displays free slots in italic and attention items with '!' suffix."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tab_tooltips = {}
        self.setMouseTracking(True)

    def set_tab_free(self, index, is_free):
        """Legacy method for backward compatibility."""
        self.set_tab_state(index, TAB_STATE_FREE if is_free else TAB_STATE_USED)

    def set_tab_state(self, index, state, tooltip=None):
        """Set tab state and optional tooltip."""
        self.setTabData(index, state)
        self._update_tooltip(index, tooltip)
        self.update()

    def _update_tooltip(self, index, tooltip):
        if tooltip:
            self._tab_tooltips[index] = tooltip
        elif index in self._tab_tooltips:
            del self._tab_tooltips[index]

    def event(self, event):
        if event.type() == QEvent.ToolTip:
            return self._handle_tooltip(event)
        return super().event(event)

    def _handle_tooltip(self, event):
        index = self.tabAt(event.pos())
        if index >= 0 and index in self._tab_tooltips:
            QToolTip.showText(event.globalPos(), self._tab_tooltips[index], self)
            return True
        QToolTip.hideText()
        return False

    def paintEvent(self, event):
        painter = QStylePainter(self)
        for index in range(self.count()):
            self._paint_tab(painter, index)

    def _paint_tab(self, painter, index):
        option = QStyleOptionTab()
        self.initStyleOption(option, index)
        painter.drawControl(QStyle.CE_TabBarTabShape, option)
        state = self.tabData(index)
        if state == TAB_STATE_FREE:
            self._paint_free_tab(painter, option)
        elif state == TAB_STATE_ATTENTION:
            self._paint_attention_tab(painter, option)
        else:
            painter.drawControl(QStyle.CE_TabBarTabLabel, option)

    def _paint_free_tab(self, painter, option):
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

    def _paint_attention_tab(self, painter, option):
        painter.save()
        if not option.text.endswith("!"):
            option.text = option.text + "!"
        painter.drawControl(QStyle.CE_TabBarTabLabel, option)
        painter.restore()
