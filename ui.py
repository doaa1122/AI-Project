"""
ui.py
-----
All drawing / rendering code for the Quoridor game.

Responsibilities:
- Draw the 9x9 board grid
- Draw pawns
- Draw placed walls
- Highlight valid moves
- Show wall preview on hover
- Draw the sidebar (turn info, wall counts, mode buttons)
- Draw the winner overlay
"""

import pygame

# -------------------------------------------------------------------------
# Color palette
# -------------------------------------------------------------------------
BG_COLOR        = (30, 30, 40)        # Dark background
BOARD_BG        = (245, 230, 200)     # Warm wood color for board
GRID_COLOR      = (180, 160, 130)     # Grid lines
CELL_COLOR      = (245, 230, 200)     # Empty cell
CELL_HOVER      = (255, 245, 220)     # Hovered cell

PLAYER1_COLOR   = (220, 80, 60)       # Red player
PLAYER2_COLOR   = (60, 120, 220)      # Blue player
PLAYER1_DARK    = (160, 40, 20)
PLAYER2_DARK    = (20, 60, 160)

VALID_MOVE      = (100, 200, 100, 160)  # Green highlight (semi-transparent)
WALL_H_COLOR    = (200, 140, 40)      # Horizontal wall color (amber)
WALL_V_COLOR    = (200, 140, 40)      # Vertical wall color (amber)
WALL_PREVIEW    = (255, 200, 80, 180) # Wall preview color

SIDEBAR_BG      = (22, 22, 32)
TEXT_COLOR      = (240, 240, 240)
TEXT_DIM        = (150, 150, 160)
BUTTON_COLOR    = (50, 50, 70)
BUTTON_ACTIVE   = (80, 140, 220)
BUTTON_HOVER    = (60, 60, 90)

WIN_OVERLAY     = (0, 0, 0, 180)
WIN_TEXT_P1     = (220, 80, 60)
WIN_TEXT_P2     = (60, 120, 220)

# -------------------------------------------------------------------------
# Layout constants
# -------------------------------------------------------------------------
CELL_SIZE   = 64   # pixels per cell
WALL_WIDTH  = 10   # wall thickness in pixels
GAP         = 4    # small gap between cells
BOARD_OFFSET_X = 10
BOARD_OFFSET_Y = 10
SIDEBAR_X   = BOARD_OFFSET_X + 9 * CELL_SIZE + 20
SIDEBAR_WIDTH = 220
WINDOW_W    = SIDEBAR_X + SIDEBAR_WIDTH + 10
WINDOW_H    = BOARD_OFFSET_Y + 9 * CELL_SIZE + 10 + 10


