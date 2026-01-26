"""Geometric calculations for combo visualization."""

from PyQt5.QtCore import QPointF


class ComboGeometry:
    """Handles geometric calculations for line intersections and collisions."""

    @staticmethod
    def segments_intersect(p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects with p3-p4."""
        def ccw(a, b, c):
            return (c.y() - a.y()) * (b.x() - a.x()) > (b.y() - a.y()) * (c.x() - a.x())
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

    @staticmethod
    def line_intersection(p1, p2, p3, p4):
        """Find intersection point of two line segments, or None."""
        x1, y1, x2, y2 = p1.x(), p1.y(), p2.x(), p2.y()
        x3, y3, x4, y4 = p3.x(), p3.y(), p4.x(), p4.y()

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

        if 0 <= t <= 1 and 0 <= u <= 1:
            return QPointF(x1 + t * (x2 - x1), y1 + t * (y2 - y1))
        return None

    @staticmethod
    def line_crosses_rect(p1, p2, rect, margin_ratio=0.15):
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
