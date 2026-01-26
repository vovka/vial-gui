"""Smooth dendron routing for combo visualization."""

import math

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath

ARC_RADIUS = 6.0
STEM_RATIO = 0.22
HANDLE_RATIO = 0.55
END_HANDLE_RATIO = 0.35


class ComboLineRouter:
    """Routes smooth dendrons between combo labels and keys."""

    def __init__(self, obstacles, avg_size):
        self.obstacles = obstacles
        self.avg_size = avg_size
        self.arc_radius = min(ARC_RADIUS, avg_size * 0.12)

    def create_path(self, start, end, combo_key_rects, alignment):
        """Create a smooth curve path from start to end."""
        path = QPainterPath()
        path.moveTo(start)

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.hypot(dx, dy)

        if distance < 0.1:
            return path

        if distance < self.arc_radius * 2:
            path.lineTo(end)
            return path

        stem_dir = self._alignment_vector(alignment, dx, dy)
        stem_len = max(self.avg_size * STEM_RATIO, self.arc_radius * 1.5)
        stem_point = QPointF(
            start.x() + stem_dir.x() * stem_len,
            start.y() + stem_dir.y() * stem_len,
        )
        path.lineTo(stem_point)

        ctrl1, ctrl2 = self._control_points(stem_point, end, stem_dir)
        path.cubicTo(ctrl1, ctrl2, end)
        return path

    def _alignment_vector(self, alignment, dx, dy):
        if alignment == 'top':
            return QPointF(0.0, 1.0)
        if alignment == 'bottom':
            return QPointF(0.0, -1.0)
        if alignment == 'left':
            return QPointF(1.0, 0.0)
        if alignment == 'right':
            return QPointF(-1.0, 0.0)
        magnitude = math.hypot(dx, dy)
        if magnitude == 0:
            return QPointF(0.0, 0.0)
        return QPointF(dx / magnitude, dy / magnitude)

    def _control_points(self, start, end, stem_dir):
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = math.hypot(dx, dy)
        if distance == 0:
            return start, end

        handle = min(distance * HANDLE_RATIO, self.avg_size * 1.1)
        end_handle = min(distance * END_HANDLE_RATIO, self.avg_size * 0.7)

        end_dir = QPointF(-dx / distance, -dy / distance)
        ctrl1 = QPointF(
            start.x() + stem_dir.x() * handle,
            start.y() + stem_dir.y() * handle,
        )
        ctrl2 = QPointF(
            end.x() + end_dir.x() * end_handle,
            end.y() + end_dir.y() * end_handle,
        )
        return ctrl1, ctrl2
