# SPDX-License-Identifier: GPL-2.0-or-later

from dataclasses import dataclass


@dataclass(frozen=True)
class ComboInfo:
    index: int
    combo_widgets: list
    output_label: str
    combo_label: str
    rect_w: float
    rect_h: float
    avg_size: float
    bbox: object
    anchor: object
    adjacent: bool
