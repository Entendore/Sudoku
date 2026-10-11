"""
NumButton — Custom widget showing digit with remaining count
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal


class NumButton(QFrame):
    clicked = Signal(int)

    def __init__(self, num, parent=None):
        super().__init__(parent)
        self.num = num
        self.setFixedSize(68, 56)
        self.setCursor(Qt.PointingHandCursor)
        self._count = 9

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 4, 2, 4)
        lay.setSpacing(0)

        self.num_lbl = QLabel(str(num))
        self.num_lbl.setAlignment(Qt.AlignCenter)
        self.num_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.cnt_lbl = QLabel("×9")
        self.cnt_lbl.setAlignment(Qt.AlignCenter)
        self.cnt_lbl.setFont(QFont("Segoe UI", 9))

        lay.addWidget(self.num_lbl)
        lay.addWidget(self.cnt_lbl)

    def set_count(self, c):
        self._count = c
        self.cnt_lbl.setText(f"×{c}")
        self.setEnabled(c > 0)

    def mousePressEvent(self, e):
        if self.isEnabled() and e.button() == Qt.LeftButton:
            self.clicked.emit(self.num)