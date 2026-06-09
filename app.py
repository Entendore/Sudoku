#!/usr/bin/env python3
"""
Premium Sudoku Application — Single File Edition

Features:
  • 9×9 Sudoku with Easy / Medium / Hard difficulties
  • Dark / Light theme with polished visuals
  • Notes (pencil marks) mode
  • Auto-check conflicts  &  manual Check button
  • Full Undo / Redo (including batch auto-notes undo)
  • Hint system with naked-single & hidden-single explanations
  • Animated solver visualisation
  • Pause / Resume with board overlay
  • Mistake counter (compared to solution)
  • Auto-Notes (fill all candidates)
  • Save / Load puzzle as text   &   Save / Load full game state as JSON
  • Menu bar with keyboard shortcuts
  • Status bar
  • Full keyboard + mouse support

Requirements:  pip install PySide6
"""

import sys, json, random
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QComboBox, QFrame,
    QCheckBox, QMessageBox, QFileDialog, QSizePolicy,
    QDialog, QDialogButtonBox, QTextEdit,
)
from PySide6.QtGui import (
    QFont, QColor, QPen, QPainter, QKeySequence, QShortcut, QAction,
)
from PySide6.QtCore import QTimer, Qt, Signal, QRectF, QPointF


# ═══════════════════════════════════════════════════════════════════════
#  SUDOKU ENGINE — Pure logic (no UI)
# ═══════════════════════════════════════════════════════════════════════

class SudokuEngine:

    @staticmethod
    def is_valid(board, row, col, num):
        for i in range(9):
            if i != col and board[row][i] == num:
                return False
            if i != row and board[i][col] == num:
                return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if (r != row or c != col) and board[r][c] == num:
                    return False
        return True

    @staticmethod
    def solve(board):
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    for n in range(1, 10):
                        if SudokuEngine.is_valid(board, r, c, n):
                            board[r][c] = n
                            if SudokuEngine.solve(board):
                                return True
                            board[r][c] = 0
                    return False
        return True

    @staticmethod
    def count_solutions(board, limit=2):
        def _cnt(b):
            for r in range(9):
                for c in range(9):
                    if b[r][c] == 0:
                        t = 0
                        for n in range(1, 10):
                            if SudokuEngine.is_valid(b, r, c, n):
                                b[r][c] = n
                                t += _cnt(b)
                                b[r][c] = 0
                                if t >= limit:
                                    return t
                        return t
            return 1
        return _cnt([row[:] for row in board])

    @staticmethod
    def solve_with_steps(board):
        steps = []
        def _go(b):
            for r in range(9):
                for c in range(9):
                    if b[r][c] == 0:
                        for n in range(1, 10):
                            if SudokuEngine.is_valid(b, r, c, n):
                                b[r][c] = n
                                steps.append((r, c, n, "place"))
                                if _go(b):
                                    return True
                                b[r][c] = 0
                                steps.append((r, c, 0, "remove"))
                        return False
            return True
        _go([row[:] for row in board])
        return steps

    @staticmethod
    def get_hint(board):
        # ── Naked singles ─────────────────────────────────────
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    cands = [n for n in range(1, 10)
                             if SudokuEngine.is_valid(board, r, c, n)]
                    if len(cands) == 1:
                        n = cands[0]
                        return (r, c, n,
                                f"R{r+1}C{c+1}: Naked Single — only {n} fits.\n"
                                f"Row, column & box block all other digits.")
        # ── Hidden singles in rows ────────────────────────────
        for r in range(9):
            for n in range(1, 10):
                if n not in board[r]:
                    pos = [c for c in range(9)
                           if board[r][c] == 0
                           and SudokuEngine.is_valid(board, r, c, n)]
                    if len(pos) == 1:
                        c = pos[0]
                        return (r, c, n,
                                f"R{r+1}C{c+1}: Hidden Single in row — "
                                f"{n} can only go here in row {r+1}.")
        # ── Hidden singles in columns ─────────────────────────
        for c in range(9):
            for n in range(1, 10):
                col_vals = [board[r][c] for r in range(9)]
                if n not in col_vals:
                    pos = [r for r in range(9)
                           if board[r][c] == 0
                           and SudokuEngine.is_valid(board, r, c, n)]
                    if len(pos) == 1:
                        r = pos[0]
                        return (r, c, n,
                                f"R{r+1}C{c+1}: Hidden Single in column — "
                                f"{n} can only go here in col {c+1}.")
        # ── Hidden singles in boxes ───────────────────────────
        for br in range(3):
            for bc in range(3):
                for n in range(1, 10):
                    found = False
                    pos = []
                    for r in range(br * 3, br * 3 + 3):
                        for c in range(bc * 3, bc * 3 + 3):
                            if board[r][c] == n:
                                found = True
                            elif board[r][c] == 0 and SudokuEngine.is_valid(board, r, c, n):
                                pos.append((r, c))
                    if not found and len(pos) == 1:
                        r, c = pos[0]
                        return (r, c, n,
                                f"R{r+1}C{c+1}: Hidden Single in box — "
                                f"{n} can only go here in this box.")
        # ── Fallback: first valid candidate ───────────────────
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    for n in range(1, 10):
                        if SudokuEngine.is_valid(board, r, c, n):
                            return (r, c, n,
                                    f"R{r+1}C{c+1}: {n} is valid here\n"
                                    f"(no conflict in row, column, or box).")
        return None

    @staticmethod
    def generate(difficulty="medium"):
        grid = [[0] * 9 for _ in range(9)]
        def fill(b):
            for r in range(9):
                for c in range(9):
                    if b[r][c] == 0:
                        nums = list(range(1, 10))
                        random.shuffle(nums)
                        for n in nums:
                            if SudokuEngine.is_valid(b, r, c, n):
                                b[r][c] = n
                                if fill(b):
                                    return True
                                b[r][c] = 0
                        return False
            return True
        fill(grid)
        holes = {"easy": (30, 36), "medium": (37, 46), "hard": (47, 54)}
        lo, hi = holes.get(difficulty, (37, 46))
        target = random.randint(lo, hi)
        puzzle = [row[:] for row in grid]
        positions = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(positions)
        removed = 0
        for r, c in positions:
            if removed >= target:
                break
            bak = puzzle[r][c]
            puzzle[r][c] = 0
            if SudokuEngine.count_solutions(puzzle) == 1:
                removed += 1
            else:
                puzzle[r][c] = bak
        return puzzle, grid

    @staticmethod
    def get_candidates(board, row, col):
        if board[row][col] != 0:
            return []
        return [n for n in range(1, 10) if SudokuEngine.is_valid(board, row, col, n)]


