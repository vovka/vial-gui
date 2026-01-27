# SPDX-License-Identifier: GPL-2.0-or-later
"""Main orchestrator for alternative combos visualization."""

from typing import List, Tuple
from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPalette
from PyQt5.QtWidgets import QApplication

from .geometry import ComboAnchor, Route
from .boundary_calculator import BoundaryCalculator
from .slot_assigner import SlotAssigner
from .routing_grid import RoutingGrid
from .pathfinder import Pathfinder
from .path_simplifier import PathSimplifier
from .crossing_reducer import CrossingReducer
from .path_renderer import PathRenderer
from .key_connector import KeyConnector


class AltCombosRenderer:
    """Orchestrates the alternative combos visualization pipeline."""

    def __init__(self, margin: float = 30.0, cell_size: float = 4.0):
        self.boundary_calc = BoundaryCalculator(margin=margin)
        self.slot_assigner = SlotAssigner()
        self.pathfinder = Pathfinder(bend_penalty=5.0)
        self.simplifier = PathSimplifier()
        self.crossing_reducer = CrossingReducer()
        self.path_renderer = PathRenderer()
        self.key_connector = KeyConnector()
        self.cell_size = cell_size

    def render(
        self, qp: QPainter, combos: List[Tuple], key_rects: List[QRectF],
        scale: float, avg_size: float
    ):
        """Render all combos with routed paths and boundary labels."""
        if not combos:
            return

        anchors = self._build_anchors(combos)
        boundary = self.boundary_calc.compute_boundary(key_rects)
        slot_count = max(len(anchors) * 2, 20)
        slots = self.boundary_calc.compute_slots(boundary, slot_count)

        assignment = self.slot_assigner.assign(anchors, slots, boundary)
        routes = self._route_all_paths(anchors, slots, assignment, key_rects, boundary)

        self._setup_painter(qp, scale)
        self._draw_all(qp, routes, anchors, slots, assignment, avg_size)
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

    def _route_all_paths(
        self, anchors, slots, assignment, key_rects, boundary
    ) -> List[Route]:
        """Route paths for all combos."""
        grid = RoutingGrid(boundary, self.cell_size)
        grid.mark_obstacles(key_rects, padding=self.cell_size)

        slot_map = {s.index: s for s in slots}
        ordered = self.crossing_reducer.order_combos_for_routing(
            anchors, assignment, slots
        )

        routes = []
        for anchor in ordered:
            slot_idx = assignment.get(anchor.combo_index)
            if slot_idx is None:
                continue
            slot = slot_map.get(slot_idx)
            if slot is None:
                continue

            route = self._route_single(grid, anchor, slot)
            if route:
                grid.mark_used(route.path)
                routes.append(route)

        return routes

    def _route_single(self, grid, anchor, slot) -> Route:
        """Route a single combo to its slot."""
        start = grid.world_to_grid(anchor.position)
        goal = grid.world_to_grid(slot.position)

        path, cost = self.pathfinder.find_path(grid, start, goal)
        simplified = self.simplifier.simplify(grid, path) if path else []

        return Route(anchor.combo_index, slot.index, path or [], simplified, cost)

    def _setup_painter(self, qp: QPainter, scale: float):
        """Setup painter with scale and antialiasing."""
        qp.save()
        qp.scale(scale, scale)
        qp.setRenderHint(QPainter.Antialiasing)

    def _draw_all(self, qp, routes, anchors, slots, assignment, avg_size):
        """Draw all routes and labels."""
        palette = QApplication.palette()
        line_pen, fill_brush, border_pen, text_pen = self._create_pens(palette)
        name_font, text_font = self._create_fonts()

        slot_map = {s.index: s for s in slots}
        anchor_map = {a.combo_index: a for a in anchors}

        for anchor in anchors:
            self.key_connector.render_key_connections(
                qp, anchor.position, anchor.key_rects, line_pen
            )
            self._draw_anchor_dot(qp, anchor.position, fill_brush, border_pen, avg_size)

        for route in routes:
            self.path_renderer.render_route(qp, route, line_pen)

        for route in routes:
            anchor = anchor_map.get(route.combo_index)
            slot = slot_map.get(route.slot_index)
            if anchor and slot:
                self.path_renderer.render_label(
                    qp, slot, anchor.combo_label, anchor.output_label, avg_size,
                    fill_brush, border_pen, text_pen, name_font, text_font
                )

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
