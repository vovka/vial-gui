"""Geometric calculations for combo visualization."""

from PyQt5.QtCore import QPointF

RECT_INTERIOR_MARGIN = 0.15


class ComboGeometry:
    """Handles geometric calculations for line intersections and collisions."""

    @staticmethod
    def segments_intersect(p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects with p3-p4."""
        def ccw(a, b, c):
            return (c.y() - a.y()) * (b.x() - a.x()) > (b.y() - a.y()) * (c.x() - a.x())
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    @staticmethod
    def line_crosses_rect(p1, p2, rect, margin_ratio=RECT_INTERIOR_MARGIN):
        """Check if line crosses through rectangle interior."""
        shrunk = rect.adjusted(
            rect.width() * margin_ratio, rect.height() * margin_ratio,
            -rect.width() * margin_ratio, -rect.height() * margin_ratio
        )
        edges = ComboGeometry._get_rect_edges(shrunk)
        return any(ComboGeometry.segments_intersect(p1, p2, e1, e2) for e1, e2 in edges)

    @staticmethod
    def _get_rect_edges(rect):
        """Return the four edges of a rectangle as point pairs."""
        return [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top())),
        ]
