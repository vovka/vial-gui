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
    def ray_rect_edge_intersection(start, rect):
        """Return the rectangle edge intersection from start toward the rect center."""
        center = rect.center()
        if rect.contains(start):
            return center

        dx = center.x() - start.x()
        dy = center.y() - start.y()
        if dx == 0 and dy == 0:
            return center

        candidates = []
        if dx != 0:
            t = (rect.left() - start.x()) / dx
            if 0 <= t <= 1:
                y = start.y() + t * dy
                if rect.top() <= y <= rect.bottom():
                    candidates.append((t, QPointF(rect.left(), y)))
            t = (rect.right() - start.x()) / dx
            if 0 <= t <= 1:
                y = start.y() + t * dy
                if rect.top() <= y <= rect.bottom():
                    candidates.append((t, QPointF(rect.right(), y)))

        if dy != 0:
            t = (rect.top() - start.y()) / dy
            if 0 <= t <= 1:
                x = start.x() + t * dx
                if rect.left() <= x <= rect.right():
                    candidates.append((t, QPointF(x, rect.top())))
            t = (rect.bottom() - start.y()) / dy
            if 0 <= t <= 1:
                x = start.x() + t * dx
                if rect.left() <= x <= rect.right():
                    candidates.append((t, QPointF(x, rect.bottom())))

        if not candidates:
            return center

        _, point = min(candidates, key=lambda item: item[0])
        return point

    @staticmethod
    def _get_rect_edges(rect):
        """Return the four edges of a rectangle as point pairs."""
        return [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top())),
        ]

    @staticmethod
    def closest_rect_corner(point, rect, inset_ratio=0.08):
        """Return the closest rectangle corner to the point, inset slightly."""
        inset_x = rect.width() * inset_ratio
        inset_y = rect.height() * inset_ratio
        corners = [
            QPointF(rect.left() + inset_x, rect.top() + inset_y),
            QPointF(rect.right() - inset_x, rect.top() + inset_y),
            QPointF(rect.right() - inset_x, rect.bottom() - inset_y),
            QPointF(rect.left() + inset_x, rect.bottom() - inset_y),
        ]
        return min(corners, key=lambda c: (c.x() - point.x()) ** 2 + (c.y() - point.y()) ** 2)
