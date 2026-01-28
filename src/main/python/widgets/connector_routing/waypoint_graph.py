# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF
from widgets.connector_routing.waypoint import Waypoint


class WaypointGraph:
    """Builds a graph of waypoints from gaps between keys."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.waypoints = []
        self._build_waypoints()

    def _build_waypoints(self):
        """Generate waypoints from gaps between adjacent keys."""
        threshold = self.avg_key_size * 1.5
        seen = set()
        for i, rect1 in enumerate(self.key_rects):
            for rect2 in self.key_rects[i + 1:]:
                gap_points = self._find_gap_points(rect1, rect2, threshold)
                for point in gap_points:
                    key = (round(point.x(), 1), round(point.y(), 1))
                    if key not in seen and not self._point_inside_key(point):
                        seen.add(key)
                        self.waypoints.append(Waypoint(point, "gap"))
        self._add_row_column_waypoints(seen)

    def _find_gap_points(self, rect1, rect2, threshold):
        """Find waypoints in the gap between two adjacent keys."""
        c1, c2 = rect1.center(), rect2.center()
        dist = math.hypot(c1.x() - c2.x(), c1.y() - c2.y())
        if dist > threshold:
            return []
        dx = abs(c1.x() - c2.x())
        dy = abs(c1.y() - c2.y())
        points = []
        if dx > dy:
            edge1_x = rect1.right() if c1.x() < c2.x() else rect1.left()
            edge2_x = rect2.left() if c1.x() < c2.x() else rect2.right()
            gap_x = (edge1_x + edge2_x) / 2
            points.append(QPointF(gap_x, c1.y()))
            points.append(QPointF(gap_x, c2.y()))
            points.append(QPointF(gap_x, (c1.y() + c2.y()) / 2))
        else:
            edge1_y = rect1.bottom() if c1.y() < c2.y() else rect1.top()
            edge2_y = rect2.top() if c1.y() < c2.y() else rect2.bottom()
            gap_y = (edge1_y + edge2_y) / 2
            points.append(QPointF(c1.x(), gap_y))
            points.append(QPointF(c2.x(), gap_y))
            points.append(QPointF((c1.x() + c2.x()) / 2, gap_y))
        return points

    def _add_row_column_waypoints(self, seen):
        """Add waypoints along row/column gaps for corridor routing."""
        if not self.key_rects:
            return
        rows = self._group_by_row()
        for row_rects in rows.values():
            if len(row_rects) < 2:
                continue
            sorted_rects = sorted(row_rects, key=lambda r: r.left())
            for i in range(len(sorted_rects) - 1):
                r1, r2 = sorted_rects[i], sorted_rects[i + 1]
                gap_x = (r1.right() + r2.left()) / 2
                for r in [r1, r2]:
                    for y in [r.top(), r.bottom()]:
                        point = QPointF(gap_x, y)
                        key = (round(point.x(), 1), round(point.y(), 1))
                        if key not in seen and not self._point_inside_key(point):
                            seen.add(key)
                            self.waypoints.append(Waypoint(point, "corridor"))

    def _group_by_row(self):
        """Group key rectangles by approximate row (y-center)."""
        rows = {}
        tolerance = self.avg_key_size * 0.3
        for rect in self.key_rects:
            cy = rect.center().y()
            found = False
            for row_y in rows:
                if abs(row_y - cy) < tolerance:
                    rows[row_y].append(rect)
                    found = True
                    break
            if not found:
                rows[cy] = [rect]
        return rows

    def _point_inside_key(self, point):
        """Check if a point is inside any key rectangle."""
        for rect in self.key_rects:
            if rect.contains(point):
                return True
        return False

    def find_nearest_waypoints(self, point, count=5):
        """Find the nearest waypoints to a given point."""
        if not self.waypoints:
            return []
        sorted_wps = sorted(self.waypoints, key=lambda w: w.distance_to(point))
        return sorted_wps[:count]
