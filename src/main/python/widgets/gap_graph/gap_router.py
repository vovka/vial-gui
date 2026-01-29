# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF
from widgets.gap_graph.gap_graph import GapGraph


class GapRouter:
    """Routes connectors through gap graph from keys to combo labels."""

    def __init__(self, key_rects, avg_key_size):
        self.key_rects = key_rects
        self.avg_key_size = avg_key_size
        self.graph = GapGraph(key_rects, avg_key_size)

    def route(self, key_rect, label_center):
        """Route a path from key to label center through gap nodes."""
        key_center = key_rect.center()
        path = [key_center]
        entry_node = self._find_entry_node(key_rect)
        if entry_node is None:
            path.append(label_center)
            return path
        path.append(entry_node.position)
        visited = {entry_node}
        current = entry_node
        while True:
            next_node = self._select_next_node(current, label_center, visited)
            if next_node is None:
                break
            path.append(next_node.position)
            visited.add(next_node)
            current = next_node
            if current.is_leaf():
                break
        path.append(label_center)
        return path

    def _find_entry_node(self, key_rect):
        """Find the best entry node near the key."""
        if not self.graph.nodes:
            return None
        key_center = key_rect.center()
        margin = self.avg_key_size * 0.5
        nearby = []
        for node in self.graph.nodes:
            if self._is_node_adjacent_to_rect(node, key_rect, margin):
                nearby.append(node)
        if nearby:
            return min(nearby, key=lambda n: n.distance_to(key_center))
        return self.graph.find_nearest_node(key_center)

    def _is_node_adjacent_to_rect(self, node, rect, margin):
        """Check if node is adjacent to the rectangle (not inside, but close)."""
        expanded = rect.adjusted(-margin, -margin, margin, margin)
        if not expanded.contains(node.position):
            return False
        if rect.contains(node.position):
            return False
        return True

    def _select_next_node(self, current, destination, visited):
        """Select the next node that moves closer to destination."""
        candidates = []
        current_dist = current.distance_to(destination)
        for neighbor in current.neighbors:
            if neighbor in visited:
                continue
            neighbor_dist = neighbor.distance_to(destination)
            if neighbor_dist < current_dist:
                candidates.append((neighbor, neighbor_dist))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]

    def get_graph(self):
        """Return the underlying gap graph for visualization."""
        return self.graph
