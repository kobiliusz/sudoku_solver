from dataclasses import dataclass
import numpy as np
import tkinter as tk
import tkinter.messagebox as mb
import threading as thr
from abc import *


class BoardError(BaseException):
    pass


def no_nones(list):
    return {i for i in list if i}


def each_field(what):
    for x in range(9):
        for y in range(9):
            what(x=x, y=y)


def p_of_block(x, y):
    return 3*int(y/3)+int(x/3)


def field_color(x, y):
    if p_of_block(x, y) % 2 == 1:
        return 'white'
    else:
        return '#dddddd'


board = None


def reset_state():
    global board
    board = np.zeros([9, 9], dtype=int)


def field_check(text):
    return not text or (text.isdigit() and 1 <= int(text) <= 9)


tk_root = tk.Tk()
tk_root.title("Sudoku Solver")
solve_button = None
reset_button = None
solve_t = None
kill_solve = True
had_error = False
success = False
check_cmd = (tk_root.register(field_check), '%P')
reset_state()
fields = [[tk.Entry(tk_root, width=1, validate='all', validatecommand=check_cmd, bg=field_color(x,y))
           for x in range(9)] for y in range(9)]

each_field(lambda x, y: fields[x][y].grid(row=y, column=x))


def reset_fields():
    global fields, kill_solve
    kill_solve = True
    each_field(lambda x, y: fields[x][y].configure(state='normal', bg=field_color(x,y)))
    each_field(lambda x, y: fields[x][y].delete(0, tk.END))
    solve_button.configure(state='normal')
    reset_state()


reset_button = tk.Button(tk_root, text="Reset", command=reset_fields)
reset_button.grid(row=9, column=0, columnspan=4, pady=5)

NUMS = {1, 2, 3, 4, 5, 6, 7, 8, 9}


@dataclass
class FillCandidate:
    x: int
    y: int
    no: int


class Part(metaclass=ABCMeta):

    def missing(self):
        return NUMS.difference(no_nones(self.vals))

    def empties(self):
        return [i for i in range(9) if self.vals[i] == 0]

    @abstractmethod
    def get_x(self, index):
        pass

    @abstractmethod
    def get_y(self, index):
        pass


class Row(Part):

    def __init__(self, row_y):
        self.row_y = row_y
        self.vals = []
        for x in range(9):
            if board[x][row_y] != 0 and board[x][row_y] in self.vals:
                raise BoardError()
            else:
                self.vals.append(board[x][row_y])

    def get_x(self, index):
        return index

    def get_y(self, index):
        return self.row_y


class Column(Part):

    def __init__(self, col_x):
        self.col_x = col_x
        self.vals = []
        for y in range(9):
            if board[col_x][y] != 0 and board[col_x][y] in self.vals:
                raise BoardError()
            else:
                self.vals.append(board[col_x][y])

    def get_x(self, index):
        return self.col_x

    def get_y(self, index):
        return index


#   0 1 2
#   3 4 5
#   6 7 8

def x_from_p(p):
    return p % 3


def y_from_p(p):
    return int(p / 3)


class Block(Part):

    def __init__(self, block_p):
        self.block_p = block_p
        self.block_x = x_from_p(block_p) * 3
        self.block_y = y_from_p(block_p) * 3
        self.vals = []
        for p in range(9):
            if (board[self.block_x + x_from_p(p)][self.block_y + y_from_p(p)] != 0
                    and board[self.block_x + x_from_p(p)][self.block_y + y_from_p(p)] in self.vals):
                raise BoardError()
            else:
                self.vals.append(board[self.block_x + x_from_p(p)][self.block_y + y_from_p(p)])

    def get_x(self, index):
        return self.block_x + x_from_p(index)

    def get_y(self, index):
        return self.block_y + y_from_p(index)


def copy_field(x, y):
    global fields, board
    if fields[x][y].get():
        board[x][y] = int(fields[x][y].get())
        fields[x][y].configure(bg='#00aa00')
    fields[x][y].configure(state='disabled')


def fill_field(x, y, no):
    global fields
    fields[x][y].configure(state='normal')
    fields[x][y].insert(0, str(no))
    fields[x][y].configure(state='disabled')


def solve():
    global kill_solve, had_error, success, board
    kill_solve = False
    try:
        solve_button.configure(state='disabled')
        each_field(lambda x, y: copy_field(x, y))
        found = True
        while True:
            if kill_solve:
                return
            if not found:
                board[best_fill.x][best_fill.y] = best_fill.no
                fields[best_fill.x][best_fill.y].configure(bg='#aaaa00')
                fill_field(best_fill.x, best_fill.y, best_fill.no)
            best_len = 10
            best_fill: FillCandidate = None
            found = False
            rows = [Row(i) for i in range(9)]
            cols = [Column(i) for i in range(9)]
            blocks = [Block(i) for i in range(9)]
            parts = [*rows, *cols, *blocks]
            parts.sort(key=lambda part: len(part.missing()))
            if len(parts[len(parts)-1].missing()) == 0:
                success = True
                return
            for part in parts:
                if kill_solve:
                    return
                for missingno in part.missing():
                    if kill_solve:
                        return
                    fits = []
                    for ind in part.empties():
                        if kill_solve:
                            return
                        empty_x = part.get_x(ind)
                        empty_y = part.get_y(ind)
                        empty_p = p_of_block(empty_x, empty_y)
                        if (missingno in rows[empty_y].missing() and missingno in cols[empty_x].missing() and missingno
                                in blocks[empty_p].missing()):
                            fits.append(ind)
                    if len(fits) == 0:
                        raise BoardError()
                    elif len(fits) == 1:
                        n = fits[0]
                        board[part.get_x(n)][part.get_y(n)] = missingno
                        fill_field(part.get_x(n), part.get_y(n), missingno)
                        found = True
                        break
                    elif len(fits) < best_len:
                        best_len = len(fits)
                        n = fits[0]
                        best_fill = FillCandidate(x=part.get_x(n), y=part.get_y(n), no=missingno)
                if found:
                    break

    except BoardError:
        had_error = True
        reset_fields()


def solve_thread():
    global solve_t, had_error, success
    solve_t = thr.Thread(target=solve)
    solve_t.start()
    while solve_t.is_alive():
        tk_root.update()
    if had_error:
        had_error = False
        mb.showerror(title='Board Error', message='Unable to solve puzzle.')
    elif success:
        each_field(lambda x, y: fields[x][y].configure(state='normal'))
        mb.showinfo(title='Success!', message='Puzzle solved.')


solve_button = tk.Button(tk_root, text="Solve", command=solve_thread)
solve_button.grid(row=9, column=5, columnspan=4, pady=5)

tk_root.resizable(False, False)
tk_root.mainloop()