# ═══════════════════════════════════════════════════════════════════════
#  THEME DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════

DARK_COLORS = dict(
    bg="#181825", ce="#1E1E2E", co="#232336",
    gf="#CDD6F4", uf="#89B4FA", ef="#F38BA8", eb="#3B1A2A",
    nf="#7F849C", sb="#45475A", sn="#1E3A5F", sp="#1C2333",
    lt="#313244", lk="#585B70", bd="#6C7086", sv=(0, 180, 100, 35),
)

LIGHT_COLORS = dict(
    bg="#DFE6ED", ce="#FFFFFF", co="#F0F4F8",
    gf="#1A237E", uf="#1565C0", ef="#C62828", eb="#FFCDD2",
    nf="#78909C", sb="#90CAF9", sn="#BBDEFB", sp="#E3F2FD",
    lt="#B0BEC5", lk="#37474F", bd="#263238", sv=(0, 200, 80, 30),
)

DARK_BASE_SS = """
QMainWindow, QWidget { background:#181825; }
QLabel { color:#CDD6F4; }
QLabel#hintLabel { color:#A6ADC8; font-size:11pt;
    background:#1E1E2E; padding:10px; border-radius:8px; }
QLabel#keyHint { color:#585B70; font-size:9pt; }
QLabel#mistakeLabel { color:#F38BA8; font-size:10pt; font-weight:bold; }
QCheckBox { color:#CDD6F4; spacing:6px; }
QCheckBox::indicator { width:16px; height:16px; }
QComboBox { background:#313244; color:#CDD6F4; border:1px solid #45475A;
    border-radius:4px; padding:4px 8px; }
QComboBox QAbstractItemView { background:#313244; color:#CDD6F4;
    selection-background-color:#45475A; }
QComboBox::drop-down { border:none; }
QFrame[frameShape="4"] { color:#313244; }
QMenuBar { background:#181825; color:#CDD6F4; border-bottom:1px solid #313244; }
QMenuBar::item:selected { background:#313244; }
QMenu { background:#1E1E2E; color:#CDD6F4; border:1px solid #45475A; }
QMenu::item:selected { background:#313244; }
QStatusBar { background:#181825; color:#585B70; border-top:1px solid #313244; }
"""

DARK_BTN_SS = """
QPushButton#actionBtn { background:#313244; color:#CDD6F4;
    border:1px solid #45475A; border-radius:6px; font-weight:bold; }
QPushButton#actionBtn:hover { background:#45475A; }
QPushButton#actionBtn:pressed { background:#585B70; }
QPushButton#actionBtn:disabled { background:#1E1E2E; color:#45475A; }
QPushButton#toggleBtn { background:#313244; color:#CDD6F4;
    border:1px solid #45475A; border-radius:6px; padding:6px 12px; font-weight:bold; }
QPushButton#toggleBtn:hover { background:#45475A; }
QPushButton#toggleBtn:checked { background:#89B4FA; color:#1E1E2E; }
QPushButton#themeBtn { background:#313244; color:#CDD6F4;
    border:1px solid #45475A; border-radius:8px; font-size:18px; }
QPushButton#themeBtn:hover { background:#45475A; }
QPushButton#pauseBtn { background:#313244; color:#CDD6F4;
    border:1px solid #45475A; border-radius:6px; font-size:14px; }
QPushButton#pauseBtn:hover { background:#45475A; }
NumButton { background:#313244; border:1px solid #45475A; border-radius:8px; }
NumButton:hover { background:#45475A; }
NumButton:disabled { background:#1E1E2E; color:#45475A; }
QLabel { color:#CDD6F4; }
"""

LIGHT_BASE_SS = """
QMainWindow, QWidget { background:#F0F2F5; }
QLabel { color:#212121; }
QLabel#hintLabel { color:#424242; font-size:11pt;
    background:#FFFFFF; padding:10px; border-radius:8px;
    border:1px solid #E0E0E0; }
QLabel#keyHint { color:#9E9E9E; font-size:9pt; }
QLabel#mistakeLabel { color:#C62828; font-size:10pt; font-weight:bold; }
QCheckBox { color:#212121; spacing:6px; }
QCheckBox::indicator { width:16px; height:16px; }
QComboBox { background:#FFFFFF; color:#212121; border:1px solid #BDBDBD;
    border-radius:4px; padding:4px 8px; }
QComboBox QAbstractItemView { background:#FFFFFF; color:#212121;
    selection-background-color:#E3F2FD; }
QComboBox::drop-down { border:none; }
QFrame[frameShape="4"] { color:#E0E0E0; }
QMenuBar { background:#F0F2F5; color:#212121; border-bottom:1px solid #E0E0E0; }
QMenuBar::item:selected { background:#E3F2FD; }
QMenu { background:#FFFFFF; color:#212121; border:1px solid #E0E0E0; }
QMenu::item:selected { background:#E3F2FD; }
QStatusBar { background:#F0F2F5; color:#757575; border-top:1px solid #E0E0E0; }
"""

