# SPDX-License-Identifier: GPL-2.0-or-later
"""Renders routed paths and labels using QPainter."""

from typing import List
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFontMetrics
from PyQt5.QtWidgets import QApplication
from .geometry import Route, Slot


class PathRenderer:
    """Renders paths and labels for alt combos visualization."""

    def __init__(self, key_roundness: float = 0.08):
        self.key_roundness = key_roundness

    def render_route(self, qp: QPainter, route: Route, line_pen: QPen):
        """Render a single route as a polyline."""
        if len(route.simplified_path) < 2:
            return

        path = QPainterPath()
        path.moveTo(route.simplified_path[0])
        for point in route.simplified_path[1:]:
            path.lineTo(point)

        qp.setPen(line_pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawPath(path)

    def render_label(
        self, qp: QPainter, slot: Slot, combo_label: str, output_label: str,
        avg_size: float, fill_brush: QBrush, border_pen: QPen, text_pen: QPen,
        name_font, text_font
    ):
        """Render combo label at slot position."""
        rect = self._compute_label_rect(slot, avg_size, combo_label, output_label,
                                         name_font, text_font)

        corner = avg_size * self.key_roundness
        qp.setPen(border_pen)
        qp.setBrush(fill_brush)
        qp.drawRoundedRect(rect, corner, corner)

        self._draw_label_text(qp, rect, combo_label, output_label,
                              text_pen, name_font, text_font)

    def _compute_label_rect(
        self, slot: Slot, avg_size: float, combo_label: str, output_label: str,
        name_font, text_font
    ) -> QRectF:
        """Compute label rectangle positioned at slot."""
        name_metrics = QFontMetrics(name_font)
        label_metrics = QFontMetrics(text_font)

        rect_w = max(avg_size * 0.5, avg_size * 0.45)
        rect_h = max(avg_size * 0.4, avg_size * 0.35)
        text_padding = max(2.0, avg_size * 0.08)

        label_lines = output_label.splitlines() if output_label else []
        label_height = len(label_lines) * label_metrics.height()
        name_height = name_metrics.height() if combo_label else 0
        text_gap = max(1.0, name_metrics.height() * 0.15) if output_label else 0
        needed_height = name_height + label_height + text_gap + (text_padding * 2)
        if needed_height > rect_h:
            rect_h = needed_height

        offset = avg_size * 0.6
        rect_x = slot.position.x() + slot.direction.x() * offset - rect_w / 2
        rect_y = slot.position.y() + slot.direction.y() * offset - rect_h / 2

        return QRectF(rect_x, rect_y, rect_w, rect_h)

    def _draw_label_text(
        self, qp: QPainter, rect: QRectF, combo_label: str, output_label: str,
        text_pen: QPen, name_font, text_font
    ):
        """Draw text inside label rectangle."""
        qp.setPen(text_pen)

        if output_label:
            name_metrics = QFontMetrics(name_font)
            label_metrics = QFontMetrics(text_font)
            name_height = name_metrics.height()
            label_height = label_metrics.height() * len(output_label.splitlines())
            text_gap = max(1.0, name_metrics.height() * 0.15)
            total_height = name_height + label_height + text_gap
            start_y = rect.y() + (rect.height() - total_height) / 2

            name_rect = QRectF(rect.x(), start_y, rect.width(), name_height)
            label_rect = QRectF(rect.x(), start_y + name_height + text_gap,
                               rect.width(), label_height)
            qp.setFont(name_font)
            qp.drawText(name_rect, Qt.AlignHCenter | Qt.AlignVCenter, combo_label)
            qp.setFont(text_font)
            qp.drawText(label_rect, Qt.AlignHCenter | Qt.AlignVCenter, output_label)
        else:
            qp.setFont(name_font)
            qp.drawText(rect, Qt.AlignCenter, combo_label)
