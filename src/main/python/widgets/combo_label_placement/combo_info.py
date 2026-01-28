# SPDX-License-Identifier: GPL-2.0-or-later

class ComboInfo:
    def __init__(self, index, combo_widgets, output_label, combo_label,
                 rect_w, rect_h, avg_size, bbox, anchor, adjacent):
        self.index = index
        self.combo_widgets = combo_widgets
        self.output_label = output_label
        self.combo_label = combo_label
        self.rect_w = rect_w
        self.rect_h = rect_h
        self.avg_size = avg_size
        self.bbox = bbox
        self.anchor = anchor
        self.adjacent = adjacent
