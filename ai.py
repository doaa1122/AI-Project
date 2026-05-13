"""
ai.py
-----
Contains the AI logic for the computer opponent.

Easy AI:
    - Just picks a random valid move (pawn move or wall placement).

Medium AI:
    - Tries to move toward the goal first.
    - Occasionally places a wall to slow down the human player.
    - Falls back to random if nothing smart is available.
"""

import random
from pathfinding import bfs_has_path


def get_easy_move(board):
    """
    Easy AI: randomly choose between moving the pawn or placing a wall.
    If it has walls, there's a 30% chance it tries to place one randomly.
    Otherwise just move the pawn.
    """
    player = board.current_player()

    # Decide whether to try placing a wall
    if player['walls'] > 0 and random.random() < 0.3:
        wall_move = _random_wall(board)
        if wall_move:
            return ('wall', wall_move)

    # Move pawn randomly
    pawn_moves = board.get_valid_pawn_moves()
    if pawn_moves:
        chosen = random.choice(pawn_moves)
        return ('pawn', chosen)

    return None


def get_medium_move(board):
    """
    Medium AI:
    1. Check if there's a pawn move that gets closer to the goal.
    2. If the human is very close to winning, try to place a blocking wall.
    3. Otherwise move toward goal, or random if nothing better.
    """
    player = board.current_player()
    opponent = board.other_player()

    # Figure out goals
    # AI is always player 2 (needs to reach row 8)
    ai_goal_row = 8
    human_goal_row = 0

    # --- Try to block the human if they're close ---
    human_row = opponent['row']
    # If the human is within 2 rows of their goal, try placing a wall
    if player['walls'] > 0 and human_row <= 2:
        wall_move = _find_blocking_wall(board, opponent)
        if wall_move:
            return ('wall', wall_move)

    # --- Move toward goal ---
    pawn_moves = board.get_valid_pawn_moves()
    if pawn_moves:
        # Score each move: lower distance to goal is better
        best_move = None
        best_dist = abs(player['row'] - ai_goal_row) + 1  # current distance

        for (r, c) in pawn_moves:
            dist = abs(r - ai_goal_row)
            if dist < best_dist:
                best_dist = dist
                best_move = (r, c)

        if best_move:
            return ('pawn', best_move)

        # No move gets us closer — just pick a random pawn move
        return ('pawn', random.choice(pawn_moves))

    return None


# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _random_wall(board):
    """Try random wall placements until one is valid or give up after 30 tries."""
    for _ in range(30):
        row = random.randint(0, 7)
        col = random.randint(0, 7)
        direction = random.choice(['H', 'V'])
        if board.can_place_wall(row, col, direction):
            return (row, col, direction)
    return None


def _find_blocking_wall(board, opponent):
    """
    Try to find a wall that increases the opponent's path length.
    We test a few candidate positions near the opponent.
    """
    or_, oc = opponent['row'], opponent['col']
    human_goal = 0  # Human (player 1) needs to reach row 0

    # Get current opponent path length
    current_dist = _bfs_distance(board, or_, oc, human_goal)

    best_wall = None
    best_increase = 0

    # Try walls near the opponent's current position
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            wr, wc = or_ + dr, oc + dc
            for direction in ['H', 'V']:
                if board.can_place_wall(wr, wc, direction):
                    # Temporarily place wall
                    edges = board._wall_edges(wr, wc, direction)
                    for e in edges:
                        board.blocked_edges.add(e)

                    # Measure new distance
                    new_dist = _bfs_distance(board, or_, oc, human_goal)

                    # Remove temporary wall
                    for e in edges:
                        board.blocked_edges.remove(e)

                    increase = new_dist - current_dist
                    if increase > best_increase:
                        best_increase = increase
                        best_wall = (wr, wc, direction)

    return best_wall


def _bfs_distance(board, start_row, start_col, goal_row):
    """
    BFS to find shortest path distance (in steps) from start to goal_row.
    Returns a large number if unreachable.
    """
    from collections import deque

    queue = deque()
    queue.append((start_row, start_col, 0))
    visited = set()
    visited.add((start_row, start_col))

    while queue:
        row, col, dist = queue.popleft()
        if row == goal_row:
            return dist
        for (nr, nc) in board.get_neighbors(row, col):
            if (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc, dist + 1))

    return 999  # unreachable
