"""Simple 2D point class for combo visualization geometry."""

from math import sqrt


class Point:
    """Represents a 2D point with basic vector operations."""

    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Point':
        return Point(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Point':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Point':
        return Point(self.x / scalar, self.y / scalar)

    def __abs__(self) -> float:
        return sqrt(self.x ** 2 + self.y ** 2)

    def __repr__(self) -> str:
        return f"Point({self.x:.1f}, {self.y:.1f})"

    def to_tuple(self) -> tuple:
        return (self.x, self.y)

    @classmethod
    def from_qpoint(cls, qpoint) -> 'Point':
        """Create Point from QPointF or QPoint."""
        return cls(qpoint.x(), qpoint.y())
