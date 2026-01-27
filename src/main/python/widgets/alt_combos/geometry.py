# SPDX-License-Identifier: GPL-2.0-or-later
"""Basic geometry data classes for alt combos visualization."""

from dataclasses import dataclass
from typing import List, Tuple
from PyQt5.QtCore import QPointF, QRectF


@dataclass
class Slot:
    """A label slot on the boundary perimeter."""
    position: QPointF
    direction: QPointF  # Inward normal (unit vector)
    index: int
    side: str  # 'top', 'right', 'bottom', 'left'


@dataclass
class ComboAnchor:
    """Anchor point for a combo (centroid of involved keys)."""
    position: QPointF
    combo_index: int
    key_rects: List[QRectF]
    output_label: str
    combo_label: str


@dataclass
class Route:
    """A routed path from combo anchor to assigned slot."""
    combo_index: int
    slot_index: int
    path: List[Tuple[int, int]]  # Grid coordinates
    simplified_path: List[QPointF]  # Canvas coordinates
    cost: float
