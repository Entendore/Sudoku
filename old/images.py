import random
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def generate_sudoku_grid():
    """Generates a full valid Sudoku grid using backtracking."""
    grid = [[0]*9 for _ in range(9)]

    def is_valid(num, row, col):
        for i in range(9):
            if grid[row][i] == num or grid[i][col] == num:
                return False
        start_row, start_col = 3*(row//3), 3*(col//3)
        for i in range(3):
            for j in range(3):
                if grid[start_row+i][start_col+j] == num:
                    return False
        return True

    def solve():
        for i in range(9):
            for j in range(9):
                if grid[i][j] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for num in nums:
                        if is_valid(num, i, j):
                            grid[i][j] = num
                            if solve():
                                return True
                            grid[i][j] = 0
                    return False
        return True

    solve()
    return grid

def remove_numbers(grid, holes=40):
    """Remove numbers from the filled Sudoku to make a puzzle."""
    puzzle = [row[:] for row in grid]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)
    for i in range(holes):
        r, c = positions[i]
        puzzle[r][c] = 0
    return puzzle

def random_color():
    """Generate a random hex color."""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def sudoku_to_svg(grid, cell_size=50):
    """Convert a Sudoku grid to SVG with gradient-colored numbers."""
    svg_size = cell_size * 9
    svg = Element('svg', xmlns="http://www.w3.org/2000/svg",
                  width=str(svg_size), height=str(svg_size))

    # Colors for alternating 3x3 blocks
    block_colors = ["#f8f8f8", "#e0f7fa"]

    # Draw 3x3 block backgrounds
    for block_row in range(3):
        for block_col in range(3):
            color = block_colors[(block_row + block_col) % 2]
            SubElement(svg, 'rect',
                       x=str(block_col*3*cell_size),
                       y=str(block_row*3*cell_size),
                       width=str(3*cell_size),
                       height=str(3*cell_size),
                       fill=color)

    # Draw grid lines
    for i in range(10):
        thickness = '3' if i % 3 == 0 else '1'
        SubElement(svg, 'line', x1=str(i*cell_size), y1='0',
                   x2=str(i*cell_size), y2=str(svg_size),
                   stroke='black', **{'stroke-width': thickness})
        SubElement(svg, 'line', x1='0', y1=str(i*cell_size),
                   x2=str(svg_size), y2=str(i*cell_size),
                   stroke='black', **{'stroke-width': thickness})

    # Draw numbers with random gradients
    defs = SubElement(svg, 'defs')
    for r in range(9):
        for c in range(9):
            num = grid[r][c]
            if num != 0:
                grad_id = f"grad_{r}_{c}"
                grad = SubElement(defs, 'linearGradient', id=grad_id, x1="0%", y1="0%", x2="100%", y2="100%")
                SubElement(grad, 'stop', offset="0%", style=f"stop-color:{random_color()};stop-opacity:1")
                SubElement(grad, 'stop', offset="100%", style=f"stop-color:{random_color()};stop-opacity:1")
                
                text = SubElement(svg, 'text',
                                 x=str(c*cell_size + cell_size/2),
                                 y=str(r*cell_size + cell_size*0.65),
                                 fill=f"url(#{grad_id})",
                                 **{'font-size': str(cell_size*0.6),
                                    'font-family': 'Georgia, serif',
                                    'font-weight': 'bold',
                                    'text-anchor': 'middle'})
                text.text = str(num)

    xml_str = minidom.parseString(tostring(svg)).toprettyxml(indent="  ")
    return xml_str

if __name__ == "__main__":
    full_grid = generate_sudoku_grid()
    puzzle = remove_numbers(full_grid, holes=40)
    svg_output = sudoku_to_svg(puzzle)

    with open("gradient_sudoku.svg", "w") as f:
        f.write(svg_output)

    print("Gradient Sudoku puzzle SVG saved as 'gradient_sudoku.svg'")
