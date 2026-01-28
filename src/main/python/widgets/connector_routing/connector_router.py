# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.connector_routing.waypoint_graph import WaypointGraph
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors using orthogonal (horizontal/vertical) paths."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.graph = WaypointGraph(key_rects, avg_key_size)

    def route(self, label_center, key_rect):
        """Find an orthogonal path from label center to the key."""
        key_point = self._find_key_connection_point(key_rect, label_center)
        path = self._build_orthogonal_path(label_center, key_point, key_rect)
        return path

    def _find_key_connection_point(self, key_rect, from_point):
        """Find the closest point on the key edge to connect to."""
        inset = min(key_rect.width(), key_rect.height()) * 0.25
        return self._closest_edge_point(key_rect, from_point, inset)

    def _closest_edge_point(self, rect, point, inset):
        """Find the closest point on rect edge, inset from corners."""
        cx, cy = rect.center().x(), rect.center().y()
        px, py = point.x(), point.y()
        left, right = rect.left() + inset, rect.right() - inset
        top, bottom = rect.top() + inset, rect.bottom() - inset
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

    def _build_orthogonal_path(self, start, end, target_key_rect):
        """Build an L-shaped or routed orthogonal path."""
        corner1 = QPointF(end.x(), start.y())
        corner2 = QPointF(start.x(), end.y())
        path1 = [start, corner1, end]
        path2 = [start, corner2, end]
        cost1 = self._path_cost(path1, target_key_rect)
        cost2 = self._path_cost(path2, target_key_rect)
        if cost1 == 0:
            return path1
        if cost2 == 0:
            return path2
        routed = self._try_routed_path(start, end, target_key_rect)
        if routed:
            return routed
        return path1 if cost1 <= cost2 else path2

    def _path_cost(self, path, target_key_rect):
        """Calculate how many keys a path crosses (excluding target)."""
        cost = 0
        for i in range(len(path) - 1):
            cost += self._segment_crossings(path[i], path[i + 1], target_key_rect)
        return cost

    def _segment_crossings(self, p1, p2, target_key_rect):
        """Count how many keys a segment crosses."""
        count = 0
        for rect in self.key_rects:
            if rect == target_key_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                count += 1
        return count

    def _try_routed_path(self, start, end, target_key_rect):
        """Try to find a path through gap waypoints."""
        best_path = None
        best_cost = float('inf')
        for wp in self.graph.waypoints:
            pos = wp.position
            if target_key_rect.contains(pos):
                continue
            for path in self._waypoint_path_variants(start, end, pos):
                cost = self._path_cost(path, target_key_rect)
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
        return best_path if best_cost == 0 else None

    def _waypoint_path_variants(self, start, end, waypoint):
        """Generate different orthogonal path variants through waypoint."""
        mid_x, mid_y = waypoint.x(), waypoint.y()
        return [
            [start, QPointF(mid_x, start.y()), QPointF(mid_x, end.y()), end],
            [start, QPointF(start.x(), mid_y), QPointF(end.x(), mid_y), end],
            [start, QPointF(mid_x, start.y()), waypoint, QPointF(mid_x, end.y()), end],
            [start, QPointF(start.x(), mid_y), waypoint, QPointF(end.x(), mid_y), end],
        ]
