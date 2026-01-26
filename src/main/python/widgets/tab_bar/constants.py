# SPDX-License-Identifier: GPL-2.0-or-later
from PyQt5.QtGui import QColor

# Tab states
TAB_STATE_USED = 0        # Normal, configured and used
TAB_STATE_FREE = 1        # Empty/unconfigured (italic)
TAB_STATE_ATTENTION = 2   # Configured but needs attention (has "!" suffix)

# Drag-and-drop constants
DRAG_START_DISTANCE = 10  # Minimum distance to move before starting a drag
SWAP_ZONE_RATIO = 0.25    # Middle portion of tab for swap mode (0.25 = middle 50%)

# Visual feedback colors
DROP_INDICATOR_COLOR = QColor(0, 120, 215)
SWAP_HIGHLIGHT_COLOR = QColor(0, 120, 215, 80)
