"""
Premium Sudoku Application — Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication

from Sudoku.old.window import SudokuWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = SudokuWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()