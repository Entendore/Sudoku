import sys
import random
import copy
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLineEdit, QPushButton, QVBoxLayout,
    QFileDialog, QMessageBox, QComboBox, QLabel, QHBoxLayout, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIntValidator, QFont, QColor, QPalette

class SudokuSolver:
    def __init__(self, board):
        self.board = board
        self.steps = []

    def is_valid(self, row, col, num):
        for i in range(9):
            if self.board[row][i] == num or self.board[i][col] == num:
                return False
        start_row, start_col = 3 * (row//3), 3 * (col//3)
        for i in range(3):
            for j in range(3):
                if self.board[start_row+i][start_col+j] == num:
                    return False
        return True

    def solve_with_steps(self):
        for row in range(9):
            for col in range(9):
                if self.board[row][col] == 0:
                    for num in range(1, 10):
                        if self.is_valid(row, col, num):
                            self.board[row][col] = num
                            self.steps.append((row, col, num))
                            if self.solve_with_steps():
                                return True
                            self.board[row][col] = 0
                            self.steps.append((row, col, 0))
                    return False
        return True

    def count_solutions(self, limit=2):
        return self._count_recursive(limit)

    def _count_recursive(self, limit, board=None):
        if board is None:
            board = self.board
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    count = 0
                    for num in range(1, 10):
                        if self.is_valid(row, col, num):
                            board[row][col] = num
                            count += self._count_recursive(limit, board)
                            if count >= limit:
                                board[row][col] = 0
                                return count
                            board[row][col] = 0
                    return count
        return 1

    def get_hint(self, board):
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    for num in range(1, 10):
                        if self.is_valid(row, col, num):
                            explanation = (
                                f"Placing {num} at ({row+1},{col+1}) is valid because:\n"
                                f"- Row {row+1} has no {num}\n"
                                f"- Column {col+1} has no {num}\n"
                                f"- 3x3 box starting at ({3*(row//3)+1},{3*(col//3)+1}) has no {num}"
                            )
                            return row, col, num, explanation
        return None

class SudokuGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Solver")
        self.grid_cells = [[None for _ in range(9)] for _ in range(9)]
        self.solver = None
        self.solve_timer = QTimer()
        self.step_index = 0
        self.undo_stack = []
        self.redo_stack = []
        self.solve_delay = 50  # ms
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()
        font = QFont("Arial", 16)

        for i in range(9):
            for j in range(9):
                cell = QLineEdit()
                cell.setFixedSize(50, 50)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFont(font)
                cell.setValidator(QIntValidator(1, 9))
                cell.old_text = ""
                cell.textChanged.connect(lambda text, r=i, c=j, cell=cell: self.cell_changed(r, c, cell, text))
                self.grid_cells[i][j] = cell
                grid_layout.addWidget(cell, i, j)

        main_layout.addLayout(grid_layout)

        # Difficulty selector
        diff_layout = QHBoxLayout()
        diff_label = QLabel("Difficulty:")
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(["Easy", "Medium", "Hard"])
        diff_layout.addWidget(diff_label)
        diff_layout.addWidget(self.diff_combo)
        main_layout.addLayout(diff_layout)

        # Buttons
        button_layout = QHBoxLayout()
        solve_button = QPushButton("Solve")
        solve_button.clicked.connect(self.start_animation)
        hint_button = QPushButton("Hint")
        hint_button.clicked.connect(lambda: self.give_hint(animate=True))
        undo_button = QPushButton("Undo")
        undo_button.clicked.connect(self.undo)
        redo_button = QPushButton("Redo")
        redo_button.clicked.connect(self.redo)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_grid)
        load_button = QPushButton("Load Puzzle")
        load_button.clicked.connect(self.load_puzzle)
        save_button = QPushButton("Save Puzzle")
        save_button.clicked.connect(lambda: self.save_puzzle(solution=False))
        save_sol_button = QPushButton("Save Solution")
        save_sol_button.clicked.connect(lambda: self.save_puzzle(solution=True))
        random_button = QPushButton("Random Puzzle")
        random_button.clicked.connect(self.random_puzzle)
        button_layout.addWidget(solve_button)
        button_layout.addWidget(hint_button)
        button_layout.addWidget(undo_button)
        button_layout.addWidget(redo_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(load_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(save_sol_button)
        button_layout.addWidget(random_button)
        main_layout.addLayout(button_layout)

        # Hint display
        self.hint_display = QTextEdit()
        self.hint_display.setReadOnly(True)
        main_layout.addWidget(self.hint_display)

        self.setLayout(main_layout)
        self.solve_timer.timeout.connect(self.animate_step)

    # ------------------- Board Functions -------------------
    def get_board(self):
        return [
            [int(self.grid_cells[i][j].text()) if self.grid_cells[i][j].text().isdigit() else 0
             for j in range(9)] for i in range(9)
        ]

    def set_board(self, board):
        for i in range(9):
            for j in range(9):
                self.grid_cells[i][j].setText(str(board[i][j]) if board[i][j] != 0 else "")

    # ------------------- Cell Change Tracking -------------------
    def cell_changed(self, row, col, cell, new_text):
        old_value = int(cell.old_text) if cell.old_text.isdigit() else 0
        new_value = int(new_text) if new_text.isdigit() else 0
        if old_value != new_value:
            self.undo_stack.append((row, col, old_value))
            self.redo_stack.clear()
        cell.old_text = new_text
        self.highlight_invalid()

    def undo(self):
        if not self.undo_stack:
            return
        row, col, value = self.undo_stack.pop()
        cell = self.grid_cells[row][col]
        current_value = int(cell.text()) if cell.text().isdigit() else 0
        self.redo_stack.append((row, col, current_value))
        cell.setText(str(value) if value != 0 else "")

    def redo(self):
        if not self.redo_stack:
            return
        row, col, value = self.redo_stack.pop()
        cell = self.grid_cells[row][col]
        current_value = int(cell.text()) if cell.text().isdigit() else 0
        self.undo_stack.append((row, col, current_value))
        cell.setText(str(value) if value != 0 else "")

    # ------------------- Highlight Invalid -------------------
    def highlight_invalid(self):
        board = self.get_board()
        for i in range(9):
            for j in range(9):
                cell = self.grid_cells[i][j]
                palette = cell.palette()
                text = cell.text()
                if text.isdigit() and int(text) != 0:
                    solver = SudokuSolver(board)
                    if not solver.is_valid(i, j, int(text)):
                        palette.setColor(QPalette.ColorRole.Base, QColor("#FFAAAA"))
                    else:
                        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
                else:
                    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
                cell.setPalette(palette)

    # ------------------- Solver Animation -------------------
    def start_animation(self):
        board = self.get_board()
        self.solver = SudokuSolver(copy.deepcopy(board))
        if self.solver.solve_with_steps():
            self.step_index = 0
            self.solve_timer.start(self.solve_delay)
        else:
            QMessageBox.warning(self, "No Solution", "This puzzle has no solution.")

    def animate_step(self):
        if self.step_index < len(self.solver.steps):
            row, col, value = self.solver.steps[self.step_index]
            self.grid_cells[row][col].setText(str(value) if value != 0 else "")
            palette = self.grid_cells[row][col].palette()
            palette.setColor(QPalette.ColorRole.Base, QColor("#DDFFDD") if value != 0 else QColor("#FFDDDD"))
            self.grid_cells[row][col].setPalette(palette)
            self.step_index += 1
        else:
            for i in range(9):
                for j in range(9):
                    palette = self.grid_cells[i][j].palette()
                    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
                    self.grid_cells[i][j].setPalette(palette)
            self.solve_timer.stop()

    # ------------------- Hints -------------------
    def give_hint(self, animate=True):
        board = self.get_board()
        solver = SudokuSolver(copy.deepcopy(board))
        hint = solver.get_hint(board)
        if hint is None:
            QMessageBox.information(self, "No Hint", "No empty cells or no valid hint.")
            return
        row, col, num, explanation = hint
        self.hint_display.setText(explanation)
        if animate:
            self.grid_cells[row][col].setText("")
            QTimer.singleShot(500, lambda r=row, c=col, n=num: self.grid_cells[r][c].setText(str(n)))
        else:
            self.grid_cells[row][col].setText(str(num))

    # ------------------- File Handling -------------------
    def load_puzzle(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Puzzle", "", "Text Files (*.txt);;CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, "r") as f:
                    board = []
                    for line in f:
                        row = [int(n) if n.isdigit() else 0 for n in line.strip().split(",")]
                        board.append(row)
                    if len(board) == 9 and all(len(r) == 9 for r in board):
                        self.set_board(board)
                    else:
                        QMessageBox.warning(self, "Error", "Invalid puzzle format (must be 9x9).")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def save_puzzle(self, solution=False):
        board = self.get_board()
        if solution:
            solver = SudokuSolver(copy.deepcopy(board))
            if not solver.solve_with_steps():
                QMessageBox.warning(self, "No Solution", "Cannot save solution: puzzle unsolvable.")
                return
            board = solver.board
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Puzzle", "", "Text Files (*.txt);;CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name, "w") as f:
                    for row in board:
                        f.write(",".join(str(num) for num in row) + "\n")
                QMessageBox.information(self, "Saved", "Puzzle saved successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ------------------- Clear / Random Puzzle -------------------
    def clear_grid(self):
        self.set_board([[0]*9 for _ in range(9)])

    def random_puzzle(self):
        while True:
            board = [[0]*9 for _ in range(9)]
            solver = SudokuSolver(board)
            solver.solve_with_steps()
            puzzle = copy.deepcopy(solver.board)

            difficulty = self.diff_combo.currentText()
            if difficulty == "Easy":
                cells_to_remove = random.randint(30, 35)
            elif difficulty == "Medium":
                cells_to_remove = random.randint(40, 45)
            else:
                cells_to_remove = random.randint(50, 55)

            removed = 0
            while removed < cells_to_remove:
                i, j = random.randint(0, 8), random.randint(0, 8)
                if puzzle[i][j] != 0:
                    temp = puzzle[i][j]
                    puzzle[i][j] = 0
                    temp_solver = SudokuSolver(copy.deepcopy(puzzle))
                    if temp_solver.count_solutions() == 1:
                        removed += 1
                    else:
                        puzzle[i][j] = temp
            self.set_board(puzzle)
            break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SudokuGUI()
    window.show()
    sys.exit(app.exec())
