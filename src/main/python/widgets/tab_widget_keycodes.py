# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QTabWidget, QTabBar, QStyle, QStyleOptionTab, QStylePainter

from tabbed_keycodes import TabbedKeycodes


class TabWidgetWithKeycodes(QTabWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabBar(FreeSlotTabBar())
        self.currentChanged.connect(self.on_changed)

    def mouseReleaseEvent(self, ev):
        TabbedKeycodes.close_tray()

    def on_changed(self, index):
        TabbedKeycodes.close_tray()

    def set_tab_label(self, index, text, is_free=False):
        self.setTabText(index, text)
        tab_bar = self.tabBar()
        if isinstance(tab_bar, FreeSlotTabBar):
            tab_bar.set_tab_free(index, is_free)


class FreeSlotTabBar(QTabBar):

    def set_tab_free(self, index, is_free):
        self.setTabData(index, bool(is_free))
        self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOptionTab()
        for index in range(self.count()):
            self.initStyleOption(option, index)
            painter.drawControl(QStyle.CE_TabBarTabShape, option)
            if bool(self.tabData(index)):
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
            else:
                painter.drawControl(QStyle.CE_TabBarTabLabel, option)
