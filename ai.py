"""
ai.py
-----
Contains the AI logic for the computer opponent.

Easy AI:
    - Moves toward the goal following the shortest path.
    - 15% chance to place a valid random wall.

Hard AI:
    - Greedy evaluation: compares (Human_Path_Length - AI_Path_Length).
    - Selects the action (move or wall) with the best immediate advantage.
"""

import random
from collections import deque
from pathfinding import bfs_has_path


def get_easy_move(board):
    """
    Easy AI: Move along the actual shortest path to the goal using BFS.
    15% chance to place a valid random wall if walls available.
    """
    player = board.current_player()
    
    # 15% chance to try placing a wall
    if player['walls'] > 0 and random.random() < 0.15:
        wall_move = _find_blocking_wall(board)
        if wall_move:
            return ('wall', wall_move)
    
    # Get goal row for current player
    goal_row = 8 if board.current_turn == 2 else 0
    
    # Find the first move in the shortest path using BFS
    next_move = _get_first_move_in_shortest_path(
        board,
        player['row'],
        player['col'],
        goal_row
    )
    
    if next_move:
        return ('pawn', next_move)
    
    # Fallback: if no path found, try any valid move
    pawn_moves = board.get_valid_pawn_moves()
    if pawn_moves:
        return ('pawn', pawn_moves[0])
    
    return None


def get_hard_move(board):
    """
    Hard AI: Greedy evaluation of moves vs walls.
    
    Compare each option and select the action that maximizes:
    (Human_Shortest_Path_Length - AI_Shortest_Path_Length)
    """
    player = board.current_player()
    opponent = board.other_player()
    
    # Current state path lengths
    ai_path_length = _get_shortest_path_length(
        board,
        player['row'],
        player['col'],
        8 if board.current_turn == 2 else 0
    )
    opponent_path_length = _get_shortest_path_length(
        board,
        opponent['row'],
        opponent['col'],
        0 if board.current_turn == 2 else 8
    )
    
    current_advantage = opponent_path_length - ai_path_length
    best_action = None
    best_advantage = current_advantage
    
    # Evaluate pawn moves
    pawn_moves = board.get_valid_pawn_moves()
    for move_r, move_c in pawn_moves:
        # Simulate move
        old_r, old_c = player['row'], player['col']
        player['row'] = move_r
        player['col'] = move_c
        
        new_ai_path = _get_shortest_path_length(
            board,
            move_r,
            move_c,
            8 if board.current_turn == 2 else 0
        )
        new_advantage = opponent_path_length - new_ai_path
        
        # Undo move
        player['row'] = old_r
        player['col'] = old_c
        
        if new_advantage > best_advantage:
            best_advantage = new_advantage
            best_action = ('pawn', (move_r, move_c))
    
    # Evaluate wall placements
    if player['walls'] > 0:
        walls_to_try = _get_walls_near_players(board, max_distance=3)
        for row, col, direction in walls_to_try:
            if not board.can_place_wall(row, col, direction):
                continue
            
            # Simulate wall placement
            new_edges = board._wall_edges(row, col, direction)
            for edge in new_edges:
                board.blocked_edges.add(edge)
            
            opponent_new_path = _get_shortest_path_length(
                board,
                opponent['row'],
                opponent['col'],
                0 if board.current_turn == 2 else 8
            )
            new_advantage = opponent_new_path - ai_path_length
            
            # Undo wall
            for edge in new_edges:
                board.blocked_edges.remove(edge)
            
            if new_advantage > best_advantage:
                best_advantage = new_advantage
                best_action = ('wall', (row, col, direction))
    
    # If we found a good action, use it; otherwise move toward goal
    if best_action:
        return best_action
    
    # Default: move toward goal
    if pawn_moves:
        goal_row = 8 if board.current_turn == 2 else 0
        best_move = min(pawn_moves, key=lambda m: abs(m[0] - goal_row))
        return ('pawn', best_move)
    
    return None



# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------

