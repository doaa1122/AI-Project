"""
main.py
-------
Entry point for the Quoridor game.

Handles:
- Game initialization
- The main game loop
- User input (mouse clicks and keyboard)
- Game mode selection (Human vs Human, Human vs AI)
- Connecting UI actions to Board logic
- Triggering AI moves
"""

import pygame
import sys
import time

from board import Board
from ui import UI, pixel_to_cell, pixel_to_wall_slot, WINDOW_W, WINDOW_H
from ai import get_easy_move, get_hard_move


# -------------------------------------------------------------------------
# Game Mode Menu
# -------------------------------------------------------------------------
def show_menu(screen):
    """
    Show a simple startup menu to choose game mode and AI difficulty.
    Returns: ('hvh', None), ('hvc', 'easy'), or ('hvc', 'hard')
    """
    font_title  = pygame.font.SysFont('Segoe UI', 42, bold=True)
    font_option = pygame.font.SysFont('Segoe UI', 26)
    font_small  = pygame.font.SysFont('Segoe UI', 18)

    # Colors (R, G, B)
    BG       = (30, 30, 40) # BG is background color
    TITLE_C  = (240, 200, 100) # TITLE_C is title color
    TEXT_C   = (240, 240, 240) # TEXT_C is text color
    DIM_C    = (150, 150, 160) # DIM_C is dimmed text color
    BTN_C    = (50, 50, 70) # BTN_C is button color
    BTN_H    = (80, 80, 110) # BTN_H is button hover color
    BTN_A    = (80, 140, 220) # BTN_A is button active color (not used in this menu but reserved for future use)

    # List of buttons with their labels, return values, and rectangles for click detection
    buttons = [
        {'label': 'Human vs Human',       'value': ('hvh', None),     'rect': pygame.Rect(WINDOW_W//2 - 180, 250, 360, 56)},
        {'label': 'Human vs AI (Easy)',    'value': ('hvc', 'easy'),   'rect': pygame.Rect(WINDOW_W//2 - 180, 328, 360, 56)},
        {'label': 'Human vs AI (Hard)',    'value': ('hvc', 'hard'),   'rect': pygame.Rect(WINDOW_W//2 - 180, 405, 360, 56)},
    ]

    clock = pygame.time.Clock() # Create a clock to control the frame rate of the menu loop

    # Main menu loop
    while True:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG)

        # Title
        title = font_title.render("QUORIDOR", True, TITLE_C)
        screen.blit(title, (WINDOW_W//2 - title.get_width()//2, 80)) # blit used to draw the title on the screen at a centered position

        subtitle = font_small.render("Abstract Strategy Board Game", True, DIM_C)
        screen.blit(subtitle, (WINDOW_W//2 - subtitle.get_width()//2, 137))

        pygame.draw.line(screen, (50, 50, 70), (WINDOW_W//2 - 180, 163), (WINDOW_W//2 + 180, 163), 1)

        choose_lbl = font_option.render("Select Game Mode", True, TEXT_C)
        screen.blit(choose_lbl, (WINDOW_W//2 - choose_lbl.get_width()//2, 198))

        # Draw buttons
        for btn in buttons:
            rect = btn['rect']
            color = BTN_H if rect.collidepoint(mouse_pos) else BTN_C
            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, (80, 80, 110), rect, 1, border_radius=10)
            lbl = font_option.render(btn['label'], True, TEXT_C)
            screen.blit(lbl, (rect.x + (rect.width - lbl.get_width())//2,
                               rect.y + (rect.height - lbl.get_height())//2))

        # Footer note
        note = font_small.render("You play as Player 1 (Red) | AI plays as Player 2 (Blue)", True, DIM_C)
        screen.blit(note, (WINDOW_W//2 - note.get_width()//2, 525))

        pygame.display.flip() # Update the display with all the drawn elements
        clock.tick(60) # Limit the menu loop to 60 frames per second

        # Event handling for menu
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # event.button == 1 checks for LEFT mouse button click
                for btn in buttons:
                    if btn['rect'].collidepoint(event.pos):
                        return btn['value']


# -------------------------------------------------------------------------
# Main game function
# -------------------------------------------------------------------------
def run_game(screen, game_mode, ai_difficulty):
    """
    Main game loop.

    Parameters:
        screen       - pygame display surface
        game_mode    - 'hvh' (human vs human) or 'hvc' (human vs computer)
        ai_difficulty- None, 'easy', or 'hard'
    """
    board = Board()
    ui    = UI(screen)
    clock = pygame.time.Clock()

    # AI is always Player 2
    ai_turn = 2

    # Small delay between frames to let the screen update before AI move
    ai_thinking = False
    ai_think_timer = 0

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos() # always check mouse position
        current_time = pygame.time.get_ticks() # for AI thinking delay.

        # ---------------------------------------------------------------
        # AI move logic
        # ---------------------------------------------------------------
        if (game_mode == 'hvc' and board.current_turn == ai_turn 
                and not board.winner and not ai_thinking):
            # Start a short "thinking" delay so it doesn't feel instant
            ai_thinking = True
            ai_think_timer = current_time + 400  # 400ms delay

        if ai_thinking and current_time >= ai_think_timer:
            ai_thinking = False
            _do_ai_move(board, ai_difficulty)


        # ---------------------------------------------------------------
        # Events
        # ---------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                _handle_key(event.key, board, screen, game_mode, ai_difficulty)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Don't allow input during AI turn
                if game_mode == 'hvc' and board.current_turn == ai_turn:
                    continue

                # First check if a sidebar button was clicked, otherwise check for board clicks
                action = ui.get_button_action(mouse_pos) # action will be None if no button was clicked, otherwise it will be a string like 'mode_move', 'orient_H', etc.
                if action:
                    _handle_button(action, board, screen, game_mode, ai_difficulty)
                elif ui.is_board_click(mouse_pos) and not board.winner:
                    _handle_board_click(mouse_pos, board)

        # ---------------------------------------------------------------
        # Draw
        # ---------------------------------------------------------------
        ui.draw_all(board, game_mode, mouse_pos)
        pygame.display.flip()
        clock.tick(60)


# -------------------------------------------------------------------------
# Input handlers
# -------------------------------------------------------------------------
def _handle_key(key, board, screen, game_mode, ai_difficulty):
    """Handle keyboard shortcuts."""
    if key == pygame.K_r:
        # Reset game
        board.reset()

    elif key == pygame.K_w:
        # Toggle between move and wall mode
        board.mode = 'wall' if board.mode == 'move' else 'move'

    elif key == pygame.K_h:
        # Set horizontal wall orientation
        board.wall_orientation = 'H'
        board.mode = 'wall'

    elif key == pygame.K_v:
        # Set vertical wall orientation
        board.wall_orientation = 'V'
        board.mode = 'wall'

    elif key == pygame.K_m:
        # Switch back to move mode
        board.mode = 'move'

    elif key == pygame.K_ESCAPE:
        # Go back to menu (restart)
        main()


def _handle_button(action, board, screen, game_mode, ai_difficulty):
    """Handle sidebar button clicks."""
    if action == 'mode_move':
        board.mode = 'move'
    elif action == 'mode_wall':
        board.mode = 'wall'
    elif action == 'orient_H':
        board.wall_orientation = 'H'
    elif action == 'orient_V':
        board.wall_orientation = 'V'
    elif action == 'reset':
        board.reset()


def _handle_board_click(mouse_pos, board):
    """
    Handle a click on the board area.
    - In 'move' mode: try to move the pawn to the clicked cell.
    - In 'wall' mode: try to place a wall at the clicked position.
    """
    if board.mode == 'move':
        cell = pixel_to_cell(mouse_pos[0], mouse_pos[1]) # Convert pixel coordinates to board cell (row, col)
        if cell: # If the click was within the board area and corresponds to a valid cell
            row, col = cell
            board.move_pawn(row, col)

    elif board.mode == 'wall':
        slot = pixel_to_wall_slot(mouse_pos[0], mouse_pos[1], board.wall_orientation)
        if slot:
            row, col = slot
            board.place_wall(row, col, board.wall_orientation)


def _do_ai_move(board, difficulty):
    """Ask the AI for a move and apply it to the board."""
    if difficulty == 'easy':
        move = get_easy_move(board)
    else:  # 'hard'
        move = (board)

    if move is None:
        # Fallback: just switch turn (Safety measure in case AI is implemented incorrectly)
        board.switch_turn()
        return

    # expected move format: ('pawn', (row, col)) or ('wall', (row, col, direction))    
    move_type, data = move

    if move_type == 'pawn':
        row, col = data
        board.move_pawn(row, col)

    elif move_type == 'wall':
        row, col, direction = data
        board.place_wall(row, col, direction)


# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Quoridor")

    # Show menu, get game mode
    game_mode, ai_difficulty = show_menu(screen)

    # Run the game
    run_game(screen, game_mode, ai_difficulty)


if __name__ == '__main__':
    main()
