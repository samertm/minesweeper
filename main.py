import sys
import re
from enum import Enum
from random import random

NUM_BOMBS = 15
BOARD_LEN = 10

class GameState(Enum):
    ALIVE = 1
    DEAD = 2
    WON = 3

class Cell:
    def __init__(self, is_bomb=False, num_surrounding_bombs=0, revealed=False):
        self.is_bomb = is_bomb
        self.num_surrounding_bombs = num_surrounding_bombs
        self.revealed = revealed
        self.flag = False

    def __repr__(self):
        return "Cell(is_bomb={is_bomb}, num_surrounding_bombs={num_surrounding_bombs}, revealed={revealed})".format(
            is_bomb=self.is_bomb,
            num_surrounding_bombs=self.num_surrounding_bombs,
            revealed=self.revealed,
        )

    def __str__(self):
        if not self.revealed:
            if self.flag:
                return "F"
            return "X"
        if self.is_bomb:
            return "b"
        if self.num_surrounding_bombs > 0:
            return str(self.num_surrounding_bombs)
        return " "

def create_grid(num_bombs, board_len):
    bombs = set()
    for _ in range(num_bombs):
        while True:
            x, y = int(random() * board_len), int(random() * board_len)
            if (x, y) in bombs:
                continue
            bombs.add((x, y))
            break

    # Initialize grid
    grid = []
    for i in range(board_len):
        row = []
        for j in range(board_len):
            row.append(None)
        grid.append(row)

    # Add bombs
    for x, y in bombs:
        grid[x][y] = Cell(is_bomb=True)

    # Add surrounding cells
    for x in range(board_len):
        for y in range(board_len):
            if grid[x][y] is not None:
                continue

            num_bombs = 0
            neighbor_deltas = [-1, 0, 1]
            for x_delta in neighbor_deltas:
                for y_delta in neighbor_deltas:
                    if x_delta == 0 and y_delta == 0:
                        continue

                    x_neigh = x + x_delta
                    y_neigh = y + y_delta

                    if x_neigh < 0 or x_neigh >= board_len or\
                       y_neigh < 0 or y_neigh >= board_len:
                        continue

                    if grid[x_neigh][y_neigh] is not None and grid[x_neigh][y_neigh].is_bomb:
                        num_bombs += 1

            grid[x][y] = Cell(is_bomb=False, num_surrounding_bombs=num_bombs)

    return grid

def fill_space(to_print, space):
    assert len(to_print) < space

    fill = space - len(to_print)

    return " " * fill

def print_grid(grid):

    cell_space = len(str(len(grid))) + 1

    left_padding = " " * (cell_space + 1)

    # Print top axis
    print(left_padding, end="")
    for i in range(len(grid)):
        x_coord = str(i+1)
        print(x_coord, end=fill_space(x_coord, cell_space))
    print()

    # Add "_"'s
    print(left_padding, end="")
    print("_" * (len(grid) * cell_space))

    for y in range(len(grid)):
        y_coord = str(y+1)
        print(y_coord, end=fill_space(y_coord, cell_space))
        print("|", end="")
        for x in range(len(grid)):
            cell = grid[x][y]
            print(cell, end=fill_space(str(cell), cell_space))
        print()

class Move:
    def __init__(self, x, y, flag=False):
        self.x = x
        self.y = y
        self.flag = flag

def get_user_move():
    move = input("What's your move?\nUse the format '<x>, <y>' to uncover a spot, or 'f <x>, <y>' to place a flag: ")
    is_flag = False
    m = re.match(" *(\d+) *, *(\d+)", move)
    if not m:
        is_flag = True
        m = re.match(" *f *(\d+) *, *(\d+)", move)
        if not m:
            return None

    user_x_str = m.group(1)
    user_y_str = m.group(2)
    try:
        # subtract 1 to make the coordinates 0-based
        user_x = int(user_x_str) - 1
        user_y = int(user_y_str) - 1
    except ValueError:
        return None

    return Move(user_x, user_y, flag=is_flag)

def move_is_valid(move, grid):
    user_x, user_y = move.x, move.y
    board_len = len(grid)
    if (user_x < 0 or user_x >= board_len or
        user_y < 0 or user_y >= board_len):
        return False

    return True

def reveal_neighbors(grid, user_x, user_y):
    board_len = len(grid)
    neighbor_deltas = [-1, 0, 1]

    to_recurse = []
    for x_delta in neighbor_deltas:
        for y_delta in neighbor_deltas:
            if x_delta == 0 and y_delta == 0:
                continue

            x = user_x + x_delta
            y = user_y + y_delta
            if (x < 0 or x >= board_len or
                y < 0 or y >= board_len):
                continue

            neighbor = grid[x][y]
            assert not neighbor.is_bomb
            if neighbor.revealed:
                continue

            neighbor.revealed = True
            if neighbor.num_surrounding_bombs == 0:
                to_recurse.append((x, y))

    for recurse_x, recurse_y in to_recurse:
        reveal_neighbors(grid, recurse_x, recurse_y)

def process_move(grid, move):
    """Returns True if the user is still alive, False otherwise."""
    user_x, user_y = move.x, move.y

    cell = grid[user_x][user_y]

    if move.flag:
        cell.flag = not cell.flag
        return GameState.ALIVE

    cell.revealed = True
    if cell.is_bomb:
        return GameState.DEAD

    if cell.num_surrounding_bombs == 0:
        reveal_neighbors(grid, user_x, user_y)

    # Calculate win
    winner = True
    for row in grid:
        if winner == False:
            break

        for cell in row:
            if not cell.revealed and not cell.is_bomb:
                winner = False
                break

    return GameState.WON if winner else GameState.ALIVE


def main():
    grid = create_grid(NUM_BOMBS, BOARD_LEN)

    print_grid(grid)
    print()

    while True:
        move = get_user_move()
        if not move or not move_is_valid(move, grid):
            print("Invalid move, try again.")
            continue

        if not move.flag and grid[move.x][move.y].revealed:
            print("Coordinate is already revealed, try again.")
            continue

        result = process_move(grid, move)

        print()
        print_grid(grid)
        print()

        if result == GameState.DEAD:
            print("You exploded!")
            # Reveal entire board
            for row in grid:
                for cell in row:
                    cell.revealed = True
            print()
            print_grid(grid)
            return
        if result == GameState.WON:
            print("YOU WON! CONGRATS!")
            return


if __name__ == "__main__":
    main()
