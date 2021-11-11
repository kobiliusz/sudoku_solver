import numpy as np
import tkinter as tk

NUMS = {1, 2, 3, 4, 5, 6, 7, 8, 9}

board = None
given = None

def reset_state():
    global board, given
    board = np.empty([9, 9])
    given = np.full_like(board, False)

def field_check(text):
    return not text or (text.isdigit() and 1 <= int(text) <= 9)

tk_root = tk.Tk()
tk_root.title("Sudoku Solver")
check_cmd = (tk_root.register(field_check), '%P')
reset_state()
fields = [[tk.Entry(tk_root, width=1, validate='all', validatecommand=check_cmd)
           for x in range(9)] for y in range(9)]

for x in range(9):
    for y in range(9):
        fields[x][y].grid(row=y, column=x)

def reset_fields():
    global fields
    for x in range(9):
        for y in range(9):
            fields[x][y].delete(0,tk.END)
    reset_state()

reset_button = tk.Button(tk_root, text="Reset", command=reset_fields)
reset_button.grid(row=9, column=0, columnspan=4, pady=5)

def solve():
    pass

solve_button = tk.Button(tk_root, text="Solve", command=solve)
solve_button.grid(row=9, column=5, columnspan=4, pady=5)

tk_root.mainloop()