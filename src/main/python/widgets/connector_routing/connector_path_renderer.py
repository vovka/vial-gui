# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPainterPath


class ConnectorPathRenderer:
    """Renders connector paths as polylines with rounded corners."""

    def __init__(self, corner_radius=8.0):
        self.corner_radius = corner_radius

    def create_path(self, points):
        """Create a QPainterPath from a list of points with rounded corners."""
        if len(points) < 2:
            return QPainterPath()
        path = QPainterPath()
        path.moveTo(points[0])
        if len(points) == 2:
            path.lineTo(points[1])
            return path
        for i in range(1, len(points) - 1):
            prev_pt = points[i - 1]
            curr_pt = points[i]
            next_pt = points[i + 1]
            self._add_rounded_corner(path, prev_pt, curr_pt, next_pt)
        path.lineTo(points[-1])
        return path

    def _add_rounded_corner(self, path, prev_pt, curr_pt, next_pt):
        """Add a rounded corner at curr_pt between prev_pt and next_pt."""
        d1 = self._distance(prev_pt, curr_pt)
        d2 = self._distance(curr_pt, next_pt)
        radius = min(self.corner_radius, d1 / 2, d2 / 2)
        if radius < 1.0:
            path.lineTo(curr_pt)
            return
        v1 = self._normalize(prev_pt, curr_pt)
        v2 = self._normalize(next_pt, curr_pt)
        p1 = QPointF(curr_pt.x() + v1.x() * radius, curr_pt.y() + v1.y() * radius)
        p2 = QPointF(curr_pt.x() + v2.x() * radius, curr_pt.y() + v2.y() * radius)
        path.lineTo(p1)
        path.quadTo(curr_pt, p2)

    def _distance(self, p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

    def _normalize(self, from_pt, to_pt):
        """Return normalized direction vector from to_pt toward from_pt."""
        dx = from_pt.x() - to_pt.x()
        dy = from_pt.y() - to_pt.y()
        length = math.hypot(dx, dy)
        if length < 0.001:
            return QPointF(0, 0)
        return QPointF(dx / length, dy / length)
