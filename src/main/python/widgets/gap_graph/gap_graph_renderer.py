# SPDX-License-Identifier: GPL-2.0-or-later

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor


class GapGraphRenderer:
    """Renders gap graph nodes and edges for debugging visualization."""

    def __init__(self, node_radius=4.0):
        self.node_radius = node_radius

    def render(self, painter, graph, scale=1.0):
        """Render the gap graph with nodes as circles and edges as lines."""
        painter.save()
        painter.scale(scale, scale)
        self._draw_edges(painter, graph)
        self._draw_nodes(painter, graph)
        painter.restore()

    def _draw_edges(self, painter, graph):
        """Draw edges between connected nodes."""
        edge_color = QColor(100, 100, 255, 80)
        edge_pen = QPen(edge_color)
        edge_pen.setWidthF(1.5)
        painter.setPen(edge_pen)
        painter.setBrush(Qt.NoBrush)
        drawn = set()
        for node in graph.nodes:
            for neighbor in node.neighbors:
                edge_key = tuple(sorted([node.node_id, neighbor.node_id]))
                if edge_key not in drawn:
                    drawn.add(edge_key)
                    painter.drawLine(node.position, neighbor.position)

    def _draw_nodes(self, painter, graph):
        """Draw nodes as circles."""
        node_color = QColor(255, 100, 100, 180)
        leaf_color = QColor(100, 255, 100, 180)
        border_color = QColor(50, 50, 50, 200)
        border_pen = QPen(border_color)
        border_pen.setWidthF(1.0)
        for node in graph.nodes:
            color = leaf_color if node.is_leaf() else node_color
            painter.setPen(border_pen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                node.position,
                self.node_radius,
                self.node_radius
            )

    def render_path(self, painter, path, scale=1.0):
        """Render a routed path as a polyline."""
        if len(path) < 2:
            return
        painter.save()
        painter.scale(scale, scale)
        path_color = QColor(255, 150, 50, 200)
        path_pen = QPen(path_color)
        path_pen.setWidthF(2.0)
        painter.setPen(path_pen)
        painter.setBrush(Qt.NoBrush)
        for i in range(len(path) - 1):
            p1 = path[i] if isinstance(path[i], QPointF) else QPointF(*path[i])
            p2 = path[i+1] if isinstance(path[i+1], QPointF) else QPointF(*path[i+1])
            painter.drawLine(p1, p2)
        painter.restore()
