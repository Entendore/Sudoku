"""
SudokuWindow — Main application window with all UI and game logic
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox, QFrame,
    QCheckBox, QMessageBox, QFileDialog
)
from PySide6.QtGui import QFont, QColor, QKeySequence, QShortcut
from PySide6.QtCore import QTimer, Qt

from Sudoku.old.engine import SudokuEngine
from Sudoku.old.num_button import NumButton
from Sudoku.old.board import SudokuBoard
from Sudoku.old.themes import (
    get_base_stylesheet, get_button_stylesheet,
    get_hint_highlight_color, get_solve_place_colors, get_solve_remove_colors
)


class SudokuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku")
        self.setMinimumSize(760, 540)
        self.resize(850, 620)

        self.solution = None
        self.undo_stack: list = []
        self.redo_stack: list = []
        self.notes_mode = False
        self.auto_check = True
        self.dark_mode = False
        self.elapsed = 0
        self.timer_on = False
        self.solving = False
        self._solve_steps = []
        self._solve_idx = 0

        self._build_ui()
        self._apply_theme()
        self._connect()
        self._shortcuts()
        self._new_game()

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        root = QHBoxLayout(cw)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(18)

        self.board = SudokuBoard()
        root.addWidget(self.board, 1)

        panel = QWidget()
        panel.setFixedWidth(270)
        pl = QVBoxLayout(panel)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(10)

        # Timer row
        tr = QHBoxLayout()
        tr.addWidget(self._icon_label("⏱"))
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setFont(QFont("Consolas", 18, QFont.Bold))
        tr.addWidget(self.timer_lbl)
        tr.addStretch()
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(42, 42)
        self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setToolTip("Toggle theme")
        tr.addWidget(self.theme_btn)
        pl.addLayout(tr)

        # Toggles
        tg = QHBoxLayout()
        self.notes_btn = QPushButton("✏ Notes")
        self.notes_btn.setCheckable(True)
        self.notes_btn.setObjectName("toggleBtn")
        self.auto_cb = QCheckBox("Auto-check")
        self.auto_cb.setChecked(True)
        tg.addWidget(self.notes_btn)
        tg.addWidget(self.auto_cb)
        pl.addLayout(tg)

        # Numpad
        ng = QGridLayout()
        ng.setSpacing(5)
        self.num_btns: list[NumButton] = []
        for i in range(9):
            b = NumButton(i + 1)
            b.setObjectName("numBtn")
            self.num_btns.append(b)
            ng.addWidget(b, i // 3, i % 3)
        self.erase_btn = QPushButton("⌫  Erase")
        self.erase_btn.setFixedHeight(42)
        self.erase_btn.setObjectName("actionBtn")
        ng.addWidget(self.erase_btn, 3, 0, 1, 3)
        pl.addLayout(ng)

        # Action buttons
        ag = QGridLayout()
        ag.setSpacing(5)
        self.undo_btn = QPushButton("↩ Undo")
        self.redo_btn = QPushButton("↪ Redo")
        self.hint_btn = QPushButton("💡 Hint")
        self.check_btn = QPushButton("✓ Check")
        self.solve_btn = QPushButton("▶ Solve")
        self.new_btn = QPushButton("🔄 New Game")
        for b in (self.undo_btn, self.redo_btn, self.hint_btn,
                  self.check_btn, self.solve_btn, self.new_btn):
            b.setFixedHeight(38)
            b.setObjectName("actionBtn")
        ag.addWidget(self.undo_btn, 0, 0)
        ag.addWidget(self.redo_btn, 0, 1)
        ag.addWidget(self.hint_btn, 1, 0)
        ag.addWidget(self.check_btn, 1, 1)
        ag.addWidget(self.solve_btn, 2, 0)
        ag.addWidget(self.new_btn, 2, 1)
        pl.addLayout(ag)

        # Difficulty
        dr = QHBoxLayout()
        dr.addWidget(QLabel("Difficulty:"))
        self.diff_cb = QComboBox()
        self.diff_cb.addItems(["Easy", "Medium", "Hard"])
        self.diff_cb.setCurrentIndex(1)
        self.diff_cb.setFixedWidth(100)
        dr.addWidget(self.diff_cb)
        dr.addStretch()
        pl.addLayout(dr)

        # Hint area
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        pl.addWidget(sep)

        self.hint_lbl = QLabel("Select a cell and enter a number,\nor press Hint for help.")
        self.hint_lbl.setWordWrap(True)
        self.hint_lbl.setMinimumHeight(80)
        self.hint_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hint_lbl.setObjectName("hintLabel")
        pl.addWidget(self.hint_lbl)

        # Keyboard hint
        kb = QLabel("Keys: 1-9 • Del • N (notes) • Arrows")
        kb.setObjectName("keyHint")
        pl.addWidget(kb)

        pl.addStretch()
        root.addWidget(panel)

        self._solve_timer = QTimer(self)
        self._solve_timer.timeout.connect(self._anim_step)

    @staticmethod
    def _icon_label(text):
        l = QLabel(text)
        l.setFont(QFont("Segoe UI", 16))
        return l

    # ── Theme ─────────────────────────────────────────────────

    def _apply_theme(self):
        self.board.set_dark(self.dark_mode)
        self.setStyleSheet(get_base_stylesheet(self.dark_mode))
        self._btn_ss = get_button_stylesheet(self.dark_mode)
        for b in (self.notes_btn, self.erase_btn, self.undo_btn, self.redo_btn,
                  self.hint_btn, self.check_btn, self.solve_btn, self.new_btn, self.theme_btn):
            b.setStyleSheet(self._btn_ss)
        for nb in self.num_btns:
            nb.setStyleSheet(self._btn_ss)

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
        self._apply_theme()

    # ── Connections ───────────────────────────────────────────

    def _connect(self):
        self.board.cellClicked.connect(self._on_cell)
        self.board.numberInput.connect(self._on_num)
        self.board.eraseInput.connect(self._on_erase)
        self.board.noteToggled.connect(self._toggle_notes)

        for i, nb in enumerate(self.num_btns):
            nb.clicked.connect(lambda n=i + 1: self._on_num(n))
        self.erase_btn.clicked.connect(self._on_erase)
        self.notes_btn.clicked.connect(self._toggle_notes)
        self.auto_cb.toggled.connect(lambda v: setattr(self, "auto_check", v))
        self.undo_btn.clicked.connect(self._undo)
        self.redo_btn.clicked.connect(self._redo)
        self.hint_btn.clicked.connect(self._hint)
        self.check_btn.clicked.connect(self._check)
        self.solve_btn.clicked.connect(self._start_solve)
        self.new_btn.clicked.connect(self._new_game)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.diff_cb.currentTextChanged.connect(lambda _: self._new_game())

    def _shortcuts(self):
        for key, fn in [
            (QKeySequence("Ctrl+Z"), self._undo),
            (QKeySequence("Ctrl+Y"), self._redo),
            (QKeySequence("Ctrl+N"), self._new_game),
            (QKeySequence("H"), self._hint),
            (QKeySequence("Ctrl+D"), self._toggle_theme),
        ]:
            s = QShortcut(key, self)
            s.activated.connect(fn)

    # ── Timer ─────────────────────────────────────────────────

    def _start_timer(self):
        self.elapsed = 0
        self.timer_on = True
        self._update_timer()
        if not hasattr(self, "_tick"):
            self._tick = QTimer(self)
            self._tick.timeout.connect(self._tick_timer)
        self._tick.start(1000)

    def _tick_timer(self):
        if self.timer_on:
            self.elapsed += 1
            self._update_timer()

    def _update_timer(self):
        m, s = divmod(self.elapsed, 60)
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

    def _stop_timer(self):
        self.timer_on = False

    # ── Game logic ────────────────────────────────────────────

    def _new_game(self):
        self._stop_solving()
        diff = self.diff_cb.currentText().lower()
        puzzle, solution = SudokuEngine.generate(diff)
        self.solution = solution
        self.board.load(puzzle)
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.notes_mode = False
        self.notes_btn.setChecked(False)
        self.board.notes_mode = False
        self.hint_lbl.setText("New puzzle generated.\nGood luck!")
        self._update_counts()
        self._start_timer()

    def _on_cell(self, r, c):
        if not self.solving:
            cd = self.board.cells[r][c]
            status = ""
            if cd.is_given:
                status = f"R{r + 1}C{c + 1}: Given clue ({cd.value})"
            elif cd.value:
                status = f"R{r + 1}C{c + 1}: You placed {cd.value}"
            elif cd.notes:
                status = f"R{r + 1}C{c + 1}: Notes: {', '.join(map(str, sorted(cd.notes)))}"
            else:
                status = f"R{r + 1}C{c + 1}: Empty"
            self.hint_lbl.setText(status)

    def _on_num(self, n):
        if self.solving:
            return
        r, c = self.board.selected
        if (r, c) == (-1, -1):
            return
        if self.notes_mode:
            old = self.board.cell_data(r, c)
            if self.board.toggle_note(r, c, n):
                self.undo_stack.append((r, c, old[0], old[1], old[2], self.board.cell_data(r, c)[2]))
                self.redo_stack.clear()
        else:
            old = self.board.cell_data(r, c)
            if self.board.set_value(r, c, n):
                self.undo_stack.append((r, c, old[0], old[1], old[2], frozenset()))
                self.redo_stack.clear()
                self.board.remove_note_from_peers(r, c, n)
                if self.auto_check:
                    self._auto_validate(r, c, n)
                self._check_win()
        self._update_counts()

    def _on_erase(self):
        if self.solving:
            return
        r, c = self.board.selected
        if (r, c) == (-1, -1):
            return
        old = self.board.cell_data(r, c)
        if self.board.clear_cell(r, c):
            self.undo_stack.append((r, c, old[0], old[1], old[2], frozenset()))
            self.redo_stack.clear()
            if self.auto_check:
                self._do_check()
            self._update_counts()

    def _toggle_notes(self):
        self.notes_mode = not self.notes_mode
        self.notes_btn.setChecked(self.notes_mode)
        self.board.notes_mode = self.notes_mode

    def _auto_validate(self, row, col, num):
        b = self.board.board()
        errs = set()
        for i in range(9):
            if b[row][i] == num and i != col and not self.board.cells[row][i].is_given:
                errs.add((row, i))
            if b[i][col] == num and i != row and not self.board.cells[i][col].is_given:
                errs.add((i, col))
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if b[r][c] == num and (r, c) != (row, col) and not self.board.cells[r][c].is_given:
                    errs.add((r, c))
        if not SudokuEngine.is_valid(b, row, col, num):
            errs.add((row, col))
        self.board.mark_errors(errs)

    def _do_check(self):
        b = self.board.board()
        errs = set()
        for r in range(9):
            for c in range(9):
                if b[r][c] and not self.board.cells[r][c].is_given:
                    if not SudokuEngine.is_valid(b, r, c, b[r][c]):
                        errs.add((r, c))
        self.board.mark_errors(errs)
        return len(errs)

    def _check(self):
        if self.solving:
            return
        n = self._do_check()
        if n == 0:
            b = self.board.board()
            empty = sum(1 for r in range(9) for c in range(9) if b[r][c] == 0)
            if empty:
                self.hint_lbl.setText(f"✓ No conflicts found!\n{empty} cells remaining.")
            else:
                self.hint_lbl.setText("✓ Perfect! Puzzle solved correctly!")
        else:
            self.hint_lbl.setText(f"✗ Found {n} conflicting cell(s).\nHighlighted in red.")

    def _hint(self):
        if self.solving:
            return
        b = self.board.board()
        h = SudokuEngine.get_hint(b)
        if h is None:
            self.hint_lbl.setText("No empty cells left.")
            return
        r, c, n, txt = h
        self.board.selected = (r, c)
        self.board.cellClicked.emit(r, c)
        self.board.update()
        self.hint_lbl.setText(f"💡 {txt}\n\nPress {n} to place it.")
        self._highlight_hint_cell(r, c)

    def _highlight_hint_cell(self, r, c):
        color = get_hint_highlight_color(self.dark_mode)
        self.board.anim_cell(r, c, QColor(color))
        QTimer.singleShot(2000, self.board.clear_anim)

    def _undo(self):
        if self.solving or not self.undo_stack:
            return
        r, c, old_v, old_g, old_n, _ = self.undo_stack.pop()
        cur = self.board.cell_data(r, c)
        cd = self.board.cells[r][c]
        cd.value = old_v
        cd.notes = set(old_n)
        cd.is_given = old_g
        cd.is_error = False
        self.redo_stack.append((r, c, cur[0], cur[1], cur[2], old_n))
        self.board.update()
        if self.auto_check:
            self._do_check()
        self._update_counts()

    def _redo(self):
        if self.solving or not self.redo_stack:
            return
        r, c, old_v, old_g, old_n, new_n = self.redo_stack.pop()
        cur = self.board.cell_data(r, c)
        cd = self.board.cells[r][c]
        cd.value = old_v
        cd.notes = set(new_n)
        cd.is_given = old_g
        cd.is_error = False
        self.undo_stack.append((r, c, cur[0], cur[1], cur[2], new_n))
        self.board.update()
        if self.auto_check:
            self._do_check()
        self._update_counts()

    def _check_win(self):
        b = self.board.board()
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0:
                    return
        for r in range(9):
            for c in range(9):
                if not SudokuEngine.is_valid(b, r, c, b[r][c]):
                    return
        self._stop_timer()
        self.board.set_solved()
        m, s = divmod(self.elapsed, 60)
        self.hint_lbl.setText(
            f"🎉 Congratulations!\n\n"
            f"Puzzle solved in {m:02d}:{s:02d}\n"
            f"Difficulty: {self.diff_cb.currentText()}"
        )

    # ── Numpad counts ─────────────────────────────────────────

    def _update_counts(self):
        b = self.board.board()
        for n in range(1, 10):
            cnt = sum(1 for r in range(9) for c in range(9) if b[r][c] == n)
            self.num_btns[n - 1].set_count(9 - cnt)

    # ── Animated solver ───────────────────────────────────────

    def _start_solve(self):
        if self.solving:
            return
        b = self.board.board()
        test = [row[:] for row in b]
        if not SudokuEngine.solve(test):
            self.hint_lbl.setText("✗ This puzzle has no solution.")
            return
        self._solve_steps = SudokuEngine.solve_with_steps(b)
        self._solve_idx = 0
        self.solving = True
        self._stop_timer()
        self.solve_btn.setText("⏹ Stop")
        self.solve_btn.clicked.disconnect()
        self.solve_btn.clicked.connect(self._stop_solving)
        self.board.clear_errors()
        self._solve_timer.start(8)

    def _anim_step(self):
        if self._solve_idx >= len(self._solve_steps):
            self._stop_solving()
            self.board.clear_anim()
            self._update_counts()
            self._check_win()
            return
        r, c, v, act = self._solve_steps[self._solve_idx]
        if act == "place":
            self.board.cells[r][c].value = v
            flash, fade = get_solve_place_colors(self.dark_mode)
            self.board.anim_cell(r, c, QColor(flash))
            QTimer.singleShot(30, lambda: self.board.anim_cell(r, c, QColor(fade)))
        else:
            self.board.cells[r][c].value = 0
            flash, fade = get_solve_remove_colors(self.dark_mode)
            self.board.anim_cell(r, c, QColor(flash))
            QTimer.singleShot(30, lambda: self.board.anim_cell(r, c, QColor(fade)))
        self._solve_idx += 1
        self.board.update()

    def _stop_solving(self):
        self._solve_timer.stop()
        self.solving = False
        self.board.clear_anim()
        self.solve_btn.setText("▶ Solve")
        self.solve_btn.clicked.disconnect()
        self.solve_btn.clicked.connect(self._start_solve)
        self._update_counts()

    # ── Save / Load ───────────────────────────────────────────

    def save_puzzle(self, with_solution=False):
        b = self.board.board()
        if with_solution:
            test = [row[:] for row in b]
            if not SudokuEngine.solve(test):
                QMessageBox.warning(self, "Error", "Cannot solve this puzzle.")
                return
            b = test
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "Text Files (*.txt)")
        if path:
            with open(path, "w") as f:
                for row in b:
                    f.write(",".join(str(x) for x in row) + "\n")

    def load_puzzle(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load", "", "Text Files (*.txt)")
        if not path:
            return
        try:
            with open(path) as f:
                lines = [l.strip() for l in f if l.strip()]
            board = []
            for line in lines:
                row = [int(x) if x.strip().isdigit() else 0 for x in line.split(",")]
                board.append(row)
            if len(board) != 9 or any(len(r) != 9 for r in board):
                raise ValueError
            self._stop_solving()
            self.solution = None
            self.board.load(board)
            self.undo_stack.clear()
            self.redo_stack.clear()
            self._update_counts()
            self._start_timer()
            self.hint_lbl.setText("Puzzle loaded from file.")
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid puzzle file (need 9×9 comma-separated).")

    # ── Override close for clean shutdown ─────────────────────

    def closeEvent(self, e):
        self._stop_solving()
        self._stop_timer()
        super().closeEvent(e)