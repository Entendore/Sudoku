import sys
import random
import copy
import numpy as np
import imageio
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTextEdit, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QIntValidator, QFont, QColor, QPalette, QPainter
from PyQt6.QtCore import Qt, QTimer

# ---------------- Sudoku Solver ----------------
class SudokuSolver:
    def __init__(self, board):
        self.board = board
        self.steps = []

    def is_valid(self, row, col, num):
        for i in range(9):
            if self.board[row][i]==num or self.board[i][col]==num:
                return False
        start_row, start_col=3*(row//3), 3*(col//3)
        for i in range(3):
            for j in range(3):
                if self.board[start_row+i][start_col+j]==num:
                    return False
        return True

    def solve_with_steps(self):
        for row in range(9):
            for col in range(9):
                if self.board[row][col]==0:
                    for num in range(1,10):
                        if self.is_valid(row,col,num):
                            self.board[row][col]=num
                            self.steps.append((row,col,num))
                            if self.solve_with_steps():
                                return True
                            self.board[row][col]=0
                            self.steps.append((row,col,0))
                    return False
        return True

    def count_solutions(self, limit=2):
        return self._count_recursive(limit)

    def _count_recursive(self, limit, board=None):
        if board is None:
            board=self.board
        for row in range(9):
            for col in range(9):
                if board[row][col]==0:
                    count=0
                    for num in range(1,10):
                        if self.is_valid(row,col,num):
                            board[row][col]=num
                            count+=self._count_recursive(limit,board)
                            if count>=limit:
                                board[row][col]=0
                                return count
                            board[row][col]=0
                    return count
        return 1

    def get_hint(self, board):
        for row in range(9):
            for col in range(9):
                if board[row][col]==0:
                    for num in range(1,10):
                        if self.is_valid(row,col,num):
                            explanation = (
                                f"Placing {num} at ({row+1},{col+1}) is valid because:\n"
                                f"- Row {row+1} has no {num}\n"
                                f"- Column {col+1} has no {num}\n"
                                f"- 3x3 box starting at ({3*(row//3)+1},{3*(col//3)+1}) has no {num}"
                            )
                            return row,col,num,explanation
        return None

# ---------------- GUI ----------------
class SudokuGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Solver")
        self.setMinimumSize(900,600)
        self.grid_cells=[[None for _ in range(9)] for _ in range(9)]
        self.solver=None
        self.solve_timer=QTimer()
        self.step_index=0
        self.undo_stack=[]
        self.redo_stack=[]
        self.solve_delay=50
        self.recording=False
        self.record_frames=[]
        self.record_hint_text=""
        self.record_format="gif"
        self.init_ui()
        self.solve_timer.timeout.connect(self.animate_step)

    # ---------------- GUI Layout ----------------
    def init_ui(self):
        main_layout=QHBoxLayout()
        grid_frame=QFrame()
        grid_layout=QGridLayout()
        grid_frame.setLayout(grid_layout)
        font=QFont("Arial",20,QFont.Weight.Bold)

        # 9x9 Grid
        for i in range(9):
            for j in range(9):
                cell=QLineEdit()
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFont(font)
                cell.setFixedSize(60,60)
                cell.setValidator(QIntValidator(1,9))
                cell.old_text=""
                cell.textChanged.connect(lambda text,r=i,c=j,cell=cell:self.cell_changed(r,c,cell,text))
                top=2 if i%3==0 else 1
                left=2 if j%3==0 else 1
                bottom=2 if i==8 else 1
                right=2 if j==8 else 1
                cell.setStyleSheet(f"border-top:{top}px solid black;"
                                   f"border-left:{left}px solid black;"
                                   f"border-bottom:{bottom}px solid black;"
                                   f"border-right:{right}px solid black;"
                                   "background-color:#FFFFFF;")
                self.grid_cells[i][j]=cell
                grid_layout.addWidget(cell,i,j)
        main_layout.addWidget(grid_frame,3)

        # Sidebar
        sidebar_layout=QVBoxLayout()
        diff_layout=QHBoxLayout()
        diff_label=QLabel("Difficulty:")
        diff_label.setFont(QFont("Arial",12,QFont.Weight.Bold))
        self.diff_combo=QComboBox()
        self.diff_combo.addItems(["Easy","Medium","Hard"])
        diff_layout.addWidget(diff_label)
        diff_layout.addWidget(self.diff_combo)
        sidebar_layout.addLayout(diff_layout)

        # Buttons
        buttons=[
            ("Random Puzzle", self.random_puzzle),
            ("Solve", lambda: self.start_animation(record=False)),
            ("Hint", lambda: self.give_hint(True)),
            ("Undo", self.undo),
            ("Redo", self.redo),
            ("Clear", self.clear_grid),
            ("Load Puzzle", self.load_puzzle),
            ("Save Puzzle", lambda: self.save_puzzle(False)),
            ("Save Solution", lambda: self.save_puzzle(True)),
            ("Record GIF", lambda: self.start_animation(record=True, format="gif")),
            ("Record MP4", lambda: self.start_animation(record=True, format="mp4"))
        ]
        for name, func in buttons:
            btn=QPushButton(name)
            btn.setFixedHeight(40)
            btn.setStyleSheet("background-color:#5DADE2;color:white;font-weight:bold;")
            btn.clicked.connect(func)
            sidebar_layout.addWidget(btn)

        # Hint Display
        self.hint_display=QTextEdit()
        self.hint_display.setReadOnly(True)
        self.hint_display.setFixedWidth(250)
        self.hint_display.setStyleSheet("background-color:#F0F0F0;font-size:12pt;")
        sidebar_layout.addWidget(self.hint_display)
        sidebar_layout.addStretch()
        main_layout.addLayout(sidebar_layout,1)
        self.setLayout(main_layout)

    # ---------------- Board Functions ----------------
    def get_board(self):
        return [[int(self.grid_cells[i][j].text()) if self.grid_cells[i][j].text().isdigit() else 0 for j in range(9)] for i in range(9)]
    def set_board(self,board):
        for i in range(9):
            for j in range(9):
                self.grid_cells[i][j].setText(str(board[i][j]) if board[i][j]!=0 else "")

    # ---------------- Cell Tracking ----------------
    def cell_changed(self,row,col,cell,new_text):
        old_value=int(cell.old_text) if cell.old_text.isdigit() else 0
        new_value=int(new_text) if new_text.isdigit() else 0
        if old_value!=new_value:
            self.undo_stack.append((row,col,old_value))
            self.redo_stack.clear()
        cell.old_text=new_text
        self.highlight_invalid()
    def undo(self):
        if not self.undo_stack: return
        row,col,value=self.undo_stack.pop()
        cell=self.grid_cells[row][col]
        current_value=int(cell.text()) if cell.text().isdigit() else 0
        self.redo_stack.append((row,col,current_value))
        cell.setText(str(value) if value!=0 else "")
    def redo(self):
        if not self.redo_stack: return
        row,col,value=self.redo_stack.pop()
        cell=self.grid_cells[row][col]
        current_value=int(cell.text()) if cell.text().isdigit() else 0
        self.undo_stack.append((row,col,current_value))
        cell.setText(str(value) if value!=0 else "")

    # ---------------- Highlight Invalid ----------------
    def highlight_invalid(self):
        board=self.get_board()
        for i in range(9):
            for j in range(9):
                cell=self.grid_cells[i][j]
                palette=cell.palette()
                text=cell.text()
                if text.isdigit() and int(text)!=0:
                    solver=SudokuSolver(board)
                    if not solver.is_valid(i,j,int(text)):
                        palette.setColor(QPalette.ColorRole.Base,QColor("#FFAAAA"))
                    else:
                        palette.setColor(QPalette.ColorRole.Base,QColor("#FFFFFF"))
                else:
                    palette.setColor(QPalette.ColorRole.Base,QColor("#FFFFFF"))
                cell.setPalette(palette)

    # ---------------- Solver Animation ----------------
    def start_animation(self, record=False, format="gif"):
        self.recording=record
        self.record_frames=[]
        self.record_format=format
        board=self.get_board()
        self.solver=SudokuSolver(copy.deepcopy(board))
        if self.solver.solve_with_steps():
            self.step_index=0
            self.solve_timer.start(self.solve_delay)
        else:
            QMessageBox.warning(self,"No Solution","This puzzle has no solution.")

    def animate_step(self):
        if self.step_index<len(self.solver.steps):
            row,col,value=self.solver.steps[self.step_index]
            self.grid_cells[row][col].setText(str(value) if value!=0 else "")
            palette=self.grid_cells[row][col].palette()
            palette.setColor(QPalette.ColorRole.Base,QColor("#DDFFDD") if value!=0 else QColor("#FFDDDD"))
            self.grid_cells[row][col].setPalette(palette)
            self.record_hint_text=self.hint_display.toPlainText()
            if self.recording:
                frame=self.capture_frame_with_hint(self.record_hint_text)
                self.record_frames.append(frame)
            self.step_index+=1
        else:
            for i in range(9):
                for j in range(9):
                    palette=self.grid_cells[i][j].palette()
                    palette.setColor(QPalette.ColorRole.Base,QColor("#FFFFFF"))
                    self.grid_cells[i][j].setPalette(palette)
            self.solve_timer.stop()
            if self.recording:
                if self.record_format=="gif":
                    self.save_gif("sudoku_solution.gif")
                else:
                    self.save_mp4("sudoku_solution.mp4")
                self.recording=False

    def capture_frame_with_hint(self,hint_text=""):
        pixmap=self.grab()
        painter=QPainter(pixmap)
        painter.setPen(QColor("blue"))
        painter.setFont(QFont("Arial",12))
        painter.drawText(10,pixmap.height()-20,hint_text)
        painter.end()
        img=pixmap.toImage()
        ptr=img.constBits()
        ptr.setsize(img.byteCount())
        arr=np.array(ptr).reshape(img.height(),img.width(),4)
        return arr

    def save_gif(self,filename):
        if not self.record_frames: return
        imageio.mimsave(filename,self.record_frames,duration=0.3)
        QMessageBox.information(self,"Saved GIF",f"Animation with hints saved as {filename}")

    def save_mp4(self,filename="sudoku_solution.mp4", fps=5):
        if not self.record_frames: return
        height,width,_=self.record_frames[0].shape
        out=cv2.VideoWriter(filename,cv2.VideoWriter_fourcc(*'mp4v'),fps,(width,height))
        for frame in self.record_frames:
            frame_bgr=cv2.cvtColor(frame,cv2.COLOR_RGBA2BGR)
            out.write(frame_bgr)
        out.release()
        QMessageBox.information(self,"Saved MP4",f"Animation saved as {filename}")

    # ---------------- Hints ----------------
    def give_hint(self,animate=True):
        board=self.get_board()
        solver=SudokuSolver(copy.deepcopy(board))
        hint=solver.get_hint(board)
        if hint is None:
            QMessageBox.information(self,"No Hint","No empty cells or valid hint.")
            return
        row,col,num,explanation=hint
        self.hint_display.setText(explanation)
        if animate:
            self.grid_cells[row][col].setText("")
            QTimer.singleShot(500,lambda r=row,c=col,n=num:self.grid_cells[r][c].setText(str(n)))
        else:
            self.grid_cells[row][col].setText(str(num))

    # ---------------- File Handling ----------------
    def load_puzzle(self):
        file_name,_=QFileDialog.getOpenFileName(self,"Open Puzzle","","Text Files (*.txt);;CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name,"r") as f:
                    board=[]
                    for line in f:
                        row=[int(n) if n.isdigit() else 0 for n in line.strip().split(",")]
                        board.append(row)
                    if len(board)==9 and all(len(r)==9 for r in board):
                        self.set_board(board)
                    else:
                        QMessageBox.warning(self,"Error","Invalid puzzle format (must be 9x9).")
            except Exception as e:
                QMessageBox.warning(self,"Error",str(e))
    def save_puzzle(self,solution=False):
        board=self.get_board()
        if solution:
            solver=SudokuSolver(copy.deepcopy(board))
            if not solver.solve_with_steps():
                QMessageBox.warning(self,"No Solution","Cannot save solution.")
                return
            board=solver.board
        file_name,_=QFileDialog.getSaveFileName(self,"Save Puzzle","","Text Files (*.txt);;CSV Files (*.csv)")
        if file_name:
            try:
                with open(file_name,"w") as f:
                    for row in board:
                        f.write(",".join(str(num) for num in row)+"\n")
                QMessageBox.information(self,"Saved","Puzzle saved successfully!")
            except Exception as e:
                QMessageBox.warning(self,"Error",str(e))

    # ---------------- Clear / Random Puzzle ----------------
    def clear_grid(self):
        self.set_board([[0]*9 for _ in range(9)])
    def random_puzzle(self):
        while True:
            board=[[0]*9 for _ in range(9)]
            solver=SudokuSolver(board)
            solver.solve_with_steps()
            puzzle=copy.deepcopy(solver.board)
            difficulty=self.diff_combo.currentText()
            if difficulty=="Easy":
                cells_to_remove=random.randint(30,35)
            elif difficulty=="Medium":
                cells_to_remove=random.randint(40,45)
            else:
                cells_to_remove=random.randint(50,55)
            removed=0
            while removed<cells_to_remove:
                i,j=random.randint(0,8),random.randint(0,8)
                if puzzle[i][j]!=0:
                    temp=puzzle[i][j]
                    puzzle[i][j]=0
                    temp_solver=SudokuSolver(copy.deepcopy(puzzle))
                    if temp_solver.count_solutions()==1:
                        removed+=1
                    else:
                        puzzle[i][j]=temp
            self.set_board(puzzle)
            break

# ---------------- Run App ----------------
if __name__=="__main__":
    app=QApplication(sys.argv)
    window=SudokuGUI()
    window.show()
    sys.exit(app.exec())