def _get_shortest_path_length(board, start_row, start_col, goal_row):
    """
    Use BFS to find the shortest path length from start to goal_row.
    Returns the distance (number of moves), or float('inf') if no path exists.
    """
    queue = deque([(start_row, start_col, 0)])  # (row, col, distance)
    visited = {(start_row, start_col)}
    
    while queue:
        row, col, dist = queue.popleft()
        
        if row == goal_row:
            return dist
        
        for neighbor_r, neighbor_c in board.get_neighbors(row, col):
            if (neighbor_r, neighbor_c) not in visited:
                visited.add((neighbor_r, neighbor_c))
                queue.append((neighbor_r, neighbor_c, dist + 1))
    
    return float('inf')


def _get_first_move_in_shortest_path(board, start_row, start_col, goal_row):
    """
    Use BFS to find the first move along the shortest path to goal_row.
    Returns (row, col) of the next cell in the shortest path, or None if no path exists.
    
    This ensures the AI can navigate around obstacles by moving along the actual
    shortest path instead of greedily moving based on row distance alone.
    """
    # Get the current distance to the goal
    current_distance = _get_shortest_path_length(board, start_row, start_col, goal_row)
    
    if current_distance == float('inf'):
        return None
    
    # Check all valid neighbors and find one that's on the shortest path
    # A neighbor is on the shortest path if its distance to goal = current_distance - 1
    for neighbor_r, neighbor_c in board.get_neighbors(start_row, start_col):
        neighbor_distance = _get_shortest_path_length(board, neighbor_r, neighbor_c, goal_row)
        if neighbor_distance == current_distance - 1:
            return (neighbor_r, neighbor_c)
    
    # Shouldn't reach here if current_distance is not infinity
    return None


def _get_walls_near_players(board, max_distance=3):
    """
    Return wall placements within max_distance cells of either player.
    This optimization reduces the search space for wall evaluation.
    """
    p1 = board.player1
    p2 = board.player2
    candidate_walls = []
    
    for row in range(8):
        for col in range(8):
            for direction in ['H', 'V']:
                # Check if wall is within max_distance of either player
                p1_dist = abs(row - p1['row']) + abs(col - p1['col'])
                p2_dist = abs(row - p2['row']) + abs(col - p2['col'])
                
                if p1_dist <= max_distance or p2_dist <= max_distance:
                    candidate_walls.append((row, col, direction))
    
    return candidate_walls


def _random_wall(board):
    """Try random wall placements until one is valid or give up after 30 tries."""
    for _ in range(30):
        row = random.randint(0, 7)
        col = random.randint(0, 7)
        direction = random.choice(['H', 'V'])
        if board.can_place_wall(row, col, direction):
            return (row, col, direction)
    return None


def _find_blocking_wall(board):
    """
    Try to find a wall that increases the opponent's path length to their goal.
    This makes the easy AI's wall placement more strategic.
    
    Returns (row, col, direction) of a wall that blocks the opponent, or None.
    """
    opponent = board.other_player()
    opponent_goal = 0 if board.current_turn == 2 else 8
    
    # Get the opponent's current shortest path length
    current_path_length = _get_shortest_path_length(
        board,
        opponent['row'],
        opponent['col'],
        opponent_goal
    )
    
    # If opponent has no path, no point in placing walls
    if current_path_length == float('inf'):
        return None
    
    # Look for walls near the opponent
    candidate_walls = _get_walls_near_players(board, max_distance=2)
    
    # Shuffle to randomize which blocking wall we pick
    random.shuffle(candidate_walls)
    
    # Try to find a wall that increases the opponent's path length
    for row, col, direction in candidate_walls:
        if not board.can_place_wall(row, col, direction):
            continue
        
        # Temporarily place the wall
        new_edges = board._wall_edges(row, col, direction)
        for edge in new_edges:
            board.blocked_edges.add(edge)
        
        # Check the new path length
        new_path_length = _get_shortest_path_length(
            board,
            opponent['row'],
            opponent['col'],
            opponent_goal
        )
        
        # Remove the temporary wall
        for edge in new_edges:
            board.blocked_edges.remove(edge)
        
        # If this wall blocks the path or increases its length, use it
        if new_path_length > current_path_length:
            return (row, col, direction)
    
    # If no blocking wall found, fall back to random wall
    return _random_wall(board)