LIGHT_BTN_SS = """
QPushButton#actionBtn { background:#FFFFFF; color:#212121;
    border:1px solid #E0E0E0; border-radius:6px; font-weight:bold; }
QPushButton#actionBtn:hover { background:#E3F2FD; border-color:#90CAF9; }
QPushButton#actionBtn:pressed { background:#BBDEFB; }
QPushButton#actionBtn:disabled { background:#F5F5F5; color:#BDBDBD; }
QPushButton#toggleBtn { background:#FFFFFF; color:#212121;
    border:1px solid #E0E0E0; border-radius:6px; padding:6px 12px; font-weight:bold; }
QPushButton#toggleBtn:hover { background:#E3F2FD; }
QPushButton#toggleBtn:checked { background:#1976D2; color:#FFFFFF; }
QPushButton#themeBtn { background:#FFFFFF; color:#212121;
    border:1px solid #E0E0E0; border-radius:8px; font-size:18px; }
QPushButton#themeBtn:hover { background:#E3F2FD; }
QPushButton#pauseBtn { background:#FFFFFF; color:#212121;
    border:1px solid #E0E0E0; border-radius:6px; font-size:14px; }
QPushButton#pauseBtn:hover { background:#E3F2FD; }
NumButton { background:#FFFFFF; border:1px solid #E0E0E0; border-radius:8px; }
NumButton:hover { background:#E3F2FD; }
NumButton:disabled { background:#F5F5F5; color:#BDBDBD; }
QLabel { color:#212121; }
"""


def _colors(dark):   return dict(DARK_COLORS if dark else LIGHT_COLORS)
def _base_ss(dark):  return DARK_BASE_SS if dark else LIGHT_BASE_SS
def _btn_ss(dark):   return DARK_BTN_SS if dark else LIGHT_BTN_SS
def _hint_clr(dark): return "#4A3F00" if dark else "#FFF9C4"
def _solve_place(dark):  return ("#2E7D32", "#1B5E20") if dark else ("#66BB6A", "#C8E6C9")
def _solve_remove(dark): return ("#7F1D1D", "#4A1A1A") if dark else ("#EF9A9A", "#FFEBEE")


# ═══════════════════════════════════════════════════════════════════════
#  SUDOKU BOARD — Custom-painted 9×9 grid widget
# ═══════════════════════════════════════════════════════════════════════

class _CD:
    """Cell Data container."""
    __slots__ = ("value", "is_given", "notes", "is_error")
    def __init__(self):
        self.value = 0
        self.is_given = False
        self.notes: set = set()
        self.is_error = False


