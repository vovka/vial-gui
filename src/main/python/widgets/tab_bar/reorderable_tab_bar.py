# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtCore import pyqtSignal, Qt, QMimeData
from PyQt5.QtGui import QDrag

from widgets.tab_bar.constants import DRAG_START_DISTANCE
from widgets.tab_bar.free_slot_tab_bar import FreeSlotTabBar
from widgets.tab_bar.drop_zone_calculator import DropZone, DropZoneCalculator
from widgets.tab_bar.drop_indicator_painter import DropIndicatorPainter


class ReorderableTabBar(FreeSlotTabBar):
    """Tab bar with drag-and-drop reordering (insert and swap modes)."""

    tabs_reordered = pyqtSignal(int, int, bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self._drag_start_pos = None
        self._dragged_index = -1
        self._drop_zone = DropZone()
        self._zone_calculator = DropZoneCalculator(self)
        self._indicator_painter = DropIndicatorPainter(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self._dragged_index = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._should_start_drag(event):
            return super().mouseMoveEvent(event)
        self._execute_drag()

    def _should_start_drag(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return False
        if self._drag_start_pos is None or self._dragged_index < 0:
            return False
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        return distance >= DRAG_START_DISTANCE

    def _execute_drag(self):
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self._dragged_index))
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)
        self._reset_drag_state()

    def _reset_drag_state(self):
        self._drag_start_pos = None
        self._drop_zone = DropZone()
        self.update()

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if not event.mimeData().hasText():
            return
        self._drop_zone = self._zone_calculator.calculate(event.pos())
        self.update()
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._drop_zone = DropZone()
        self.update()

    def dropEvent(self, event):
        if not event.mimeData().hasText():
            return
        from_index = int(event.mimeData().text())
        self._emit_reorder_signal(from_index)
        self._drop_zone = DropZone()
        self.update()
        event.acceptProposedAction()

    def _emit_reorder_signal(self, from_index):
        if self._drop_zone.is_swap:
            self._emit_swap(from_index)
        else:
            self._emit_insert(from_index)

    def _emit_swap(self, from_index):
        to_index = self._drop_zone.target_index
        if to_index >= 0 and from_index != to_index:
            self.tabs_reordered.emit(from_index, to_index, True)

    def _emit_insert(self, from_index):
        to_index = self._drop_zone.indicator_index
        if to_index < 0:
            return
        if from_index < to_index:
            to_index -= 1
        if from_index != to_index:
            self.tabs_reordered.emit(from_index, to_index, False)

    def paintEvent(self, event):
        super().paintEvent(event)
        self._indicator_painter.paint(self._drop_zone)
