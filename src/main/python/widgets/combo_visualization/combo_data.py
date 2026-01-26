"""Data classes for combo visualization."""

from dataclasses import dataclass
from typing import List

from .point import Point
from .combo_box_placer import Alignment


@dataclass
class KeyInfo:
    """Information about a key in a combo."""
    center: Point
    size: float
    widget: object  # Reference to the original KeyWidget


@dataclass
class ComboSpec:
    """Specification for a single combo to render."""
    keys: List[KeyInfo]
    output_label: str
    combo_label: str


@dataclass
class ComboPlacement:
    """Computed placement for a combo box."""
    position: Point
    alignment: Alignment
    width: float
    height: float
    keys: List[KeyInfo]
    output_label: str
    combo_label: str