class SudokuBoard(QWidget):
    cellClicked  = Signal(int, int)
    numberInput  = Signal(int)
    eraseInput   = Signal()
    noteToggled  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cells   = [[_CD() for _ in range(9)] for _ in range(9)]
        self.selected = (-1, -1)
        self.dark      = False
        self.notes_mode = False
        self.solved    = False
        self.paused    = False
        self._anim: dict = {}
        self.setMinimumSize(380, 380)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.ClickFocus)
        self._th()

    def _th(self):
        self.C = _colors(self.dark)

    def set_dark(self, on):
        self.dark = on; self._th(); self.update()

    def set_paused(self, on):
        self.paused = on; self.update()

    # ── data helpers ──────────────────────────────────────────

    def load(self, board):
        for r in range(9):
            for c in range(9):
                cd = self.cells[r][c]
                cd.value    = board[r][c]
                cd.is_given = board[r][c] != 0
                cd.notes.clear()
                cd.is_error = False
        self.solved = False
        self._anim.clear()
        self.selected = (-1, -1)
        self.update()

    def board(self):
        return [[self.cells[r][c].value for c in range(9)] for r in range(9)]

    def set_value(self, r, c, v):
        cd = self.cells[r][c]
        if cd.is_given: return False
        cd.value = v; cd.notes.clear(); cd.is_error = False
        self.update(); return True

    def toggle_note(self, r, c, n):
        cd = self.cells[r][c]
        if cd.is_given or cd.value: return False
        cd.notes.symmetric_difference_update({n})
        self.update(); return True

    def clear_cell(self, r, c):
        cd = self.cells[r][c]
        if cd.is_given: return False
        cd.value = 0; cd.notes.clear(); cd.is_error = False
        self.update(); return True

    def cell_data(self, r, c):
        cd = self.cells[r][c]
        return cd.value, cd.is_given, frozenset(cd.notes)

    def mark_errors(self, errs):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].is_error = (r, c) in errs
        self.update()

    def clear_errors(self):
        for r in range(9):
            for c in range(9):
                self.cells[r][c].is_error = False
        self.update()

    def remove_note_from_peers(self, row, col, num):
        for i in range(9):
            self.cells[row][i].notes.discard(num)
            self.cells[i][col].notes.discard(num)
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                self.cells[r][c].notes.discard(num)

    def set_solved(self):
        self.solved = True; self.clear_errors(); self.update()

    # ── geometry helpers ──────────────────────────────────────

    def _m(self):
        mg = 2; av = min(self.width(), self.height()) - 2 * mg
        cs = av / 9; bw = cs * 9
        return cs, (self.width() - bw) / 2, (self.height() - bw) / 2, bw

    def _cr(self, r, c):
        cs, ox, oy, _ = self._m()
        return QRectF(ox + c * cs, oy + r * cs, cs, cs)

    def _hit(self, pos):
        cs, ox, oy, _ = self._m()
        c = int((pos.x() - ox) / cs); r = int((pos.y() - oy) / cs)
        return (r, c) if 0 <= r < 9 and 0 <= c < 9 else None

    # ── painting ──────────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cs, ox, oy, bw = self._m()
        C = self.C
        p.fillRect(self.rect(), QColor(C["bg"]))

        # peer / same-number highlights
        sr, sc = self.selected
        sv = self.cells[sr][sc].value if (sr, sc) != (-1, -1) else 0
        peers, snums = set(), set()
        if (sr, sc) != (-1, -1):
            for i in range(9):
                peers.add((sr, i)); peers.add((i, sc))
            br, bc = 3 * (sr // 3), 3 * (sc // 3)
            for rr in range(br, br + 3):
                for cc in range(bc, bc + 3):
                    peers.add((rr, cc))
            peers.discard((sr, sc))
            if sv:
                for rr in range(9):
                    for cc in range(9):
                        if self.cells[rr][cc].value == sv and (rr, cc) != (sr, sc):
                            snums.add((rr, cc))

        # cell backgrounds
        for r in range(9):
            for c in range(9):
                rect = self._cr(r, c); cd = self.cells[r][c]
                if (r, c) in self._anim:       bg = self._anim[(r, c)]
                elif (r, c) == (sr, sc):       bg = C["sb"]
                elif (r, c) in snums:          bg = C["sn"]
                elif (r, c) in peers:          bg = C["sp"]
                else:                          bg = C["co"] if (r//3+c//3)%2 else C["ce"]
                if cd.is_error and (r, c) not in self._anim:
                    bg = C["eb"]
                p.fillRect(rect, QColor(bg))

        # solved tint
        if self.solved:
            p.fillRect(QRectF(ox, oy, bw, bw), QColor(*C["sv"]))

        # thin grid lines
        p.setPen(QPen(QColor(C["lt"]), 1))
        for i in range(1, 9):
            if i % 3 == 0: continue
            p.drawLine(QPointF(ox, oy+i*cs), QPointF(ox+bw, oy+i*cs))
            p.drawLine(QPointF(ox+i*cs, oy), QPointF(ox+i*cs, oy+bw))

        # thick box lines
        p.setPen(QPen(QColor(C["lk"]), 2.5))
        for i in range(4):
            p.drawLine(QPointF(ox, oy+i*3*cs), QPointF(ox+bw, oy+i*3*cs))
            p.drawLine(QPointF(ox+i*3*cs, oy), QPointF(ox+i*3*cs, oy+bw))

        # border
        p.setPen(QPen(QColor(C["bd"]), 3)); p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(ox, oy, bw, bw))

        # numbers & notes
        for r in range(9):
            for c in range(9):
                cd = self.cells[r][c]; rect = self._cr(r, c)
                if cd.value:
                    if (r, c) in self._anim:  fg = QColor("#FFFFFF")
                    elif cd.is_error:         fg = QColor(C["ef"])
                    elif cd.is_given:         fg = QColor(C["gf"])
                    else:                     fg = QColor(C["uf"])
                    f = QFont("Segoe UI", max(int(cs * 0.44), 12))
                    f.setBold(cd.is_given); p.setFont(f); p.setPen(fg)
                    p.drawText(rect, Qt.AlignCenter, str(cd.value))
                elif cd.notes:
                    p.setPen(QColor(C["nf"]))
                    p.setFont(QFont("Segoe UI", max(int(cs * 0.17), 7)))
                    nw, nh = cs / 3, cs / 3
                    for n in cd.notes:
                        nr, nc = divmod(n - 1, 3)
                        p.drawText(QRectF(rect.x()+nc*nw, rect.y()+nr*nh, nw, nh),
                                   Qt.AlignCenter, str(n))

        # pause overlay
        if self.paused and not self.solved:
            p.fillRect(QRectF(ox, oy, bw, bw), QColor(0, 0, 0, 180))
            p.setPen(QColor("#FFFFFF"))
            p.setFont(QFont("Segoe UI", 24, QFont.Bold))
            p.drawText(QRectF(ox, oy, bw, bw), Qt.AlignCenter, "⏸  PAUSED")
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(QRectF(ox, oy + bw * 0.55, bw, bw * 0.2),
                       Qt.AlignCenter, "Click ▶ or press Ctrl+P to resume")
        p.end()

    # ── input ─────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if self.paused: return
        if e.button() == Qt.LeftButton:
            h = self._hit(e.position())
            if h:
                self.selected = h
                self.cellClicked.emit(*h)
                self.setFocus(); self.update()

    def keyPressEvent(self, e):
        if self.paused: e.accept(); return
        k = e.key()
        r, c = self.selected if self.selected != (-1, -1) else (0, 0)
        if Qt.Key_1 <= k <= Qt.Key_9:
            self.numberInput.emit(k - Qt.Key_0); e.accept()
        elif k in (Qt.Key_Delete, Qt.Key_Backspace, Qt.Key_0):
            self.eraseInput.emit(); e.accept()
        elif k == Qt.Key_N:
            self.noteToggled.emit(); e.accept()
        elif k == Qt.Key_Up    and r > 0:
            self.selected = (r-1, c); self.cellClicked.emit(*self.selected); self.update(); e.accept()
        elif k == Qt.Key_Down  and r < 8:
            self.selected = (r+1, c); self.cellClicked.emit(*self.selected); self.update(); e.accept()
        elif k == Qt.Key_Left  and c > 0:
            self.selected = (r, c-1); self.cellClicked.emit(*self.selected); self.update(); e.accept()
        elif k == Qt.Key_Right and c < 8:
            self.selected = (r, c+1); self.cellClicked.emit(*self.selected); self.update(); e.accept()
        else:
            super().keyPressEvent(e)

    # ── animation helpers ─────────────────────────────────────

    def anim_cell(self, r, c, color):
        self._anim[(r, c)] = color; self.update()

    def clear_anim(self):
        self._anim.clear(); self.update()


# ═══════════════════════════════════════════════════════════════════════
#  NUM BUTTON — Digit button with remaining count
# ═══════════════════════════════════════════════════════════════════════

class NumButton(QFrame):
    clicked = Signal(int)

    def __init__(self, num, parent=None):
        super().__init__(parent)
        self.num = num
        self.setFixedSize(68, 56)
        self.setCursor(Qt.PointingHandCursor)
        self._count = 9

        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 4, 2, 4); lay.setSpacing(0)

        self.num_lbl = QLabel(str(num))
        self.num_lbl.setAlignment(Qt.AlignCenter)
        self.num_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))

        self.cnt_lbl = QLabel("×9")
        self.cnt_lbl.setAlignment(Qt.AlignCenter)
        self.cnt_lbl.setFont(QFont("Segoe UI", 9))

        lay.addWidget(self.num_lbl); lay.addWidget(self.cnt_lbl)

    def set_count(self, c):
        self._count = c
        self.cnt_lbl.setText(f"×{c}")
        self.setEnabled(c > 0)

    def mousePressEvent(self, e):
        if self.isEnabled() and e.button() == Qt.LeftButton:
            self.clicked.emit(self.num)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════

class SudokuWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku")
        self.setMinimumSize(760, 540)
        self.resize(850, 620)

        self.solution    = None
        self.undo_stack  = []      # single: (r,c,v,g,notes)  batch: ("batch", [(r,c,v,g,n),…])
        self.redo_stack  = []
        self.notes_mode  = False
        self.auto_check  = True
        self.dark_mode   = False
        self.elapsed     = 0
        self.timer_on    = False
        self.paused      = False
        self.mistakes    = 0
        self.solving     = False
        self._solve_steps = []
        self._solve_idx   = 0

        self._build_ui()
        self._build_menu()
        self._apply_theme()
        self._connect()
        self._shortcuts()
        self._new_game()

    # ── Menu bar ──────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        fm = mb.addMenu("&File")
        self._act(fm, "&New Game",              "Ctrl+N",       self._new_game)
        self._act(fm, "&Save Puzzle…",          "Ctrl+S",       lambda: self.save_puzzle(False))
        self._act(fm, "Save Puzzle &with Solution…", "Ctrl+Shift+S",
                  lambda: self.save_puzzle(True))
        self._act(fm, "&Load Puzzle…",          "Ctrl+O",       self.load_puzzle)
        fm.addSeparator()
        self._act(fm, "Save &Game State…",      "",             self._save_state)
        self._act(fm, "Load Game &State…",      "",             self._load_state)
        fm.addSeparator()
        self._act(fm, "&Quit",                  "Ctrl+Q",       self.close)

        em = mb.addMenu("&Edit")
        self._act(em, "&Undo",       "Ctrl+Z",         self._undo)
        self._act(em, "&Redo",       "Ctrl+Y",         self._redo)
        self._act(em, "&Erase",      "Delete",         self._on_erase)
        em.addSeparator()
        self._act(em, "Auto &Notes", "Ctrl+Shift+N",   self._auto_notes)

        vm = mb.addMenu("&View")
        self._act(vm, "Toggle &Theme",    "Ctrl+D",  self._toggle_theme)
        self._act(vm, "&Pause / Resume",  "Ctrl+P",  self._toggle_pause)

        hm = mb.addMenu("&Help")
        self._act(hm, "&Hint",                "H",   self._hint)
        self._act(hm, "&Check",               "",    self._check)
        hm.addSeparator()
        self._act(hm, "Keyboard &Shortcuts…", "F1",  self._show_shortcuts)
        self._act(hm, "&About",               "",    self._show_about)

    def _act(self, menu, text, shortcut, callback):
        a = QAction(text, self)
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(callback)
        menu.addAction(a)

    # ── UI construction ───────────────────────────────────────

    def _build_ui(self):
        cw = QWidget(); self.setCentralWidget(cw)
        root = QHBoxLayout(cw)
        root.setContentsMargins(14, 14, 14, 14); root.setSpacing(18)

        # ── board ─────────────────────────────────────────────
        self.board = SudokuBoard()
        root.addWidget(self.board, 1)

        # ── side panel ────────────────────────────────────────
        panel = QWidget(); panel.setFixedWidth(270)
        pl = QVBoxLayout(panel); pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(8)

        # timer row
        tr = QHBoxLayout()
        tr.addWidget(self._ilbl("⏱"))
        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setFont(QFont("Consolas", 18, QFont.Bold))
        tr.addWidget(self.timer_lbl); tr.addStretch()

        self.mistake_lbl = QLabel("")
        self.mistake_lbl.setObjectName("mistakeLabel")
        tr.addWidget(self.mistake_lbl)

        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setFixedSize(36, 36); self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setToolTip("Pause / Resume  (Ctrl+P)")
        tr.addWidget(self.pause_btn)

        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(36, 36); self.theme_btn.setObjectName("themeBtn")
        self.theme_btn.setToolTip("Toggle theme  (Ctrl+D)")
        tr.addWidget(self.theme_btn)
        pl.addLayout(tr)

        # toggles
        tg = QHBoxLayout()
        self.notes_btn = QPushButton("✏ Notes")
        self.notes_btn.setCheckable(True); self.notes_btn.setObjectName("toggleBtn")
        self.auto_cb = QCheckBox("Auto-check"); self.auto_cb.setChecked(True)
        tg.addWidget(self.notes_btn); tg.addWidget(self.auto_cb)
        pl.addLayout(tg)

        # numpad
        ng = QGridLayout(); ng.setSpacing(5)
        self.num_btns = []
        for i in range(9):
            b = NumButton(i + 1); self.num_btns.append(b)
            ng.addWidget(b, i // 3, i % 3)
        self.erase_btn = QPushButton("⌫  Erase")
        self.erase_btn.setFixedHeight(42); self.erase_btn.setObjectName("actionBtn")
        ng.addWidget(self.erase_btn, 3, 0, 1, 3)
        pl.addLayout(ng)

        # action buttons
        ag = QGridLayout(); ag.setSpacing(5)
        self.undo_btn      = QPushButton("↩ Undo")
        self.redo_btn      = QPushButton("↪ Redo")
        self.hint_btn      = QPushButton("💡 Hint")
        self.check_btn     = QPushButton("✓ Check")
        self.solve_btn     = QPushButton("▶ Solve")
        self.new_btn       = QPushButton("🔄 New")
        self.auto_notes_btn= QPushButton("📝 Auto-Notes")
        for b in (self.undo_btn, self.redo_btn, self.hint_btn,
                  self.check_btn, self.solve_btn, self.new_btn,
                  self.auto_notes_btn):
            b.setFixedHeight(36); b.setObjectName("actionBtn")
        ag.addWidget(self.undo_btn, 0, 0); ag.addWidget(self.redo_btn, 0, 1)
        ag.addWidget(self.hint_btn, 1, 0); ag.addWidget(self.check_btn, 1, 1)
        ag.addWidget(self.solve_btn, 2, 0);ag.addWidget(self.new_btn, 2, 1)
        ag.addWidget(self.auto_notes_btn, 3, 0, 1, 2)
        pl.addLayout(ag)

        # difficulty
        dr = QHBoxLayout()
        dr.addWidget(QLabel("Difficulty:"))
        self.diff_cb = QComboBox()
        self.diff_cb.addItems(["Easy", "Medium", "Hard"])
        self.diff_cb.setCurrentIndex(1); self.diff_cb.setFixedWidth(100)
        dr.addWidget(self.diff_cb); dr.addStretch()
        pl.addLayout(dr)

        # separator
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        pl.addWidget(sep)

        # hint label
        self.hint_lbl = QLabel("Select a cell and enter a number,\nor press Hint for help.")
        self.hint_lbl.setWordWrap(True); self.hint_lbl.setMinimumHeight(70)
        self.hint_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.hint_lbl.setObjectName("hintLabel")
        pl.addWidget(self.hint_lbl)

        # keyboard hint
        kb = QLabel("Keys: 1-9 · Del · N (notes) · Arrows · Ctrl+Z/Y")
        kb.setObjectName("keyHint"); pl.addWidget(kb)

        pl.addStretch()
        root.addWidget(panel)

        self.statusBar().showMessage("Ready")

        # animation timer
        self._solve_timer = QTimer(self)
        self._solve_timer.timeout.connect(self._anim_step)

    @staticmethod
    def _ilbl(t):
        l = QLabel(t); l.setFont(QFont("Segoe UI", 16)); return l

    # ── Theme ─────────────────────────────────────────────────

    def _apply_theme(self):
        self.board.set_dark(self.dark_mode)
        self.setStyleSheet(_base_ss(self.dark_mode))
        bs = _btn_ss(self.dark_mode)
        for b in (self.notes_btn, self.erase_btn, self.undo_btn, self.redo_btn,
                  self.hint_btn, self.check_btn, self.solve_btn, self.new_btn,
                  self.theme_btn, self.pause_btn, self.auto_notes_btn):
            b.setStyleSheet(bs)
        for nb in self.num_btns:
            nb.setStyleSheet(bs)

    def _toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
        self._apply_theme()

    # ── Connections ───────────────────────────────────────────

    def _connect(self):
        b = self.board
        b.cellClicked.connect(self._on_cell)
        b.numberInput.connect(self._on_num)
        b.eraseInput.connect(self._on_erase)
        b.noteToggled.connect(self._toggle_notes)

        for i, nb in enumerate(self.num_btns):
            nb.clicked.connect(lambda n=i+1: self._on_num(n))
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
        self.pause_btn.clicked.connect(self._toggle_pause)
        self.diff_cb.currentTextChanged.connect(lambda _: self._new_game())
        self.auto_notes_btn.clicked.connect(self._auto_notes)

    def _shortcuts(self):
        for key, fn in [
            (QKeySequence("Ctrl+Z"), self._undo),
            (QKeySequence("Ctrl+Y"), self._redo),
            (QKeySequence("Ctrl+N"), self._new_game),
            (QKeySequence("H"),      self._hint),
            (QKeySequence("Ctrl+D"), self._toggle_theme),
            (QKeySequence("Ctrl+P"), self._toggle_pause),
        ]:
            s = QShortcut(key, self); s.activated.connect(fn)

    # ── Timer ─────────────────────────────────────────────────

    def _ensure_tick(self):
        if not hasattr(self, "_tick"):
            self._tick = QTimer(self)
            self._tick.timeout.connect(self._tick_timer)

    def _start_timer(self, reset=True):
        if reset: self.elapsed = 0
        self.timer_on = True; self._update_timer()
        self._ensure_tick(); self._tick.start(1000)

    def _tick_timer(self):
        if self.timer_on and not self.paused:
            self.elapsed += 1; self._update_timer()

    def _update_timer(self):
        m, s = divmod(self.elapsed, 60)
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

    def _stop_timer(self):
        self.timer_on = False

    # ── Pause ─────────────────────────────────────────────────

    def _toggle_pause(self):
        if self.solving or self.board.solved: return
        self.paused = not self.paused
        self.board.set_paused(self.paused)
        self.pause_btn.setText("▶" if self.paused else "⏸")
        self.hint_lbl.setText(
            "Game paused.\nClick ▶ or Ctrl+P to resume." if self.paused
            else "Resumed. Good luck!")

    # ── Game logic ────────────────────────────────────────────

    def _new_game(self):
        self._stop_solving()
        self.paused = False; self.board.set_paused(False)
        self.pause_btn.setText("⏸")
        diff = self.diff_cb.currentText().lower()
        puzzle, solution = SudokuEngine.generate(diff)
        self.solution = solution
        self.board.load(puzzle)
        self.undo_stack.clear(); self.redo_stack.clear()
        self.notes_mode = False; self.notes_btn.setChecked(False)
        self.board.notes_mode = False
        self.mistakes = 0; self._update_mistakes()
        self.hint_lbl.setText("New puzzle generated.\nGood luck!")
        self._update_counts(); self._start_timer()
        self.statusBar().showMessage(f"New {diff} puzzle started")

    def _on_cell(self, r, c):
        if self.solving or self.paused: return
        cd = self.board.cells[r][c]
        if cd.is_given:
            txt = f"R{r+1}C{c+1}: Given clue ({cd.value})"
        elif cd.value:
            txt = f"R{r+1}C{c+1}: You placed {cd.value}"
        elif cd.notes:
            txt = f"R{r+1}C{c+1}: Notes: {', '.join(map(str, sorted(cd.notes)))}"
        else:
            cands = SudokuEngine.get_candidates(self.board.board(), r, c)
            if cands:
                txt = f"R{r+1}C{c+1}: Empty — candidates: {', '.join(map(str, sorted(cands)))}"
            else:
                txt = f"R{r+1}C{c+1}: Empty — no valid candidates"
        self.hint_lbl.setText(txt)

    def _on_num(self, n):
        if self.solving or self.paused: return
        r, c = self.board.selected
        if (r, c) == (-1, -1): return
        if self.notes_mode:
            old = self.board.cell_data(r, c)
            if self.board.toggle_note(r, c, n):
                self.undo_stack.append((r, c, old))
                self.redo_stack.clear()
        else:
            old = self.board.cell_data(r, c)
            if self.board.set_value(r, c, n):
                self.undo_stack.append((r, c, old))
                self.redo_stack.clear()
                self.board.remove_note_from_peers(r, c, n)
                # Track mistakes against the solution
                if self.solution and self.solution[r][c] != n:
                    self.mistakes += 1
                    self._update_mistakes()
                if self.auto_check:
                    self._auto_validate(r, c, n)
                self._check_win()
        self._update_counts()

    def _on_erase(self):
        if self.solving or self.paused: return
        r, c = self.board.selected
        if (r, c) == (-1, -1): return
        old = self.board.cell_data(r, c)
        if self.board.clear_cell(r, c):
            self.undo_stack.append((r, c, old))
            self.redo_stack.clear()
            if self.auto_check: self._do_check()
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
        if self.solving or self.paused: return
        n = self._do_check()
        b = self.board.board()
        empty = sum(1 for r in range(9) for c in range(9) if b[r][c] == 0)
        if n == 0:
            if empty:
                self.hint_lbl.setText(f"✓ No conflicts found!\n{empty} cells remaining.")
            else:
                self.hint_lbl.setText("✓ Perfect! Puzzle solved correctly!")
        else:
            self.hint_lbl.setText(f"✗ Found {n} conflicting cell(s).\nHighlighted in red.")

    def _hint(self):
        if self.solving or self.paused: return
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
        self.board.anim_cell(r, c, QColor(_hint_clr(self.dark_mode)))
        QTimer.singleShot(2000, self.board.clear_anim)

    # ── Undo / Redo (with batch support for Auto-Notes) ──────

    def _undo(self):
        if self.solving or self.paused or not self.undo_stack: return
        item = self.undo_stack.pop()
        redo_item = None
        if item[0] == "batch":
            _, changes = item
            redo_changes = []
            for ch in reversed(changes):
                r, c, prev = ch
                cur = self.board.cell_data(r, c)
                cd = self.board.cells[r][c]
                cd.value, cd.is_given, cd.notes, cd.is_error = prev[0], prev[1], set(prev[2]), False
                redo_changes.append((r, c, cur))
            redo_item = ("batch", redo_changes)
        else:
            r, c, prev = item
            cur = self.board.cell_data(r, c)
            cd = self.board.cells[r][c]
            cd.value, cd.is_given, cd.notes, cd.is_error = prev[0], prev[1], set(prev[2]), False
            redo_item = (r, c, cur)
        self.redo_stack.append(redo_item)
        self.board.update()
        if self.auto_check: self._do_check()
        self._update_counts()

    def _redo(self):
        if self.solving or self.paused or not self.redo_stack: return
        item = self.redo_stack.pop()
        undo_item = None
        if item[0] == "batch":
            _, changes = item
            undo_changes = []
            for ch in reversed(changes):
                r, c, prev = ch
                cur = self.board.cell_data(r, c)
                cd = self.board.cells[r][c]
                cd.value, cd.is_given, cd.notes, cd.is_error = prev[0], prev[1], set(prev[2]), False
                undo_changes.append((r, c, cur))
            undo_item = ("batch", undo_changes)
        else:
            r, c, prev = item
            cur = self.board.cell_data(r, c)
            cd = self.board.cells[r][c]
            cd.value, cd.is_given, cd.notes, cd.is_error = prev[0], prev[1], set(prev[2]), False
            undo_item = (r, c, cur)
        self.undo_stack.append(undo_item)
        self.board.update()
        if self.auto_check: self._do_check()
        self._update_counts()

    # ── Auto Notes ────────────────────────────────────────────

    def _auto_notes(self):
        if self.solving or self.paused: return
        b = self.board.board()
        changes = []
        for r in range(9):
            for c in range(9):
                cd = self.board.cells[r][c]
                if cd.value == 0:
                    old = self.board.cell_data(r, c)
                    new_notes = SudokuEngine.get_candidates(b, r, c)
                    if set(new_notes) != cd.notes:
                        cd.notes = set(new_notes)
                        changes.append((r, c, old))
        if changes:
            self.undo_stack.append(("batch", changes))
            self.redo_stack.clear()
            self.board.update()
            self.hint_lbl.setText(f"📝 Auto-notes filled for {len(changes)} cells.")

    # ── Win Check ─────────────────────────────────────────────

    def _check_win(self):
        b = self.board.board()
        for r in range(9):
            for c in range(9):
                if b[r][c] == 0: return
        for r in range(9):
            for c in range(9):
                if not SudokuEngine.is_valid(b, r, c, b[r][c]): return
        self._stop_timer()
        self.board.set_solved()
        m, s = divmod(self.elapsed, 60)
        self.hint_lbl.setText(
            f"🎉 Congratulations!\n\nPuzzle solved in {m:02d}:{s:02d}\n"
            f"Difficulty: {self.diff_cb.currentText()}\nMistakes: {self.mistakes}"
        )
        self.statusBar().showMessage("Puzzle completed!")

    # ── Numpad Counts & Mistakes ──────────────────────────────

    def _update_counts(self):
        b = self.board.board()
        for n in range(1, 10):
            cnt = sum(1 for r in range(9) for c in range(9) if b[r][c] == n)
            self.num_btns[n - 1].set_count(9 - cnt)

    def _update_mistakes(self):
        self.mistake_lbl.setText(f"✗ {self.mistakes}" if self.mistakes else "")

    # ── Animated Solver ───────────────────────────────────────

    def _start_solve(self):
        if self.solving or self.paused: return
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
            flash, fade = _solve_place(self.dark_mode)
            self.board.anim_cell(r, c, QColor(flash))
            QTimer.singleShot(30, lambda rr=r, cc=c, f=fade: self.board.anim_cell(rr, cc, QColor(f)))
        else:
            self.board.cells[r][c].value = 0
            flash, fade = _solve_remove(self.dark_mode)
            self.board.anim_cell(r, c, QColor(flash))
            QTimer.singleShot(30, lambda rr=r, cc=c, f=fade: self.board.anim_cell(rr, cc, QColor(f)))
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

    # ── Save / Load (Puzzle & Full State) ─────────────────────

    def save_puzzle(self, with_solution=False):
        b = self.board.board()
        if with_solution:
            test = [row[:] for row in b]
            if not SudokuEngine.solve(test):
                QMessageBox.warning(self, "Error", "Cannot solve this puzzle.")
                return
            b = test
        path, _ = QFileDialog.getSaveFileName(self, "Save Puzzle", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w") as f:
                    for row in b: f.write(",".join(map(str, row)) + "\n")
                self.statusBar().showMessage("Puzzle saved to file")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save:\n{e}")

    def load_puzzle(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Puzzle", "", "Text Files (*.txt)")
        if not path: return
        try:
            with open(path) as f: lines = [l.strip() for l in f if l.strip()]
            board = []
            for line in lines:
                row = [int(x) if x.strip().isdigit() else 0 for x in line.split(",")]
                board.append(row)
            if len(board) != 9 or any(len(r) != 9 for r in board): raise ValueError
            self._stop_solving()
            self.solution = None
            self.board.load(board)
            self.undo_stack.clear(); self.redo_stack.clear()
            self.mistakes = 0; self._update_mistakes()
            self._update_counts(); self._start_timer()
            self.hint_lbl.setText("Puzzle loaded from file.")
            self.statusBar().showMessage("Loaded puzzle from file")
        except Exception:
            QMessageBox.warning(self, "Error", "Invalid puzzle file (need 9×9 comma-separated).")

    def _save_state(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Game State", "", "JSON Files (*.json)")
        if not path: return
        state = {
            "board": self.board.board(),
            "given": [[self.board.cells[r][c].is_given for c in range(9)] for r in range(9)],
            "notes": [[list(self.board.cells[r][c].notes) for c in range(9)] for r in range(9)],
            "solution": self.solution,
            "elapsed": self.elapsed,
            "mistakes": self.mistakes,
            "dark_mode": self.dark_mode,
            "difficulty": self.diff_cb.currentText(),
        }
        try:
            with open(path, "w") as f: json.dump(state, f, indent=2)
            self.statusBar().showMessage("Game state saved")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save game state:\n{e}")

    def _load_state(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Game State", "", "JSON Files (*.json)")
        if not path: return
        try:
            with open(path) as f: state = json.load(f)
            board = state["board"]
            given = state["given"]
            notes = state["notes"]
            self._stop_solving()
            self.solution = state.get("solution")
            self.elapsed = state.get("elapsed", 0)
            self.mistakes = state.get("mistakes", 0)
            self._update_mistakes()
            self.diff_cb.setCurrentText(state.get("difficulty", "Medium"))
            # Apply loaded state to board
            for r in range(9):
                for c in range(9):
                    cd = self.board.cells[r][c]
                    cd.value = board[r][c]
                    cd.is_given = given[r][c]
                    cd.notes = set(notes[r][c])
                    cd.is_error = False
            self.board.solved = False; self.board._anim.clear()
            self.board.selected = (-1, -1)
            self.board.update()
            self.undo_stack.clear(); self.redo_stack.clear()
            self._update_counts(); self._start_timer(reset=False)
            if state.get("dark_mode") != self.dark_mode: self._toggle_theme()
            self.hint_lbl.setText("Game state restored.")
            self.statusBar().showMessage("Loaded game state")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load game state:\n{e}")

    # ── Dialogs ───────────────────────────────────────────────

    def _show_shortcuts(self):
        d = QDialog(self)
        d.setWindowTitle("Keyboard Shortcuts")
        d.setMinimumSize(380, 420)
        lay = QVBoxLayout(d)
        te = QTextEdit(); te.setReadOnly(True)
        te.setHtml("""
        <h3>Game Controls</h3>
        <table width='100%'>
        <tr><td><b>1-9</b></td><td>Enter number / toggle note</td></tr>
        <tr><td><b>Delete / Backspace</b></td><td>Erase cell</td></tr>
        <tr><td><b>N</b></td><td>Toggle Notes mode</td></tr>
        <tr><td><b>Arrow keys</b></td><td>Navigate board</td></tr>
        <tr><td><b>H</b></td><td>Get hint</td></tr>
        </table>
        <h3>General Shortcuts</h3>
        <table width='100%'>
        <tr><td><b>Ctrl+N</b></td><td>New Game</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>Save Puzzle</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>Load Puzzle</td></tr>
        <tr><td><b>Ctrl+Z</b></td><td>Undo</td></tr>
        <tr><td><b>Ctrl+Y</b></td><td>Redo</td></tr>
        <tr><td><b>Ctrl+D</b></td><td>Toggle Dark/Light Theme</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>Pause / Resume</td></tr>
        <tr><td><b>Ctrl+Shift+N</b></td><td>Auto-fill Notes</td></tr>
        </table>
        """)
        lay.addWidget(te)
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(d.accept); lay.addWidget(bb)
        d.exec()

    def _show_about(self):
        QMessageBox.about(self, "About Sudoku",
            "<h3>Premium Sudoku</h3>"
            "<p>Built with PySide6.</p>"
            "<p>Features generator, solver, hints, "
            "dark/light themes, and save/load functionality.</p>")

    # ── Close ─────────────────────────────────────────────────

    def closeEvent(self, e):
        self._stop_solving()
        self._stop_timer()
        super().closeEvent(e)


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SudokuWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()