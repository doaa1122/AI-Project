"""
board.py
--------
This file contains the Board class which holds all game state:
- Player positions
- Wall positions
- Wall counts
- Turn logic
- Move validation
- Win detection

The board is 9x9 cells.
Walls are placed on the EDGES between cells.
We store walls as a set of blocked edges.
"""

from pathfinding import both_players_have_path


class Board:
    def __init__(self):
        """Set up a fresh game."""
        self.reset()

    def reset(self):
        """Reset the board to the initial game state."""
        self.size = 9  # 9x9 board

        # Player 1 starts at bottom-center, needs to reach row 0
        self.player1 = {'row': 8, 'col': 4, 'walls': 10}

        # Player 2 starts at top-center, needs to reach row 8
        self.player2 = {'row': 0, 'col': 4, 'walls': 10}

        # Walls are stored as frozensets of two adjacent cell pairs.
        # A horizontal wall between (r,c)-(r,c+1) and (r+1,c)-(r+1,c+1)
        # blocks movement between row r and row r+1 for columns c and c+1.
        #
        # We store blocked EDGES (not walls themselves).
        # Each blocked edge is a tuple: ((r1,c1), (r2,c2))
        # where (r1,c1) and (r2,c2) are the two cells separated by the wall segment.
        self.blocked_edges = set()

        # Store placed walls for drawing (each wall = list of two edge segments)
        # A wall is stored as: (row, col, direction)
        # direction = 'H' means horizontal wall (blocks vertical movement)
        # direction = 'V' means vertical wall (blocks horizontal movement)
        self.placed_walls = []  # list of (row, col, direction)

        # Turn: 1 = Player 1's turn, 2 = Player 2's turn
        self.current_turn = 1

        # Winner: None until someone wins
        self.winner = None

        # Mode of interaction: 'move' or 'wall'
        self.mode = 'move'

        # Wall orientation for placement: 'H' or 'V'
        self.wall_orientation = 'H'

    # -------------------------------------------------------------------------
    # Helper: get the current player's data dict
    # -------------------------------------------------------------------------
    def current_player(self):
        return self.player1 if self.current_turn == 1 else self.player2

    def other_player(self):
        return self.player2 if self.current_turn == 1 else self.player1

    # -------------------------------------------------------------------------
    # Neighbor logic (used by BFS and move validation)
    # -------------------------------------------------------------------------
    def get_neighbors(self, row, col):
        """
        Return all cells reachable from (row, col) considering walls.
        Does NOT consider opponent pawns — used for pathfinding only.
        """
        neighbors = []
        # Up, Down, Left, Right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                # Check if the edge between (row,col) and (nr,nc) is blocked
                edge = (min((row, col), (nr, nc)), max((row, col), (nr, nc)))
                if edge not in self.blocked_edges:
                    neighbors.append((nr, nc))
        return neighbors

    # -------------------------------------------------------------------------
    # Pawn movement
    # -------------------------------------------------------------------------
    def get_valid_pawn_moves(self):
        """
        Return a list of (row, col) cells the current player can move to.
        Handles normal moves, jumping over opponent, and diagonal jumps.
        """
        player = self.current_player()
        opponent = self.other_player()
        pr, pc = player['row'], player['col']
        or_, oc = opponent['row'], opponent['col']

        valid = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dr, dc in directions:
            nr, nc = pr + dr, pc + dc

            # Must be within board
            if not (0 <= nr < self.size and 0 <= nc < self.size):
                continue

            # Check if edge is blocked by a wall
            edge = (min((pr, pc), (nr, nc)), max((pr, pc), (nr, nc)))
            if edge in self.blocked_edges:
                continue

            # If this cell has the opponent pawn
            if nr == or_ and nc == oc:
                # Try to jump over the opponent
                jr, jc = nr + dr, nc + dc
                if 0 <= jr < self.size and 0 <= jc < self.size:
                    jump_edge = (min((nr, nc), (jr, jc)), max((nr, nc), (jr, jc)))
                    if jump_edge not in self.blocked_edges:
                        # Straight jump is possible
                        valid.append((jr, jc))
                        continue

                # Straight jump is blocked — try diagonal moves
                # Try the two perpendicular directions
                perp_dirs = [(0, 1), (0, -1)] if dr != 0 else [(-1, 0), (1, 0)]
                for pdr, pdc in perp_dirs:
                    diag_r, diag_c = nr + pdr, nc + pdc
                    if 0 <= diag_r < self.size and 0 <= diag_c < self.size:
                        diag_edge = (min((nr, nc), (diag_r, diag_c)), max((nr, nc), (diag_r, diag_c)))
                        if diag_edge not in self.blocked_edges:
                            valid.append((diag_r, diag_c))
            else:
                # Normal empty cell
                valid.append((nr, nc))

        return valid

    def move_pawn(self, row, col):
        """Move the current player's pawn to (row, col). Returns True if successful."""
        if self.winner:
            return False

        valid_moves = self.get_valid_pawn_moves()
        if (row, col) not in valid_moves:
            return False

        player = self.current_player()
        player['row'] = row
        player['col'] = col

        # Check for win
        if self.current_turn == 1 and row == 0:
            self.winner = 1
        elif self.current_turn == 2 and row == 8:
            self.winner = 2
        else:
            self.switch_turn()

        return True

    # -------------------------------------------------------------------------
    # Wall placement
    # -------------------------------------------------------------------------
    def can_place_wall(self, row, col, direction):
        """
        Check if a wall can be placed at (row, col) with given direction.

        For a HORIZONTAL wall at (row, col):
          - Blocks movement between row 'row' and row 'row+1'
          - Covers columns col and col+1
          - So it blocks edges: ((row,col),(row+1,col)) and ((row,col+1),(row+1,col+1))

        For a VERTICAL wall at (row, col):
          - Blocks movement between col 'col' and col 'col+1'
          - Covers rows row and row+1
          - So it blocks edges: ((row,col),(row,col+1)) and ((row+1,col),(row+1,col+1))

        Wall anchor (row, col) must be in range [0..7] x [0..7] so the wall fits.
        """
        player = self.current_player()

        # Must have walls left
        if player['walls'] <= 0:
            return False

        # Wall anchor must be in valid range (0-7 for both row and col)
        if not (0 <= row <= 7 and 0 <= col <= 7):
            return False

        # Compute the two edges this wall would block
        new_edges = self._wall_edges(row, col, direction)

        # Check no overlap with existing blocked edges
        for edge in new_edges:
            if edge in self.blocked_edges:
                return False

        # Check no crossing walls
        # A horizontal wall crosses a vertical wall if they share the middle point
        if direction == 'H':
            cross_edges = self._wall_edges(row, col, 'V')
        else:
            cross_edges = self._wall_edges(row, col, 'H')

        # Two walls cross if they share BOTH edges at the crossing point
        # Simpler check: a H wall at (r,c) crosses V wall at (r,c) if the center overlaps
        # We detect crossing by checking if the perpendicular wall's edges are both blocked
        if all(e in self.blocked_edges for e in cross_edges):
            return False

        # Temporarily place the wall and check that both players still have a path
        for edge in new_edges:
            self.blocked_edges.add(edge)

        paths_ok = both_players_have_path(self)

        # Remove temporary wall
        for edge in new_edges:
            self.blocked_edges.remove(edge)

        return paths_ok

    def place_wall(self, row, col, direction):
        """Place a wall at (row, col) with given direction. Returns True if successful."""
        if self.winner:
            return False

        if not self.can_place_wall(row, col, direction):
            return False

        # Add the blocked edges
        new_edges = self._wall_edges(row, col, direction)
        for edge in new_edges:
            self.blocked_edges.add(edge)

        # Record the wall for drawing
        self.placed_walls.append((row, col, direction))

        # Deduct a wall from the current player
        self.current_player()['walls'] -= 1

        self.switch_turn()
        return True

    def _wall_edges(self, row, col, direction):
        """
        Return the two edges blocked by a wall at (row, col) with given direction.
        Each edge is a tuple of two sorted cell coordinates.
        """
        if direction == 'H':
            # Horizontal wall: blocks between row and row+1 at columns col and col+1
            e1 = (min((row, col), (row + 1, col)), max((row, col), (row + 1, col)))
            e2 = (min((row, col + 1), (row + 1, col + 1)), max((row, col + 1), (row + 1, col + 1)))
        else:
            # Vertical wall: blocks between col and col+1 at rows row and row+1
            e1 = (min((row, col), (row, col + 1)), max((row, col), (row, col + 1)))
            e2 = (min((row + 1, col), (row + 1, col + 1)), max((row + 1, col), (row + 1, col + 1)))
        return [e1, e2]

    # -------------------------------------------------------------------------
    # Turn management
    # -------------------------------------------------------------------------
    def switch_turn(self):
        """Switch the active player."""
        self.current_turn = 2 if self.current_turn == 1 else 1

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def is_edge_blocked(self, r1, c1, r2, c2):
        """Check if the edge between two adjacent cells is blocked."""
        edge = (min((r1, c1), (r2, c2)), max((r1, c1), (r2, c2)))
        return edge in self.blocked_edges
