# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors through gap intersection points."""

    def __init__(self, key_rects, avg_key_size, gap_intersections=None):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.gap_intersections = gap_intersections or []

    def route(self, label_center, key_rect):
        """Find a path from label center to the key through one intersection."""
        key_point = self._find_key_connection_point(key_rect, label_center)
        if not self.gap_intersections:
            return self._build_simple_path(label_center, key_point)
        # Find the intersection nearest to the key
        nearest = self._find_nearest_intersection(key_point)
        if nearest is None:
            return self._build_simple_path(label_center, key_point)
        # Build path: label -> nearest intersection -> key
        path = self._build_path_via_intersection(label_center, nearest, key_point)
        return self._normalize_path(path)

    def _find_nearest_intersection(self, point):
        """Find the nearest intersection to a point."""
        if not self.gap_intersections:
            return None
        return min(self.gap_intersections,
                   key=lambda p: GeometryUtils.distance(p, point))

    def _build_path_via_intersection(self, start, intersection, end):
        """Build path: start -> intersection -> end with orthogonal segments."""
        path = [start]
        # First segment: horizontal from start toward intersection's X
        if abs(start.x() - intersection.x()) > 0.1:
            path.append(QPointF(intersection.x(), start.y()))
        # Then vertical to reach intersection
        if abs(path[-1].y() - intersection.y()) > 0.1:
            path.append(intersection)
        # From intersection to end: vertical first, then horizontal
        if abs(intersection.y() - end.y()) > 0.1:
            path.append(QPointF(intersection.x(), end.y()))
        # Finally horizontal to end
        if abs(path[-1].x() - end.x()) > 0.1:
            path.append(end)
        else:
            path.append(end)
        return path

    def _build_simple_path(self, start, end):
        """Build a simple L-shaped path."""
        corner = QPointF(end.x(), start.y())
        return [start, corner, end]

    def _find_key_connection_point(self, key_rect, from_point):
        """Find the closest point on the key edge to connect to."""
        inset = min(key_rect.width(), key_rect.height()) * 0.25
        return self._closest_edge_point(key_rect, from_point, inset)

    def _closest_edge_point(self, rect, point, inset):
        """Find the closest point on rect edge, inset from corners."""
        cx, cy = rect.center().x(), rect.center().y()
        px, py = point.x(), point.y()
        left = rect.left() + inset
        right = rect.right() - inset
        top = rect.top() + inset
        bottom = rect.bottom() - inset
        candidates = []
        if py <= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.top()))
        if py >= cy:
            candidates.append(QPointF(max(left, min(right, px)), rect.bottom()))
        if px <= cx:
            candidates.append(QPointF(rect.left(), max(top, min(bottom, py))))
        if px >= cx:
            candidates.append(QPointF(rect.right(), max(top, min(bottom, py))))
        if not candidates:
            candidates.append(QPointF(cx, rect.top()))
        return min(candidates, key=lambda c: GeometryUtils.distance(c, point))

    def _normalize_path(self, points):
        """Remove duplicate and collinear points."""
        if not points:
            return points
        # Remove duplicates
        deduped = [points[0]]
        for pt in points[1:]:
            if GeometryUtils.distance(pt, deduped[-1]) > 0.01:
                deduped.append(pt)
        if len(deduped) < 3:
            return deduped
        # Remove collinear middle points
        simplified = [deduped[0]]
        for i in range(1, len(deduped) - 1):
            prev = simplified[-1]
            curr = deduped[i]
            next_pt = deduped[i + 1]
            same_x = abs(prev.x() - curr.x()) < 0.01 and abs(curr.x() - next_pt.x()) < 0.01
            same_y = abs(prev.y() - curr.y()) < 0.01 and abs(curr.y() - next_pt.y()) < 0.01
            if not (same_x or same_y):
                simplified.append(curr)
        simplified.append(deduped[-1])
        return simplified
