# SPDX-License-Identifier: GPL-2.0-or-later
"""Finds gaps between keys for label placement."""

from typing import List, Optional, Tuple
from PyQt5.QtCore import QPointF, QRectF


class GapFinder:
    """Finds gaps between keys suitable for label placement."""

    def __init__(self, min_gap_size: float = 10.0):
        self.min_gap_size = min_gap_size
        self._center_gap = None
        self._key_rects = []

    def analyze_keyboard(self, key_rects: List[QRectF]):
        """Analyze keyboard layout to find gaps."""
        self._key_rects = key_rects
        self._center_gap = self._find_center_gap(key_rects)

    def _find_center_gap(self, key_rects: List[QRectF]) -> Optional[QRectF]:
        """Find the gap between keyboard halves (if split keyboard)."""
        if not key_rects:
            return None

        bbox = key_rects[0]
        for rect in key_rects[1:]:
            bbox = bbox.united(rect)

        mid_x = bbox.center().x()
        left_keys = [r for r in key_rects if r.center().x() < mid_x]
        right_keys = [r for r in key_rects if r.center().x() >= mid_x]

        if not left_keys or not right_keys:
            return None

        left_edge = max(r.right() for r in left_keys)
        right_edge = min(r.left() for r in right_keys)
        gap_width = right_edge - left_edge

        if gap_width < self.min_gap_size * 2:
            return None

        return QRectF(left_edge, bbox.top(), gap_width, bbox.height())

    def find_best_position(
        self, anchor: QPointF, combo_rects: List[QRectF], label_size: Tuple[float, float]
    ) -> Tuple[QPointF, bool]:
        """Find best label position near combo keys. Returns (position, used_gap)."""
        label_w, label_h = label_size

        if self._center_gap and self._is_near_center(anchor):
            pos = self._place_in_center_gap(anchor, label_w, label_h)
            if pos:
                return pos, True

        pos = self._find_gap_near_keys(anchor, combo_rects, label_w, label_h)
        if pos:
            return pos, True

        return anchor, False

    def _is_near_center(self, point: QPointF) -> bool:
        """Check if point is near the center gap."""
        if not self._center_gap:
            return False
        expanded = self._center_gap.adjusted(-50, 0, 50, 0)
        return expanded.contains(point)

    def _place_in_center_gap(
        self, anchor: QPointF, label_w: float, label_h: float
    ) -> Optional[QPointF]:
        """Place label in center gap at anchor's y level."""
        if not self._center_gap:
            return None

        gap = self._center_gap
        if gap.width() < label_w + 4:
            return None

        x = gap.center().x()
        y = max(gap.top() + label_h / 2, min(anchor.y(), gap.bottom() - label_h / 2))

        return QPointF(x, y)

    def _find_gap_near_keys(
        self, anchor: QPointF, combo_rects: List[QRectF],
        label_w: float, label_h: float
    ) -> Optional[QPointF]:
        """Find gap adjacent to combo keys."""
        if not combo_rects:
            return None

        combo_bbox = combo_rects[0]
        for rect in combo_rects[1:]:
            combo_bbox = combo_bbox.united(rect)

        candidates = self._generate_candidates(combo_bbox, label_w, label_h)

        for pos in candidates:
            label_rect = QRectF(
                pos.x() - label_w / 2, pos.y() - label_h / 2, label_w, label_h
            )
            if not self._overlaps_keys(label_rect):
                return pos

        return None

    def _generate_candidates(
        self, bbox: QRectF, label_w: float, label_h: float
    ) -> List[QPointF]:
        """Generate candidate positions around combo bounding box."""
        gap = 4.0
        candidates = [
            QPointF(bbox.center().x(), bbox.top() - label_h / 2 - gap),
            QPointF(bbox.center().x(), bbox.bottom() + label_h / 2 + gap),
            QPointF(bbox.left() - label_w / 2 - gap, bbox.center().y()),
            QPointF(bbox.right() + label_w / 2 + gap, bbox.center().y()),
            QPointF(bbox.left() - label_w / 2 - gap, bbox.top()),
            QPointF(bbox.right() + label_w / 2 + gap, bbox.top()),
            QPointF(bbox.left() - label_w / 2 - gap, bbox.bottom()),
            QPointF(bbox.right() + label_w / 2 + gap, bbox.bottom()),
        ]
        return candidates

    def _overlaps_keys(self, rect: QRectF) -> bool:
        """Check if rectangle overlaps any key."""
        for key_rect in self._key_rects:
            if rect.intersects(key_rect):
                return True
        return False

    def get_center_gap(self) -> Optional[QRectF]:
        """Return the center gap if found."""
        return self._center_gap
