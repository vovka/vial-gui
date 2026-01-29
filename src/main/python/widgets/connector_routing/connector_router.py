# SPDX-License-Identifier: GPL-2.0-or-later

import heapq
from PyQt5.QtCore import QPointF
from widgets.connector_routing.geometry_utils import GeometryUtils


class ConnectorRouter:
    """Routes connectors using shortest Manhattan path through intersections."""

    def __init__(self, key_rects, avg_key_size, gap_intersections=None):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.gap_intersections = gap_intersections or []
        self._tolerance = avg_key_size * 0.1

    def route(self, label_center, key_rect):
        """Find shortest Manhattan path from label to key."""
        key_point = self._find_key_connection_point(key_rect, label_center)
        if not self.gap_intersections:
            return self._build_simple_path(label_center, key_point)
        path = self._find_shortest_manhattan_path(label_center, key_point)
        return self._normalize_path(path)

    def _find_shortest_manhattan_path(self, start, end):
        """A* pathfinding with Manhattan distance through intersection points."""
        # Build list of all nodes: start, end, and all intersections
        nodes = [start, end] + list(self.gap_intersections)

        def manhattan_dist(p1, p2):
            return abs(p1.x() - p2.x()) + abs(p1.y() - p2.y())

        def node_key(p):
            return (round(p.x(), 1), round(p.y(), 1))

        # A* algorithm - all nodes connected with Manhattan distance cost
        start_key = node_key(start)
        end_key = node_key(end)

        # Priority queue: (f_score, counter, node_key, node)
        counter = 0
        open_set = [(manhattan_dist(start, end), counter, start_key, start)]

        came_from = {}
        g_score = {start_key: 0}
        visited = set()

        while open_set:
            _, _, current_key, current = heapq.heappop(open_set)

            if current_key in visited:
                continue
            visited.add(current_key)

            if current_key == end_key:
                # Reconstruct path
                path = [end]
                while current_key in came_from:
                    current_key, current = came_from[current_key]
                    path.append(current)
                path.reverse()
                return self._make_orthogonal(path)

            # All intersection nodes are potential neighbors
            for neighbor in nodes:
                neighbor_key = node_key(neighbor)
                if neighbor_key == current_key or neighbor_key in visited:
                    continue

                # Cost is Manhattan distance to neighbor
                tentative_g = g_score[current_key] + manhattan_dist(current, neighbor)

                if neighbor_key not in g_score or tentative_g < g_score[neighbor_key]:
                    came_from[neighbor_key] = (current_key, current)
                    g_score[neighbor_key] = tentative_g
                    f_score = tentative_g + manhattan_dist(neighbor, end)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor_key, neighbor))

        # No path found, fallback to simple path
        return self._build_simple_path(start, end)

    def _make_orthogonal(self, path):
        """Convert path to orthogonal segments by adding corner points."""
        if len(path) < 2:
            return path
        result = [path[0]]
        for i in range(1, len(path)):
            prev = result[-1]
            curr = path[i]
            # If not aligned, add a corner point
            if abs(prev.x() - curr.x()) > 0.1 and abs(prev.y() - curr.y()) > 0.1:
                # Add corner: go horizontal first, then vertical
                result.append(QPointF(curr.x(), prev.y()))
            result.append(curr)
        return result

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
