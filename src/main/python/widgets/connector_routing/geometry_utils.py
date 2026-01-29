# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF


class GeometryUtils:
    """Utility functions for geometry calculations."""

    @staticmethod
    def distance(p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

    @staticmethod
    def line_intersects_rect(p1, p2, rect, margin=2.0):
        """Check if line segment intersects rectangle with margin."""
        expanded = rect.adjusted(-margin, -margin, margin, margin)
        if expanded.contains(p1) or expanded.contains(p2):
            return True
        edges = [
            (QPointF(expanded.left(), expanded.top()),
             QPointF(expanded.right(), expanded.top())),
            (QPointF(expanded.right(), expanded.top()),
             QPointF(expanded.right(), expanded.bottom())),
            (QPointF(expanded.right(), expanded.bottom()),
             QPointF(expanded.left(), expanded.bottom())),
            (QPointF(expanded.left(), expanded.bottom()),
             QPointF(expanded.left(), expanded.top())),
        ]
        for e1, e2 in edges:
            if GeometryUtils._segments_intersect(p1, p2, e1, e2):
                return True
        return False

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4):
        """Check if two line segments intersect."""
        d1 = GeometryUtils._cross(p3, p4, p1)
        d2 = GeometryUtils._cross(p3, p4, p2)
        d3 = GeometryUtils._cross(p1, p2, p3)
        d4 = GeometryUtils._cross(p1, p2, p4)
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        return False

    @staticmethod
    def _cross(a, b, c):
        """Cross product of vectors (b-a) and (c-a)."""
        return (b.x() - a.x()) * (c.y() - a.y()) - \
               (b.y() - a.y()) * (c.x() - a.x())
