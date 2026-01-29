# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import QPointF


class Waypoint:
    """A waypoint in the connector routing graph."""

    def __init__(self, position, waypoint_type="gap"):
        self.position = position
        self.waypoint_type = waypoint_type
        self.neighbors = []

    @property
    def x(self):
        return self.position.x()

    @property
    def y(self):
        return self.position.y()

    def add_neighbor(self, waypoint):
        """Add a neighbor waypoint that can be reached from this one."""
        if waypoint not in self.neighbors and waypoint != self:
            self.neighbors.append(waypoint)

    def is_leaf(self):
        """Check if this is a leaf node (edge of the graph)."""
        return len(self.neighbors) <= 1

    def distance_to(self, other):
        """Calculate distance to another waypoint or QPointF."""
        if isinstance(other, Waypoint):
            other_pos = other.position
        else:
            other_pos = other
        dx = self.x - other_pos.x()
        dy = self.y - other_pos.y()
        return (dx * dx + dy * dy) ** 0.5
