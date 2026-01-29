# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF
from widgets.gap_graph.gap_node import GapNode


class GapGraph:
    """Builds a graph of gap intersection nodes from keyboard geometry."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.nodes = []
        self._h_gaps = []
        self._v_gaps = []
        self._build_graph()

    def _build_graph(self):
        """Build the complete gap graph."""
        self._find_gap_lines()
        self._create_intersection_nodes()
        self._connect_nodes()

    def _find_gap_lines(self):
        """Find horizontal and vertical gap lines between keys."""
        if not self.key_rects:
            return
        rows = self._group_keys_by_row()
        self._find_horizontal_gaps(rows)
        self._find_vertical_gaps(rows)

    def _group_keys_by_row(self):
        """Group keys by approximate row based on y-center."""
        rows = {}
        tolerance = self.avg_key_size * 0.3
        for rect in self.key_rects:
            cy = rect.center().y()
            matched = False
            for row_y in rows:
                if abs(row_y - cy) < tolerance:
                    rows[row_y].append(rect)
                    matched = True
                    break
            if not matched:
                rows[cy] = [rect]
        return rows

    def _find_horizontal_gaps(self, rows):
        """Find horizontal gap lines between adjacent rows."""
        if len(rows) < 2:
            return
        sorted_rows = sorted(rows.keys())
        for i in range(len(sorted_rows) - 1):
            row1_y = sorted_rows[i]
            row2_y = sorted_rows[i + 1]
            row1_rects = rows[row1_y]
            row2_rects = rows[row2_y]
            bottom = max(r.bottom() for r in row1_rects)
            top = min(r.top() for r in row2_rects)
            if top > bottom:
                gap_y = (bottom + top) / 2
                all_rects = row1_rects + row2_rects
                x_min = min(r.left() for r in all_rects)
                x_max = max(r.right() for r in all_rects)
                self._h_gaps.append((gap_y, x_min, x_max))

    def _find_vertical_gaps(self, rows):
        """Find vertical gap lines between adjacent keys in each row."""
        seen_gaps = set()
        for row_rects in rows.values():
            if len(row_rects) < 2:
                continue
            sorted_rects = sorted(row_rects, key=lambda r: r.left())
            for i in range(len(sorted_rects) - 1):
                r1, r2 = sorted_rects[i], sorted_rects[i + 1]
                if r2.left() > r1.right():
                    gap_x = (r1.right() + r2.left()) / 2
                    gap_key = round(gap_x, 1)
                    if gap_key not in seen_gaps:
                        seen_gaps.add(gap_key)
                        y_extent = self._find_vertical_gap_extent(gap_x)
                        if y_extent:
                            self._v_gaps.append((gap_x, y_extent[0], y_extent[1]))

    def _find_vertical_gap_extent(self, gap_x):
        """Find the vertical extent of a gap at the given x coordinate."""
        y_min = float('inf')
        y_max = float('-inf')
        margin = self.avg_key_size * 0.1
        for rect in self.key_rects:
            if rect.left() - margin <= gap_x <= rect.right() + margin:
                y_min = min(y_min, rect.top())
                y_max = max(y_max, rect.bottom())
        if y_min == float('inf'):
            return None
        return (y_min, y_max)

    def _create_intersection_nodes(self):
        """Create nodes at intersections of gap lines."""
        node_id = 0
        seen = set()
        for h_gap in self._h_gaps:
            gap_y, x_min, x_max = h_gap
            for v_gap in self._v_gaps:
                gap_x, y_min, y_max = v_gap
                if x_min <= gap_x <= x_max and y_min <= gap_y <= y_max:
                    key = (round(gap_x, 1), round(gap_y, 1))
                    if key not in seen:
                        seen.add(key)
                        node = GapNode(QPointF(gap_x, gap_y), node_id)
                        self.nodes.append(node)
                        node_id += 1
        self._add_gap_endpoints(seen, node_id)

    def _add_gap_endpoints(self, seen, start_id):
        """Add nodes at the endpoints of gap lines."""
        node_id = start_id
        for h_gap in self._h_gaps:
            gap_y, x_min, x_max = h_gap
            for x in [x_min, x_max]:
                key = (round(x, 1), round(gap_y, 1))
                if key not in seen:
                    seen.add(key)
                    node = GapNode(QPointF(x, gap_y), node_id)
                    self.nodes.append(node)
                    node_id += 1
        for v_gap in self._v_gaps:
            gap_x, y_min, y_max = v_gap
            for y in [y_min, y_max]:
                key = (round(gap_x, 1), round(y, 1))
                if key not in seen:
                    seen.add(key)
                    node = GapNode(QPointF(gap_x, y), node_id)
                    self.nodes.append(node)
                    node_id += 1

    def _connect_nodes(self):
        """Connect nodes that can reach each other along gap lines."""
        self._connect_along_horizontal_gaps()
        self._connect_along_vertical_gaps()

    def _connect_along_horizontal_gaps(self):
        """Connect nodes along the same horizontal gap line."""
        for h_gap in self._h_gaps:
            gap_y, x_min, x_max = h_gap
            nodes_on_gap = self._nodes_on_horizontal_line(gap_y, x_min, x_max)
            nodes_on_gap.sort(key=lambda n: n.x)
            for i in range(len(nodes_on_gap) - 1):
                n1, n2 = nodes_on_gap[i], nodes_on_gap[i + 1]
                if not self._segment_blocked_by_key(n1.position, n2.position):
                    n1.add_neighbor(n2)
                    n2.add_neighbor(n1)

    def _connect_along_vertical_gaps(self):
        """Connect nodes along the same vertical gap line."""
        for v_gap in self._v_gaps:
            gap_x, y_min, y_max = v_gap
            nodes_on_gap = self._nodes_on_vertical_line(gap_x, y_min, y_max)
            nodes_on_gap.sort(key=lambda n: n.y)
            for i in range(len(nodes_on_gap) - 1):
                n1, n2 = nodes_on_gap[i], nodes_on_gap[i + 1]
                if not self._segment_blocked_by_key(n1.position, n2.position):
                    n1.add_neighbor(n2)
                    n2.add_neighbor(n1)

    def _nodes_on_horizontal_line(self, y, x_min, x_max):
        """Find all nodes on a horizontal line within x bounds."""
        tolerance = self.avg_key_size * 0.1
        result = []
        for node in self.nodes:
            if abs(node.y - y) < tolerance and x_min - tolerance <= node.x <= x_max + tolerance:
                result.append(node)
        return result

    def _nodes_on_vertical_line(self, x, y_min, y_max):
        """Find all nodes on a vertical line within y bounds."""
        tolerance = self.avg_key_size * 0.1
        result = []
        for node in self.nodes:
            if abs(node.x - x) < tolerance and y_min - tolerance <= node.y <= y_max + tolerance:
                result.append(node)
        return result

    def _segment_blocked_by_key(self, p1, p2):
        """Check if a line segment is blocked by any key."""
        margin = self.avg_key_size * 0.05
        for rect in self.key_rects:
            inflated = rect.adjusted(-margin, -margin, margin, margin)
            if self._line_intersects_rect(p1, p2, inflated):
                return True
        return False

    def _line_intersects_rect(self, p1, p2, rect):
        """Check if a line segment intersects a rectangle interior."""
        if rect.contains(p1) or rect.contains(p2):
            return True
        edges = [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top())),
        ]
        for e1, e2 in edges:
            if self._segments_intersect(p1, p2, e1, e2):
                return True
        return False

    def _segments_intersect(self, p1, p2, p3, p4):
        """Check if two line segments intersect."""
        def cross(o, a, b):
            return (a.x() - o.x()) * (b.y() - o.y()) - (a.y() - o.y()) * (b.x() - o.x())
        d1 = cross(p3, p4, p1)
        d2 = cross(p3, p4, p2)
        d3 = cross(p1, p2, p3)
        d4 = cross(p1, p2, p4)
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        return False

    def find_nearest_node(self, point):
        """Find the nearest node to a given point."""
        if not self.nodes:
            return None
        return min(self.nodes, key=lambda n: n.distance_to(point))

    def get_horizontal_gaps(self):
        """Return horizontal gap lines for visualization."""
        return self._h_gaps

    def get_vertical_gaps(self):
        """Return vertical gap lines for visualization."""
        return self._v_gaps
