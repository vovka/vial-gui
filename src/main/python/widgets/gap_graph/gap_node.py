# SPDX-License-Identifier: GPL-2.0-or-later

import math
from PyQt5.QtCore import QPointF


class GapNode:
    """A node in the gap graph representing an intersection point."""

    def __init__(self, position, node_id=None):
        self.position = position
        self.node_id = node_id
        self.neighbors = []

    @property
    def x(self):
        return self.position.x()

    @property
    def y(self):
        return self.position.y()

    def add_neighbor(self, node):
        """Add a neighbor node that can be reached from this node."""
        if node not in self.neighbors and node != self:
            self.neighbors.append(node)

    def distance_to(self, point):
        """Calculate distance to a point or another node."""
        if isinstance(point, GapNode):
            other = point.position
        elif isinstance(point, QPointF):
            other = point
        else:
            other = QPointF(point[0], point[1])
        return math.hypot(self.x - other.x(), self.y - other.y())

    def is_leaf(self):
        """Check if this node is a leaf (edge node with 1 or 0 neighbors)."""
        return len(self.neighbors) <= 1

    def __repr__(self):
        return f"GapNode({self.x:.1f}, {self.y:.1f}, neighbors={len(self.neighbors)})"
