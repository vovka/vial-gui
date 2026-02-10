# SPDX-License-Identifier: GPL-2.0-or-later
"""Reduces path crossings through routing order optimization."""

from typing import List, Tuple
from PyQt5.QtCore import QPointF
from .geometry import ComboAnchor, Slot, Route


class CrossingReducer:
    """Reduces crossings by optimizing routing order."""

    def order_combos_for_routing(
        self, anchors: List[ComboAnchor], assignment: dict, slots: List[Slot]
    ) -> List[ComboAnchor]:
        """Order combos for routing: longest routes first."""
        slot_map = {s.index: s for s in slots}

        scored = []
        for anchor in anchors:
            slot_idx = assignment.get(anchor.combo_index)
            if slot_idx is None:
                continue
            slot = slot_map.get(slot_idx)
            if slot is None:
                continue
            dist = self._distance(anchor.position, slot.position)
            scored.append((dist, anchor))

        scored.sort(key=lambda x: -x[0])
        return [a for _, a in scored]

    def _distance(self, p1: QPointF, p2: QPointF) -> float:
        dx = p1.x() - p2.x()
        dy = p1.y() - p2.y()
        return (dx * dx + dy * dy) ** 0.5

    def count_crossings(self, routes: List[Route]) -> int:
        """Count total segment crossings between routes."""
        count = 0
        for i, r1 in enumerate(routes):
            for r2 in routes[i + 1:]:
                count += self._count_route_crossings(r1, r2)
        return count

    def _count_route_crossings(self, r1: Route, r2: Route) -> int:
        """Count crossings between two routes."""
        crossings = 0
        for i in range(len(r1.simplified_path) - 1):
            seg1 = (r1.simplified_path[i], r1.simplified_path[i + 1])
            for j in range(len(r2.simplified_path) - 1):
                seg2 = (r2.simplified_path[j], r2.simplified_path[j + 1])
                if self._segments_intersect(seg1, seg2):
                    crossings += 1
        return crossings

    def _segments_intersect(self, seg1, seg2) -> bool:
        """Check if two line segments intersect."""
        p1, p2 = seg1
        p3, p4 = seg2
        return self._ccw(p1, p3, p4) != self._ccw(p2, p3, p4) and \
               self._ccw(p1, p2, p3) != self._ccw(p1, p2, p4)

    def _ccw(self, a: QPointF, b: QPointF, c: QPointF) -> bool:
        """Check counter-clockwise orientation."""
        return (c.y() - a.y()) * (b.x() - a.x()) > (b.y() - a.y()) * (c.x() - a.x())
