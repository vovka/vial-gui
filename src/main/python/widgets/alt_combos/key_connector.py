# SPDX-License-Identifier: GPL-2.0-or-later
"""Draws connector lines from combo keys to anchor point."""

import math
from typing import List
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QPen, Qt


class KeyConnector:
    """Draws short connector lines from each combo key to the anchor."""

    def __init__(self, bend_radius: float = 8.0):
        self.bend_radius = bend_radius

    def render_key_connections(
        self, qp: QPainter, anchor: QPointF, key_rects: List[QRectF], line_pen: QPen
    ):
        """Draw connections from each key to the anchor point."""
        qp.setPen(line_pen)
        qp.setBrush(Qt.NoBrush)

        for rect in key_rects:
            corner = self._find_closest_corner(rect, anchor)
            path = self._create_connector_path(anchor, corner, rect)
            qp.drawPath(path)

    def _find_closest_corner(self, rect: QRectF, point: QPointF) -> QPointF:
        """Find the corner of rect closest to point, inset along diagonal."""
        corners = [
            QPointF(rect.left(), rect.top()),
            QPointF(rect.right(), rect.top()),
            QPointF(rect.left(), rect.bottom()),
            QPointF(rect.right(), rect.bottom()),
        ]
        corner = min(corners, key=lambda c: self._distance(c, point))

        center = rect.center()
        dx = center.x() - corner.x()
        dy = center.y() - corner.y()
        inset_ratio = 0.4
        return QPointF(corner.x() + dx * inset_ratio, corner.y() + dy * inset_ratio)

    def _create_connector_path(
        self, start: QPointF, end_corner: QPointF, key_rect: QRectF
    ) -> QPainterPath:
        """Create curved path from start to key corner."""
        path = QPainterPath()
        path.moveTo(start)

        approach = self._calculate_approach_point(end_corner, key_rect)
        path.lineTo(approach)

        ctrl = self._curve_control_point(approach, end_corner, key_rect)
        path.quadTo(ctrl, end_corner)
        return path

    def _calculate_approach_point(self, corner: QPointF, key_rect: QRectF) -> QPointF:
        """Calculate approach point outside the key corner."""
        offset = self.bend_radius
        cx, cy = key_rect.center().x(), key_rect.center().y()

        ax = corner.x() - offset if corner.x() < cx else corner.x() + offset
        ay = corner.y() - offset if corner.y() < cy else corner.y() + offset

        return QPointF(ax, ay)

    def _curve_control_point(
        self, approach: QPointF, corner: QPointF, key_rect: QRectF
    ) -> QPointF:
        """Calculate control point for the hook curve."""
        if abs(corner.x() - approach.x()) > abs(corner.y() - approach.y()):
            return QPointF(approach.x(), corner.y())
        return QPointF(corner.x(), approach.y())

    def _distance(self, p1: QPointF, p2: QPointF) -> float:
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())
