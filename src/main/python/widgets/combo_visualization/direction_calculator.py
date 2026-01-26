"""Direction calculation for combo label placement."""


class DirectionCalculator:
    """Calculates preferred label placement direction based on key positions."""

    @staticmethod
    def compute(combo_centers, all_key_centers, canvas_width, canvas_height):
        """Compute preferred directions for label placement."""
        if not combo_centers:
            return ['above', 'below', 'right', 'left']

        avg_x = sum(c.x() for c in combo_centers) / len(combo_centers)
        avg_y = sum(c.y() for c in combo_centers) / len(combo_centers)

        kb_center_x, kb_center_y = canvas_width / 2, canvas_height / 2
        if all_key_centers:
            kb_center_x = sum(c.x() for c in all_key_centers) / len(all_key_centers)
            kb_center_y = sum(c.y() for c in all_key_centers) / len(all_key_centers)

        dx, dy = avg_x - kb_center_x, avg_y - kb_center_y

        if abs(dx) > abs(dy):
            if dx > 0:
                return ['right', 'above', 'below', 'left']
            return ['left', 'above', 'below', 'right']
        if dy > 0:
            return ['below', 'right', 'left', 'above']
        return ['above', 'right', 'left', 'below']
