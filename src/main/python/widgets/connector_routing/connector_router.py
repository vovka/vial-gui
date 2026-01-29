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
        self._tolerance = avg_key_size * 0.3

    def route(self, label_center, key_rect):
        """Find shortest Manhattan path from label to key."""
        if not self.gap_intersections:
            key_point = self._find_key_connection_point(key_rect, label_center)
            return self._build_simple_path(label_center, key_point)

        # First find path to nearest intersection to the key
        path = self._find_path_to_key(label_center, key_rect)
        return self._normalize_path(path)

    def _find_path_to_key(self, start, key_rect):
        """Find path from start to key, connecting to nearest edge point."""
        # Find intersections near the key
        key_center = key_rect.center()
        nearby_to_key = self._find_nearby_intersections(key_center, count=12)

        if not nearby_to_key:
            key_point = self._find_key_connection_point(key_rect, start)
            return self._build_simple_path(start, key_point)

        # Find best path to any intersection near the key
        # that can connect to the key without crossing other keys
        best_path = None
        best_cost = float('inf')

        for target_intersection in nearby_to_key:
            # Check if this intersection can connect to key without crossing
            key_point = self._find_key_connection_point(key_rect, target_intersection)
            if self._segment_crosses_keys(target_intersection, key_point, key_rect):
                continue  # Skip - final segment would cross keys

            path = self._find_shortest_manhattan_path(start, target_intersection, key_rect)
            if path and len(path) >= 1:
                cost = self._path_length(path)
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
                    best_key_point = key_point

        if not best_path:
            key_point = self._find_key_connection_point(key_rect, start)
            return self._build_simple_path(start, key_point)

        # Add the final connection to the key
        best_path.append(best_key_point)
        return best_path

    def _segment_crosses_keys(self, p1, p2, exclude_rect):
        """Check if segment crosses any key except excluded one."""
        for rect in self.key_rects:
            if rect == exclude_rect:
                continue
            if GeometryUtils.line_intersects_rect(p1, p2, rect):
                return True
        return False

    def _find_nearby_intersections(self, point, count=5):
        """Find nearest intersections to a point."""
        if not self.gap_intersections:
            return []
        sorted_pts = sorted(self.gap_intersections,
                           key=lambda p: GeometryUtils.distance(p, point))
        return sorted_pts[:count]

    def _path_length(self, path):
        """Calculate total path length."""
        total = 0
        for i in range(len(path) - 1):
            total += GeometryUtils.distance(path[i], path[i + 1])
        return total

    def _find_shortest_manhattan_path(self, start, end, key_rect):
        """A* pathfinding - only connect aligned nodes that don't cross keys."""
        nodes = [start, end] + list(self.gap_intersections)

        def manhattan_dist(p1, p2):
            return abs(p1.x() - p2.x()) + abs(p1.y() - p2.y())

        def are_aligned(p1, p2):
            """Check if two points share X or Y coordinate."""
            return abs(p1.x() - p2.x()) < self._tolerance or \
                   abs(p1.y() - p2.y()) < self._tolerance

        def crosses_keys(p1, p2):
            """Check if segment crosses any key."""
            for rect in self.key_rects:
                if rect == key_rect:
                    continue
                if GeometryUtils.line_intersects_rect(p1, p2, rect):
                    return True
            return False

        def can_connect(p1, p2):
            """Check if two nodes can be connected (aligned and no key crossing)."""
            if not are_aligned(p1, p2):
                return False
            if crosses_keys(p1, p2):
                return False
            return True

        def node_key(p):
            return (round(p.x(), 1), round(p.y(), 1))

        start_key = node_key(start)
        end_key = node_key(end)

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
                path = [end]
                while current_key in came_from:
                    current_key, current = came_from[current_key]
                    path.append(current)
                path.reverse()
                return path

            for neighbor in nodes:
                neighbor_key = node_key(neighbor)
                if neighbor_key == current_key or neighbor_key in visited:
                    continue
                if not can_connect(current, neighbor):
                    continue

                cost = manhattan_dist(current, neighbor)
                tentative_g = g_score[current_key] + cost

                if neighbor_key not in g_score or tentative_g < g_score[neighbor_key]:
                    came_from[neighbor_key] = (current_key, current)
                    g_score[neighbor_key] = tentative_g
                    f_score = tentative_g + manhattan_dist(neighbor, end)
                    counter += 1
                    heapq.heappush(open_set, (f_score, counter, neighbor_key, neighbor))

        return None

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
        deduped = [points[0]]
        for pt in points[1:]:
            if GeometryUtils.distance(pt, deduped[-1]) > 0.01:
                deduped.append(pt)
        if len(deduped) < 3:
            return deduped
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
