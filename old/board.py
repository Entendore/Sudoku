"""
SudokuBoard — Custom-painted 9×9 grid widget
"""

from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, Signal, QRectF, QPointF

from Sudoku.old.themes import get_colors


class _CD:
    """Cell Data container."""
    __slots__ = ("value", "is_given", "notes", "is_error")

    def __init__(self):
        self.value = 0
        self.is_given = False
        self.notes: set = set()
        self.is_error = False


class SudokuBoard(QWidget):
    cellClicked = Signal(int, int)
    numberInput = Signal(int)
    eraseInput = Signal()
    noteToggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cells = [[_CD() for _ in range(9)] for _ in range(9)]
        self.selected = (-1, -1)
        self.dark = False
        self.notes_mode = False
        self.solved = False
        self._anim: dict = {}
        self.setMinimumSize(380, 380)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setFocusPolicy(Qt.ClickFocus)
        self._colors()

    def _colors(self):
        self.C = get_colors(self.dark)

    def set_dark(self, on):
        self.dark = on
        self._colors()
        self.update()

    def load(self, board):
        for r in range(9):
            for c in range(9):
                cd = self.cells[r][c]
                cd.value = board[r][c]
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
        if cd.is_given:
            return False
        cd.value = v
        cd.notes.clear()
        cd.is_error = False
        self.update()
        return True

    def toggle_note(self, r, c, n):
        cd = self.cells[r][c]
        if cd.is_given or cd.value:
            return False
        cd.notes.symmetric_difference_update({n})
        self.update()
        return True

    def clear_cell(self, r, c):
        cd = self.cells[r][c]
        if cd.is_given:
            return False
        cd.value = 0
        cd.notes.clear()
        cd.is_error = False
        self.update()
        return True

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
        self.solved = True
        self.clear_errors()
        self.update()

    def _m(self):
        mg = 2
        av = min(self.width(), self.height()) - 2 * mg
        cs = av / 9
        bw = cs * 9
        ox = (self.width() - bw) / 2
        oy = (self.height() - bw) / 2
        return cs, ox, oy, bw

    def _cr(self, r, c):
        cs, ox, oy, _ = self._m()
        return QRectF(ox + c * cs, oy + r * cs, cs, cs)

    def _hit(self, pos):
        cs, ox, oy, _ = self._m()
        c = int((pos.x() - ox) / cs)
        r = int((pos.y() - oy) / cs)
        if 0 <= r < 9 and 0 <= c < 9:
            return r, c
        return None

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cs, ox, oy, bw = self._m()
        C = self.C

        p.fillRect(self.rect(), C["bg"])

        sr, sc = self.selected
        sv = self.cells[sr][sc].value if (sr, sc) != (-1, -1) else 0
        peers, snums = set(), set()
        if (sr, sc) != (-1, -1):
            for i in range(9):
                peers.add((sr, i))
                peers.add((i, sc))
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

        for r in range(9):
            for c in range(9):
                rect = self._cr(r, c)
                cd = self.cells[r][c]
                if (r, c) in self._anim:
                    bg = self._anim[(r, c)]
                elif (r, c) == (sr, sc):
                    bg = C["sb"]
                elif (r, c) in snums:
                    bg = C["sn"]
                elif (r, c) in peers:
                    bg = C["sp"]
                else:
                    bg = C["co"] if (r // 3 + c // 3) % 2 else C["ce"]
                if cd.is_error and (r, c) not in self._anim:
                    bg = C["eb"]
                p.fillRect(rect, QColor(bg))

        if self.solved:
            p.fillRect(QRectF(ox, oy, bw, bw), QColor(*C["sv"]))

        p.setPen(QPen(QColor(C["lt"]), 1))
        for i in range(1, 9):
            if i % 3 == 0:
                continue
            p.drawLine(QPointF(ox, oy + i * cs), QPointF(ox + bw, oy + i * cs))
            p.drawLine(QPointF(ox + i * cs, oy), QPointF(ox + i * cs, oy + bw))

        p.setPen(QPen(QColor(C["lk"]), 2.5))
        for i in range(4):
            p.drawLine(QPointF(ox, oy + i * 3 * cs), QPointF(ox + bw, oy + i * 3 * cs))
            p.drawLine(QPointF(ox + i * 3 * cs, oy), QPointF(ox + i * 3 * cs, oy + bw))

        p.setPen(QPen(QColor(C["bd"]), 3))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRectF(ox, oy, bw, bw))

        for r in range(9):
            for c in range(9):
                cd = self.cells[r][c]
                rect = self._cr(r, c)
                if cd.value:
                    if (r, c) in self._anim:
                        fg = QColor("#FFFFFF")
                    elif cd.is_error:
                        fg = QColor(C["ef"])
                    elif cd.is_given:
                        fg = QColor(C["gf"])
                    else:
                        fg = QColor(C["uf"])
                    f = QFont("Segoe UI", max(int(cs * 0.44), 12))
                    f.setBold(cd.is_given)
                    p.setFont(f)
                    p.setPen(fg)
                    p.drawText(rect, Qt.AlignCenter, str(cd.value))
                elif cd.notes:
                    p.setPen(QColor(C["nf"]))
                    p.setFont(QFont("Segoe UI", max(int(cs * 0.17), 7)))
                    nw, nh = cs / 3, cs / 3
                    for n in cd.notes:
                        nr, nc = divmod(n - 1, 3)
                        p.drawText(QRectF(rect.x() + nc * nw, rect.y() + nr * nh, nw, nh),
                                   Qt.AlignCenter, str(n))
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            h = self._hit(e.position())
            if h:
                self.selected = h
                self.cellClicked.emit(*h)
                self.setFocus()
                self.update()

    def keyPressEvent(self, e):
        k = e.key()
        r, c = self.selected if self.selected != (-1, -1) else (0, 0)
        if Qt.Key_1 <= k <= Qt.Key_9:
            self.numberInput.emit(k - Qt.Key_0)
            e.accept()
        elif k in (Qt.Key_Delete, Qt.Key_Backspace, Qt.Key_0):
            self.eraseInput.emit()
            e.accept()
        elif k == Qt.Key_N:
            self.noteToggled.emit()
            e.accept()
        elif k == Qt.Key_Up and r > 0:
            self.selected = (r - 1, c)
            self.cellClicked.emit(*self.selected)
            self.update()
            e.accept()
        elif k == Qt.Key_Down and r < 8:
            self.selected = (r + 1, c)
            self.cellClicked.emit(*self.selected)
            self.update()
            e.accept()
        elif k == Qt.Key_Left and c > 0:
            self.selected = (r, c - 1)
            self.cellClicked.emit(*self.selected)
            self.update()
            e.accept()
        elif k == Qt.Key_Right and c < 8:
            self.selected = (r, c + 1)
            self.cellClicked.emit(*self.selected)
            self.update()
            e.accept()
        else:
            super().keyPressEvent(e)

    def anim_cell(self, r, c, color):
        self._anim[(r, c)] = color
        self.update()

    def clear_anim(self):
        self._anim.clear()
        self.update()