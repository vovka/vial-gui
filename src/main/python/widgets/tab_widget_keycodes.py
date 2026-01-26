# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtCore import pyqtSignal, Qt, QMimeData, QPoint
from PyQt5.QtGui import QFontMetrics, QDrag, QPainter, QColor, QPen
from PyQt5.QtWidgets import QTabWidget, QTabBar, QStyle, QStyleOptionTab, QStylePainter, QToolTip

from tabbed_keycodes import TabbedKeycodes


# Tab states
TAB_STATE_USED = 0        # Normal, configured and used
TAB_STATE_FREE = 1        # Empty/unconfigured (italic)
TAB_STATE_ATTENTION = 2   # Configured but needs attention (has "!" suffix)


class TabWidgetWithKeycodes(QTabWidget):

    # Signal emitted when tabs are reordered: (from_index, to_index, is_swap)
    # is_swap=True means swap mode (drop on tab), False means insert mode (drop between tabs)
    tabs_reordered = pyqtSignal(int, int, bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabBar(ReorderableTabBar())
        self.currentChanged.connect(self.on_changed)
        # Connect tab bar reorder signal
        self.tabBar().tabs_reordered.connect(self._on_tabs_reordered)

    def _on_tabs_reordered(self, from_index, to_index, is_swap):
        self.tabs_reordered.emit(from_index, to_index, is_swap)

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


class ReorderableTabBar(FreeSlotTabBar):
    """Tab bar that supports drag-and-drop reordering with two modes:
    - Insert mode: Drop between tabs to shift items
    - Swap mode: Drop on a tab to swap positions
    """

    # Signal: (from_index, to_index, is_swap)
    tabs_reordered = pyqtSignal(int, int, bool)

    # Drag threshold: minimum distance to move before starting a drag
    DRAG_START_DISTANCE = 10
    # Swap zone: middle portion of tab where dropping triggers swap mode (0.25 = middle 50%)
    SWAP_ZONE_RATIO = 0.25
    # Visual feedback colors
    DROP_INDICATOR_COLOR = QColor(0, 120, 215)
    SWAP_HIGHLIGHT_COLOR = QColor(0, 120, 215, 80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.drag_start_pos = None
        self.dragged_index = -1
        self.drop_indicator_index = -1  # For insert mode: position to insert
        self.drop_target_index = -1     # For swap mode: tab to swap with
        self.is_swap_mode = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
            self.dragged_index = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)
        if self.drag_start_pos is None:
            return super().mouseMoveEvent(event)
        if self.dragged_index < 0:
            return super().mouseMoveEvent(event)

        # Check if we've moved enough to start a drag
        if (event.pos() - self.drag_start_pos).manhattanLength() < self.DRAG_START_DISTANCE:
            return super().mouseMoveEvent(event)

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.dragged_index))
        drag.setMimeData(mime_data)

        # Execute drag
        drag.exec_(Qt.MoveAction)

        # Reset state
        self.drag_start_pos = None
        self.drop_indicator_index = -1
        self.drop_target_index = -1
        self.update()

    def mouseReleaseEvent(self, event):
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasText():
            return

        pos = event.pos()
        tab_index = self.tabAt(pos)

        # Determine if we're in swap mode or insert mode based on drop position
        if tab_index >= 0:
            tab_rect = self.tabRect(tab_index)
            tab_center = tab_rect.center().x()
            # Swap zone: middle 50% of the tab
            swap_zone_margin = tab_rect.width() * self.SWAP_ZONE_RATIO

            if abs(pos.x() - tab_center) < swap_zone_margin:
                # Swap mode: dropping on the tab
                self.is_swap_mode = True
                self.drop_target_index = tab_index
                self.drop_indicator_index = -1
            else:
                # Insert mode: dropping between tabs
                self.is_swap_mode = False
                self.drop_target_index = -1
                if pos.x() < tab_center:
                    self.drop_indicator_index = tab_index
                else:
                    self.drop_indicator_index = tab_index + 1
        else:
            # Dropping at the end
            self.is_swap_mode = False
            self.drop_target_index = -1
            self.drop_indicator_index = self.count()

        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drop_indicator_index = -1
        self.drop_target_index = -1
        self.update()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            return

        from_index = int(event.mimeData().text())

        if self.is_swap_mode and self.drop_target_index >= 0:
            # Swap mode
            to_index = self.drop_target_index
            if from_index != to_index:
                self.tabs_reordered.emit(from_index, to_index, True)
        elif self.drop_indicator_index >= 0:
            # Insert mode
            to_index = self.drop_indicator_index
            # Adjust for the fact that removing the source shifts indices
            if from_index < to_index:
                to_index -= 1
            if from_index != to_index:
                self.tabs_reordered.emit(from_index, to_index, False)

        self.drop_indicator_index = -1
        self.drop_target_index = -1
        self.is_swap_mode = False
        self.update()
        event.acceptProposedAction()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)

        # Draw drop indicator for insert mode
        if self.drop_indicator_index >= 0 and not self.is_swap_mode:
            painter.save()
            pen = QPen(self.DROP_INDICATOR_COLOR, 3)
            painter.setPen(pen)

            if self.drop_indicator_index < self.count():
                rect = self.tabRect(self.drop_indicator_index)
                x = rect.left()
            else:
                rect = self.tabRect(self.count() - 1)
                x = rect.right()

            painter.drawLine(x, 0, x, self.height())
            painter.restore()

        # Draw highlight for swap mode
        if self.drop_target_index >= 0 and self.is_swap_mode:
            painter.save()
            rect = self.tabRect(self.drop_target_index)
            painter.fillRect(rect, self.SWAP_HIGHLIGHT_COLOR)
            pen = QPen(self.DROP_INDICATOR_COLOR, 2)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()
