import math
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath


class DendronRenderer:
    """Renders dendron lines connecting combo labels to keys with curved ends."""

    def __init__(self, bend_radius=12.0):
        self.bend_radius = bend_radius

    def find_closest_corner_point(self, rect, point):
        """Find point inside rect near closest corner, along diagonal."""
        corners = [
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.left(), rect.bottom()),
            QPointF(rect.right(), rect.bottom()),
        ]
        corner = min(corners, key=lambda c: self._distance(c, point))
        center = rect.center()
        dx = center.x() - corner.x()
        dy = center.y() - corner.y()
        inset_ratio = 0.2
        return QPointF(corner.x() + dx * inset_ratio, corner.y() + dy * inset_ratio)

    def create_dendron_path(self, start, end_corner, key_rect):
        """Create a path from start to end_corner with a curly hook bend."""
        path = QPainterPath()
        path.moveTo(start)

        approach = self._calculate_approach_point(end_corner, key_rect)
        path.lineTo(approach)
        ctrl = self._curve_control_point(approach, end_corner, key_rect)
        path.quadTo(ctrl, end_corner)
        return path

    def _distance(self, p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

    def _calculate_approach_point(self, corner, key_rect):
        """Calculate the approach point outside the key corner."""
        offset = self.bend_radius
        cx, cy = key_rect.center().x(), key_rect.center().y()

        if corner.x() < cx:
            ax = corner.x() - offset
        else:
            ax = corner.x() + offset

        if corner.y() < cy:
            ay = corner.y() - offset
        else:
            ay = corner.y() + offset

        return QPointF(ax, ay)

    def _curve_control_point(self, approach, corner, key_rect):
        """Calculate control point for the hook curve into the corner."""
        cx, cy = key_rect.center().x(), key_rect.center().y()

        if abs(corner.x() - approach.x()) > abs(corner.y() - approach.y()):
            ctrl_x = approach.x()
            ctrl_y = corner.y()
        else:
            ctrl_x = corner.x()
            ctrl_y = approach.y()

        return QPointF(ctrl_x, ctrl_y)
