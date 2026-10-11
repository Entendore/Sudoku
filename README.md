# Sudoku Application

A single-file Sudoku desktop application built with Python and PySide6. It offers a polished UI, logical hint system, animated solver, and full keyboard/mouse support.

## Requirements

*   Python 3.x
*   PySide6

## Installation & Running

1. Install the required package:
   ```bash
   pip install PySide6
   ```
2. Run the application:
   ```bash
   python app.py
   ```

## Features

*   **Difficulty Levels:** Easy, Medium, and Hard (controlled by the number of given clues).
*   **Themes:** Dark and Light modes with polished visuals and cell highlighting (peers, same numbers, errors).
*   **Notes (Pencil Marks):** Toggle notes mode to place candidate numbers in empty cells.
*   **Auto-Notes:** Automatically fills all empty cells with valid candidates (Ctrl+Shift+N).
*   **Conflict Checking:** Auto-highlights conflicting numbers in real-time, plus a manual Check button.
*   **Mistake Counter:** Tracks incorrect entries against the generated solution.
*   **Hints:** Logical hint system that explains *why* a number goes in a cell (Naked Singles, Hidden Singles in row/col/box).
*   **Undo / Redo:** Full history support, including batch undo for the Auto-Notes feature.
*   **Animated Solver:** Watch the backtracking algorithm solve the puzzle step-by-step.
*   **Pause / Resume:** Hides the board under an overlay so you can step away without cheating.
*   **Save / Load:** 
    *   Save/Load puzzle boards as simple `.txt` files.
    *   Save/Load full game state (including notes, timer, mistakes, and solution) as `.json`.
*   **Numpad:** Clickable number buttons that display the remaining count for each digit.

## Controls & Shortcuts

### Mouse
*   **Left Click:** Select cell / Click numpad to enter number.
*   **Buttons:** Use the side panel for Notes, Erase, Undo, Redo, Hint, Check, Solve, Auto-Notes, and New Game.

### Keyboard
| Action | Shortcut |
| :--- | :--- |
| **Input Number** | `1` - `9` |
| **Erase Cell** | `Delete` / `Backspace` / `0` |
| **Toggle Notes Mode** | `N` |
| **Navigate Cells** | `Arrow Keys` |
| **New Game** | `Ctrl + N` |
| **Undo** | `Ctrl + Z` |
| **Redo** | `Ctrl + Y` |
| **Hint** | `H` |
| **Auto-Notes** | `Ctrl + Shift + N` |
| **Check Conflicts** | (Menu: Edit > Check) |
| **Toggle Theme** | `Ctrl + D` |
| **Pause / Resume** | `Ctrl + P` |
| **Save Puzzle (.txt)** | `Ctrl + S` |
| **Save Puzzle + Solution (.txt)**| `Ctrl + Shift + S` |
| **Load Puzzle (.txt)** | `Ctrl + O` |
| **Save Game State (.json)** | (Menu: File > Save Game State) |
| **Load Game State (.json)** | (Menu: File > Load Game State) |
| **Quit** | `Ctrl + Q` |

## File Formats

*   **Puzzle (.txt):** A 9-line text file where each line contains 9 comma-separated integers (0 for empty cells).
*   **Game State (.json):** A JSON file preserving the board state, given cells, notes, the solution, elapsed time, mistake count, theme, and difficulty.