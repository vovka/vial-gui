# SPDX-License-Identifier: GPL-2.0-or-later
"""Assigns combos to boundary slots using min-cost matching."""

import math
from typing import List, Dict, Tuple
from PyQt5.QtCore import QRectF
from .geometry import Slot, ComboAnchor


class SlotAssigner:
    """Assigns combo anchors to slots minimizing total cost."""

    def __init__(self, distance_weight: float = 1.0, side_weight: float = 0.5):
        self.distance_weight = distance_weight
        self.side_weight = side_weight

    def assign(
        self, anchors: List[ComboAnchor], slots: List[Slot], boundary: QRectF
    ) -> Dict[int, int]:
        """Assign each combo to a slot. Returns {combo_index: slot_index}."""
        if not anchors or not slots:
            return {}

        cost_matrix = self._build_cost_matrix(anchors, slots, boundary)
        return self._greedy_assignment(anchors, slots, cost_matrix)

    def _build_cost_matrix(
        self, anchors: List[ComboAnchor], slots: List[Slot], boundary: QRectF
    ) -> List[List[float]]:
        """Build cost matrix for all anchor-slot pairs."""
        cx = boundary.center().x()
        cy = boundary.center().y()

        return [
            [self._compute_cost(a, s, cx, cy) for s in slots]
            for a in anchors
        ]

    def _compute_cost(
        self, anchor: ComboAnchor, slot: Slot, cx: float, cy: float
    ) -> float:
        """Compute assignment cost for anchor-slot pair."""
        dist = self._manhattan_distance(anchor.position, slot.position)
        side_penalty = self._side_penalty(anchor.position, slot, cx, cy)

        return self.distance_weight * dist + self.side_weight * side_penalty

    def _manhattan_distance(self, p1, p2) -> float:
        return abs(p1.x() - p2.x()) + abs(p1.y() - p2.y())

    def _side_penalty(self, pos, slot: Slot, cx: float, cy: float) -> float:
        """Penalize if anchor is on opposite side from slot."""
        penalty = 0.0
        if slot.side in ('left', 'right'):
            anchor_side = 'left' if pos.x() < cx else 'right'
            if anchor_side != slot.side:
                penalty += 100.0
        else:
            anchor_side = 'top' if pos.y() < cy else 'bottom'
            if anchor_side != slot.side:
                penalty += 100.0
        return penalty

    def _greedy_assignment(
        self, anchors: List[ComboAnchor], slots: List[Slot],
        cost_matrix: List[List[float]]
    ) -> Dict[int, int]:
        """Greedy assignment: sort by min cost and assign greedily."""
        pairs = []
        for i, anchor in enumerate(anchors):
            for j, slot in enumerate(slots):
                pairs.append((cost_matrix[i][j], i, j))

        pairs.sort(key=lambda x: x[0])
        assigned_anchors = set()
        assigned_slots = set()
        result = {}

        for cost, ai, si in pairs:
            if ai in assigned_anchors or si in assigned_slots:
                continue
            result[anchors[ai].combo_index] = slots[si].index
            assigned_anchors.add(ai)
            assigned_slots.add(si)
            if len(result) == len(anchors):
                break

        return result