def board_to_pixel(row, col):
    """Convert board cell (row, col) to pixel center coordinates."""
    x = BOARD_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def pixel_to_cell(px, py):
    """Convert pixel position to board cell (row, col). Returns None if outside board."""
    col = (px - BOARD_OFFSET_X) // CELL_SIZE
    row = (py - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= row < 9 and 0 <= col < 9:
        return row, col
    return None


def pixel_to_wall_slot(px, py, orientation):
    """
    Convert pixel position to wall anchor (row, col).
    For a wall, we snap to the nearest wall slot (0-7 range).
    """
    # Wall slots are between cells
    # For horizontal wall: snap to the edge between rows
    # For vertical wall: snap to the edge between cols
    col_f = (px - BOARD_OFFSET_X) / CELL_SIZE
    row_f = (py - BOARD_OFFSET_Y) / CELL_SIZE

    if orientation == 'H':
        row = int(row_f - 0.5)
        col = int(col_f)
    else:
        row = int(row_f)
        col = int(col_f - 0.5)

    if 0 <= row <= 7 and 0 <= col <= 7:
        return row, col
    return None


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font_large  = pygame.font.SysFont('Segoe UI', 28, bold=True)
        self.font_medium = pygame.font.SysFont('Segoe UI', 20)
        self.font_small  = pygame.font.SysFont('Segoe UI', 16)

        # Transparent surface for highlights
        self.highlight_surf = pygame.Surface((CELL_SIZE - GAP*2, CELL_SIZE - GAP*2), pygame.SRCALPHA)

        # Buttons: {'label': str, 'rect': Rect, 'action': str}
        self.buttons = []
        self._build_buttons()

        self.hovered_cell = None
        self.hovered_wall = None

    def _build_buttons(self):
        """Define the sidebar buttons."""
        bx = SIDEBAR_X
        self.buttons = [
            {'label': '🚶 Move Pawn',   'action': 'mode_move',  'rect': pygame.Rect(bx, 200, 190, 44)},
            {'label': '🧱 Place Wall',  'action': 'mode_wall',  'rect': pygame.Rect(bx, 254, 190, 44)},
            {'label': '↔ Horizontal',  'action': 'orient_H',   'rect': pygame.Rect(bx, 320, 90, 38)},
            {'label': '↕ Vertical',    'action': 'orient_V',   'rect': pygame.Rect(bx + 100, 320, 90, 38)},
            {'label': '⟳ New Game',    'action': 'reset',      'rect': pygame.Rect(bx, 400, 190, 44)},
        ]

    def draw_all(self, board, game_mode, mouse_pos):
        """Main draw function — call this every frame."""
        self.screen.fill(BG_COLOR)
        self._draw_board(board, mouse_pos)
        self._draw_sidebar(board, game_mode, mouse_pos)
        if board.winner:
            self._draw_winner(board.winner)

    # -------------------------------------------------------------------------
    # Board drawing
    # -------------------------------------------------------------------------
    def _draw_board(self, board, mouse_pos):
        """Draw the grid, walls, highlights, and pawns."""
        # Board background
        board_rect = pygame.Rect(
            BOARD_OFFSET_X - 4, BOARD_OFFSET_Y - 4,
            9 * CELL_SIZE + 8, 9 * CELL_SIZE + 8
        )
        pygame.draw.rect(self.screen, (200, 175, 135), board_rect, border_radius=6)

        # Draw cells
        for row in range(9):
            for col in range(9):
                cx = BOARD_OFFSET_X + col * CELL_SIZE + GAP
                cy = BOARD_OFFSET_Y + row * CELL_SIZE + GAP
                cell_rect = pygame.Rect(cx, cy, CELL_SIZE - GAP*2, CELL_SIZE - GAP*2)
                pygame.draw.rect(self.screen, CELL_COLOR, cell_rect, border_radius=3)

        # Draw goal zones (subtle shading)
        for col in range(9):
            # Row 0 = Player 1's goal (faint red tint)
            cx = BOARD_OFFSET_X + col * CELL_SIZE + GAP
            cy = BOARD_OFFSET_Y + 0 * CELL_SIZE + GAP
            goal_rect = pygame.Rect(cx, cy, CELL_SIZE - GAP*2, CELL_SIZE - GAP*2)
            goal_surf = pygame.Surface(goal_rect.size, pygame.SRCALPHA)
            goal_surf.fill((220, 80, 60, 40))
            self.screen.blit(goal_surf, goal_rect.topleft)

            # Row 8 = Player 2's goal (faint blue tint)
            cy = BOARD_OFFSET_Y + 8 * CELL_SIZE + GAP
            goal_rect = pygame.Rect(cx, cy, CELL_SIZE - GAP*2, CELL_SIZE - GAP*2)
            goal_surf = pygame.Surface(goal_rect.size, pygame.SRCALPHA)
            goal_surf.fill((60, 120, 220, 40))
            self.screen.blit(goal_surf, goal_rect.topleft)

        # Highlight valid pawn moves
        if board.mode == 'move' and not board.winner:
            valid_moves = board.get_valid_pawn_moves()
            for (r, c) in valid_moves:
                cx = BOARD_OFFSET_X + c * CELL_SIZE + GAP
                cy = BOARD_OFFSET_Y + r * CELL_SIZE + GAP
                hl_surf = pygame.Surface((CELL_SIZE - GAP*2, CELL_SIZE - GAP*2), pygame.SRCALPHA)
                hl_surf.fill(VALID_MOVE)
                self.screen.blit(hl_surf, (cx, cy))

        # Wall preview on hover
        if board.mode == 'wall' and not board.winner:
            slot = pixel_to_wall_slot(mouse_pos[0], mouse_pos[1], board.wall_orientation)
            if slot:
                wr, wc = slot
                self._draw_wall_preview(wr, wc, board.wall_orientation, board)

        # Draw placed walls
        for (wr, wc, direction) in board.placed_walls:
            self._draw_wall(wr, wc, direction)

        # Draw pawns
        self._draw_pawn(board.player1['row'], board.player1['col'], PLAYER1_COLOR, PLAYER1_DARK, '1')
        self._draw_pawn(board.player2['row'], board.player2['col'], PLAYER2_COLOR, PLAYER2_DARK, '2')

        # Draw grid coordinate labels (optional, small)
        for i in range(9):
            label = self.font_small.render(str(i), True, (140, 110, 80))
            # Column numbers at top
            self.screen.blit(label, (BOARD_OFFSET_X + i * CELL_SIZE + CELL_SIZE//2 - 4, BOARD_OFFSET_Y - 14 + 4))
            # Row numbers at left
            self.screen.blit(label, (BOARD_OFFSET_X - 14, BOARD_OFFSET_Y + i * CELL_SIZE + CELL_SIZE//2 - 8))

    def _draw_pawn(self, row, col, color, dark_color, label):
        """Draw a circular pawn with a label."""
        x, y = board_to_pixel(row, col)
        radius = CELL_SIZE // 2 - 8

        # Shadow
        pygame.draw.circle(self.screen, (0, 0, 0, 80), (x + 3, y + 3), radius)
        # Main circle
        pygame.draw.circle(self.screen, color, (x, y), radius)
        # Highlight ring
        pygame.draw.circle(self.screen, dark_color, (x, y), radius, 3)

        # Player number label
        text = self.font_medium.render(label, True, (255, 255, 255))
        self.screen.blit(text, (x - text.get_width()//2, y - text.get_height()//2))

    def _draw_wall(self, row, col, direction, color=None, alpha=255):
        """Draw a placed wall segment."""
        if color is None:
            color = WALL_H_COLOR

        if direction == 'H':
            # Horizontal wall: sits on the bottom edge of row `row`
            # Covers two cell widths horizontally
            x = BOARD_OFFSET_X + col * CELL_SIZE + GAP
            y = BOARD_OFFSET_Y + (row + 1) * CELL_SIZE - WALL_WIDTH // 2
            w = CELL_SIZE * 2 - GAP
            h = WALL_WIDTH
        else:
            # Vertical wall: sits on the right edge of col `col`
            x = BOARD_OFFSET_X + (col + 1) * CELL_SIZE - WALL_WIDTH // 2
            y = BOARD_OFFSET_Y + row * CELL_SIZE + GAP
            w = WALL_WIDTH
            h = CELL_SIZE * 2 - GAP

        pygame.draw.rect(self.screen, color, pygame.Rect(x, y, w, h), border_radius=4)

    def _draw_wall_preview(self, row, col, direction, board):
        """Draw a semi-transparent preview of where a wall would be placed."""
        # Check if placement is valid
        if board.can_place_wall(row, col, direction):
            color = (100, 200, 100)  # green = valid
        else:
            color = (200, 80, 80)    # red = invalid

        if direction == 'H':
            x = BOARD_OFFSET_X + col * CELL_SIZE + GAP
            y = BOARD_OFFSET_Y + (row + 1) * CELL_SIZE - WALL_WIDTH // 2
            w = CELL_SIZE * 2 - GAP
            h = WALL_WIDTH
        else:
            x = BOARD_OFFSET_X + (col + 1) * CELL_SIZE - WALL_WIDTH // 2
            y = BOARD_OFFSET_Y + row * CELL_SIZE + GAP
            w = WALL_WIDTH
            h = CELL_SIZE * 2 - GAP

        preview_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        preview_surf.fill((*color, 150))
        self.screen.blit(preview_surf, (x, y))

    # -------------------------------------------------------------------------
    # Sidebar drawing
    # -------------------------------------------------------------------------
    def _draw_sidebar(self, board, game_mode, mouse_pos):
        """Draw the right sidebar with info and buttons."""
        # Sidebar background
        sidebar_rect = pygame.Rect(SIDEBAR_X - 10, 0, SIDEBAR_WIDTH + 20, WINDOW_H)
        pygame.draw.rect(self.screen, SIDEBAR_BG, sidebar_rect)

        bx = SIDEBAR_X

        # Title
        title = self.font_large.render("QUORIDOR", True, (240, 200, 100))
        self.screen.blit(title, (bx, 18))

        # Game mode
        mode_text = "Human vs Human" if game_mode == 'hvh' else "Human vs AI"
        mode_surf = self.font_small.render(mode_text, True, TEXT_DIM)
        self.screen.blit(mode_surf, (bx, 52))

        # Separator
        pygame.draw.line(self.screen, (50, 50, 70), (bx, 72), (bx + 190, 72), 1)

        # Current turn
        if not board.winner:
            turn_label = self.font_small.render("Current Turn:", True, TEXT_DIM)
            self.screen.blit(turn_label, (bx, 82))

            if board.current_turn == 1:
                turn_color = PLAYER1_COLOR
                turn_name = "Player 1 (Red)"
            else:
                turn_color = PLAYER2_COLOR
                turn_name = "Player 2 (Blue)"

            turn_surf = self.font_medium.render(turn_name, True, turn_color)
            self.screen.blit(turn_surf, (bx, 102))

        # Player wall counts
        pygame.draw.line(self.screen, (50, 50, 70), (bx, 140), (bx + 190, 140), 1)

        p1_label = self.font_small.render("Player 1 Walls:", True, TEXT_DIM)
        self.screen.blit(p1_label, (bx, 148))
        p1_walls = self.font_medium.render(f"{'▪' * board.player1['walls']}  ({board.player1['walls']})", True, PLAYER1_COLOR)
        self.screen.blit(p1_walls, (bx, 166))

        p2_label = self.font_small.render("Player 2 Walls:", True, TEXT_DIM)
        self.screen.blit(p2_label, (bx, 186))  # adjusted spacing

        # Shift everything below down slightly
        p2_walls = self.font_medium.render(f"{'▪' * board.player2['walls']}  ({board.player2['walls']})", True, PLAYER2_COLOR)
        self.screen.blit(p2_walls, (bx, 204))

        # Separator
        pygame.draw.line(self.screen, (50, 50, 70), (bx, 230), (bx + 190, 230), 1)

        # Mode label
        mode_lbl = self.font_small.render("Action Mode:", True, TEXT_DIM)
        self.screen.blit(mode_lbl, (bx, 238))

        # Draw buttons
        for btn in self.buttons:
            self._draw_button(btn, board, mouse_pos)

        # Controls help
        pygame.draw.line(self.screen, (50, 50, 70), (bx, 460), (bx + 190, 460), 1)
        help_lines = [
            "Controls:",
            "• Click cell = move pawn",
            "• W key = toggle wall mode",
            "• R key = new game",
            "• H/V key = wall orientation",
        ]
        y = 468
        for line in help_lines:
            color = TEXT_DIM if line != "Controls:" else (200, 200, 210)
            surf = self.font_small.render(line, True, color)
            self.screen.blit(surf, (bx, y))
            y += 18

    def _draw_button(self, btn, board, mouse_pos):
        """Draw a single sidebar button."""
        rect = btn['rect']
        action = btn['action']

        # Determine active/hover state
        is_active = False
        if action == 'mode_move' and board.mode == 'move':
            is_active = True
        elif action == 'mode_wall' and board.mode == 'wall':
            is_active = True
        elif action == 'orient_H' and board.wall_orientation == 'H':
            is_active = True
        elif action == 'orient_V' and board.wall_orientation == 'V':
            is_active = True

        is_hovered = rect.collidepoint(mouse_pos)

        if is_active:
            color = BUTTON_ACTIVE
        elif is_hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR

        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, (80, 80, 110), rect, 1, border_radius=6)

        label = self.font_small.render(btn['label'], True, TEXT_COLOR)
        lx = rect.x + (rect.width - label.get_width()) // 2
        ly = rect.y + (rect.height - label.get_height()) // 2
        self.screen.blit(label, (lx, ly))

    # -------------------------------------------------------------------------
    # Winner overlay
    # -------------------------------------------------------------------------
    def _draw_winner(self, winner):
        """Draw a semi-transparent overlay announcing the winner."""
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Box
        box_rect = pygame.Rect(WINDOW_W//2 - 180, WINDOW_H//2 - 80, 360, 160)
        pygame.draw.rect(self.screen, (30, 30, 45), box_rect, border_radius=16)
        pygame.draw.rect(self.screen, (200, 180, 100), box_rect, 3, border_radius=16)

        color = WIN_TEXT_P1 if winner == 1 else WIN_TEXT_P2
        name = "Player 1" if winner == 1 else "Player 2"

        win_text = self.font_large.render(f"🏆 {name} Wins!", True, color)
        self.screen.blit(win_text, (WINDOW_W//2 - win_text.get_width()//2, WINDOW_H//2 - 50))

        sub_text = self.font_medium.render("Press R to play again", True, TEXT_DIM)
        self.screen.blit(sub_text, (WINDOW_W//2 - sub_text.get_width()//2, WINDOW_H//2 + 10))

    # -------------------------------------------------------------------------
    # Hit testing for input
    # -------------------------------------------------------------------------
    def get_button_action(self, pos):
        """Return the action string of the button clicked, or None."""
        for btn in self.buttons:
            if btn['rect'].collidepoint(pos):
                return btn['action']
        return None

    def is_board_click(self, pos):
        """Return True if the click is within the board area."""
        bx, by = pos
        return (BOARD_OFFSET_X <= bx < BOARD_OFFSET_X + 9 * CELL_SIZE and
                BOARD_OFFSET_Y <= by < BOARD_OFFSET_Y + 9 * CELL_SIZE)
