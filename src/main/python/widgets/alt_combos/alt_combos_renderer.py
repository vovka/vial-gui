# SPDX-License-Identifier: GPL-2.0-or-later
"""Main orchestrator for alternative combos visualization."""

from typing import List, Tuple
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette, QFontMetrics
from PyQt5.QtWidgets import QApplication

from .geometry import ComboAnchor, Route
from .gap_finder import GapFinder
from .routing_grid import RoutingGrid
from .pathfinder import Pathfinder
from .path_simplifier import PathSimplifier
from .key_connector import KeyConnector


class AltCombosRenderer:
    """Orchestrates the alternative combos visualization pipeline."""

    def __init__(self, cell_size: float = 8.0):
        self.gap_finder = GapFinder(min_gap_size=15.0)
        self.pathfinder = Pathfinder(bend_penalty=3.0)
        self.simplifier = PathSimplifier()
        self.key_connector = KeyConnector()
        self.cell_size = cell_size
        self.placed_labels = []

    def render(
        self, qp: QPainter, combos: List[Tuple], key_rects: List[QRectF],
        scale: float, avg_size: float
    ):
        """Render all combos with routed paths and gap-based labels."""
        if not combos:
            return

        self.placed_labels = []
        self.gap_finder.analyze_keyboard(key_rects)

        anchors = self._build_anchors(combos)
        label_size = (avg_size * 0.55, avg_size * 0.45)

        label_positions = self._compute_label_positions(anchors, label_size)
        routes = self._route_all_paths(anchors, label_positions, key_rects)

        self._setup_painter(qp, scale)
        self._draw_all(qp, routes, anchors, label_positions, avg_size, key_rects)
        qp.restore()

    def _build_anchors(self, combos: List[Tuple]) -> List[ComboAnchor]:
        """Build combo anchors from combo widget data."""
        anchors = []
        for idx, (widgets, output_label, combo_label) in enumerate(combos):
            cx = sum(w.polygon.boundingRect().center().x() for w in widgets)
            cy = sum(w.polygon.boundingRect().center().y() for w in widgets)
            center = QPointF(cx / len(widgets), cy / len(widgets))
            rects = [w.polygon.boundingRect() for w in widgets]
            anchors.append(ComboAnchor(center, idx, rects, output_label, combo_label))
        return anchors

    def _compute_label_positions(
        self, anchors: List[ComboAnchor], label_size: Tuple[float, float]
    ) -> dict:
        """Compute label position for each combo using gaps."""
        positions = {}

        for anchor in anchors:
            pos, used_gap = self.gap_finder.find_best_position(
                anchor.position, anchor.key_rects, label_size
            )

            pos = self._avoid_overlaps(pos, label_size)
            positions[anchor.combo_index] = pos
            self.placed_labels.append(QRectF(
                pos.x() - label_size[0] / 2,
                pos.y() - label_size[1] / 2,
                label_size[0], label_size[1]
            ))

        return positions

    def _avoid_overlaps(
        self, pos: QPointF, label_size: Tuple[float, float]
    ) -> QPointF:
        """Adjust position to avoid overlapping existing labels."""
        label_w, label_h = label_size
        rect = QRectF(pos.x() - label_w / 2, pos.y() - label_h / 2, label_w, label_h)

        for placed in self.placed_labels:
            if rect.intersects(placed):
                pos = QPointF(pos.x(), placed.bottom() + label_h / 2 + 2)
                rect = QRectF(pos.x() - label_w / 2, pos.y() - label_h / 2,
                             label_w, label_h)

        return pos

    def _route_all_paths(
        self, anchors: List[ComboAnchor], label_positions: dict,
        key_rects: List[QRectF]
    ) -> List[Route]:
        """Route paths from anchors to label positions."""
        if not key_rects:
            return []

        bbox = key_rects[0]
        for rect in key_rects[1:]:
            bbox = bbox.united(rect)
        bbox = bbox.adjusted(-20, -20, 20, 20)

        grid = RoutingGrid(bbox, self.cell_size)
        grid.mark_obstacles(key_rects, padding=self.cell_size / 2)

        routes = []
        for anchor in anchors:
            label_pos = label_positions.get(anchor.combo_index)
            if label_pos is None:
                continue

            route = self._route_single(grid, anchor, label_pos)
            if route:
                grid.mark_used(route.path)
                routes.append(route)

        return routes

    def _route_single(self, grid, anchor: ComboAnchor, label_pos: QPointF) -> Route:
        """Route a single combo to its label position."""
        start = grid.world_to_grid(anchor.position)
        goal = grid.world_to_grid(label_pos)

        path, cost = self.pathfinder.find_path(grid, start, goal)
        simplified = self.simplifier.simplify(grid, path) if path else []

        return Route(anchor.combo_index, 0, path or [], simplified, cost)

    def _setup_painter(self, qp: QPainter, scale: float):
        """Setup painter with scale and antialiasing."""
        qp.save()
        qp.scale(scale, scale)
        qp.setRenderHint(QPainter.Antialiasing)

    def _draw_all(
        self, qp, routes, anchors, label_positions, avg_size, key_rects
    ):
        """Draw all routes and labels."""
        palette = QApplication.palette()
        line_pen, fill_brush, border_pen, text_pen = self._create_pens(palette)
        name_font, text_font = self._create_fonts()

        anchor_map = {a.combo_index: a for a in anchors}

        for anchor in anchors:
            self.key_connector.render_key_connections(
                qp, anchor.position, anchor.key_rects, line_pen
            )
            self._draw_anchor_dot(qp, anchor.position, fill_brush, border_pen, avg_size)

        for route in routes:
            self._draw_route(qp, route, line_pen)

        for anchor in anchors:
            label_pos = label_positions.get(anchor.combo_index)
            if label_pos:
                self._draw_label(
                    qp, label_pos, anchor.combo_label, anchor.output_label,
                    avg_size, fill_brush, border_pen, text_pen, name_font, text_font
                )

    def _draw_route(self, qp: QPainter, route: Route, line_pen: QPen):
        """Draw a route as a polyline."""
        if len(route.simplified_path) < 2:
            return

        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(route.simplified_path[0])
        for point in route.simplified_path[1:]:
            path.lineTo(point)

        qp.setPen(line_pen)
        qp.setBrush(Qt.NoBrush)
        qp.drawPath(path)

    def _draw_label(
        self, qp, pos, combo_label, output_label, avg_size,
        fill_brush, border_pen, text_pen, name_font, text_font
    ):
        """Draw combo label at position."""
        name_metrics = QFontMetrics(name_font)
        label_metrics = QFontMetrics(text_font)

        rect_w = avg_size * 0.55
        rect_h = avg_size * 0.45
        text_padding = max(2.0, avg_size * 0.08)

        label_lines = output_label.splitlines() if output_label else []
        label_height = len(label_lines) * label_metrics.height()
        name_height = name_metrics.height() if combo_label else 0
        text_gap = max(1.0, name_metrics.height() * 0.15) if output_label else 0
        needed_height = name_height + label_height + text_gap + (text_padding * 2)
        if needed_height > rect_h:
            rect_h = needed_height

        rect = QRectF(pos.x() - rect_w / 2, pos.y() - rect_h / 2, rect_w, rect_h)
        corner = avg_size * 0.08

        qp.setPen(border_pen)
        qp.setBrush(fill_brush)
        qp.drawRoundedRect(rect, corner, corner)

        qp.setPen(text_pen)
        if output_label:
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

    def _create_pens(self, palette):
        """Create pens and brushes for drawing."""
        fill_color = QColor(palette.color(QPalette.Highlight))
        fill_color.setAlpha(40)
        border_color = QColor(palette.color(QPalette.Highlight))
        border_color.setAlpha(90)
        line_color = QColor(palette.color(QPalette.ButtonText))
        line_color.setAlpha(80)
        text_color = QColor(palette.color(QPalette.ButtonText))
        text_color.setAlpha(160)

        line_pen = QPen(line_color)
        line_pen.setWidthF(1.0)
        border_pen = QPen(border_color)
        border_pen.setWidthF(1.0)
        fill_brush = QBrush(fill_color)
        text_pen = QPen(text_color)

        return line_pen, fill_brush, border_pen, text_pen

    def _create_fonts(self):
        """Create fonts for labels."""
        text_font = QApplication.font()
        base_size = text_font.pointSizeF()
        if base_size <= 0:
            base_size = float(text_font.pointSize())
        text_font.setPointSizeF(max(1.0, base_size * 0.7))

        name_font = QApplication.font()
        name_font.setPointSizeF(max(1.0, base_size * 0.6))

        return name_font, text_font

    def _draw_anchor_dot(self, qp, position, fill_brush, border_pen, avg_size):
        """Draw a small circle at the anchor point."""
        radius = max(2.0, avg_size * 0.05)
        qp.setPen(border_pen)
        qp.setBrush(fill_brush)
        qp.drawEllipse(position, radius, radius)
