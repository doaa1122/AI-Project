"""
pathfinding.py
--------------
Uses BFS (Breadth-First Search) to check if a player still has
a valid path to their goal after a wall is placed.

This is important because Quoridor rules say: you cannot place a
wall that completely blocks a player from reaching the other side.
"""

from collections import deque


def bfs_has_path(board, start_row, start_col, goal_row, player_id):
    """
    Check if there is a valid path from (start_row, start_col)
    to any cell in goal_row using BFS.

    Parameters:
        board      - the Board object (contains wall info)
        start_row  - starting row of the pawn
        start_col  - starting column of the pawn
        goal_row   - the row the player needs to reach to win
        player_id  - which player (1 or 2), not used for pathing but helpful for context

    Returns:
        True if a path exists, False otherwise.
    """

    # Queue holds (row, col) positions to explore
    queue = deque()
    queue.append((start_row, start_col))

    # Keep track of visited cells so we don't revisit them
    visited = set()
    visited.add((start_row, start_col))

    while queue:
        row, col = queue.popleft()

        # Check if we reached the goal row
        if row == goal_row:
            return True

        # Try all 4 directions: up, down, left, right
        neighbors = board.get_neighbors(row, col)
        for (nrow, ncol) in neighbors:
            if (nrow, ncol) not in visited:
                visited.add((nrow, ncol))
                queue.append((nrow, ncol))

    # We exhausted all reachable cells without hitting the goal row
    return False


def both_players_have_path(board):
    """
    Check that BOTH players still have a valid path after a wall is placed.

    Returns:
        True if both players can still reach their goals, False otherwise.
    """
    p1 = board.player1
    p2 = board.player2

    # Player 1 starts near row 8, needs to reach row 0
    p1_can_reach = bfs_has_path(board, p1['row'], p1['col'], 0, 1)

    # Player 2 starts near row 0, needs to reach row 8
    p2_can_reach = bfs_has_path(board, p2['row'], p2['col'], 8, 2)

    return p1_can_reach and p2_can_reach
