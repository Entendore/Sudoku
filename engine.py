"""
Sudoku Engine — Pure logic: generation, solving, validation
No UI dependencies
"""

import random


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
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    cands = [n for n in range(1, 10) if SudokuEngine.is_valid(board, r, c, n)]
                    if len(cands) == 1:
                        n = cands[0]
                        return (r, c, n,
                                f"R{r + 1}C{c + 1}: Naked Single — only {n} fits.\n"
                                f"Row, column & box block all other digits.")
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    for n in range(1, 10):
                        if SudokuEngine.is_valid(board, r, c, n):
                            return (r, c, n,
                                    f"R{r + 1}C{c + 1}: {n} is valid here\n"
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