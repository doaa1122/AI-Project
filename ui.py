"""
ui.py - Enhanced Version
-----------------------
Updated with better goal region visualization and a modern sidebar layout.
"""

import pygame

# -------------------------------------------------------------------------
# Enhanced Color Palette
# -------------------------------------------------------------------------
BG_COLOR        = (24, 24, 32)        
BOARD_BG        = (200, 175, 135)     
GRID_COLOR      = (180, 160, 130)     
CELL_COLOR      = (245, 230, 200)     

PLAYER1_COLOR   = (220, 80, 60)       # Red (Human)
PLAYER2_COLOR   = (60, 120, 220)      # Blue (AI)
PLAYER1_SOFT    = (220, 80, 60, 60)   # For P1 Goal Area
PLAYER2_SOFT    = (60, 120, 220, 60)  # For P2 Goal Area

SIDEBAR_BG      = (30, 30, 42)
TEXT_COLOR      = (240, 240, 240)
TEXT_DIM        = (160, 165, 180)
ACCENT_COLOR    = (240, 200, 100)
BUTTON_COLOR    = (45, 45, 65)
BUTTON_ACTIVE   = (70, 130, 230)
BUTTON_HOVER    = (55, 55, 85)

# -------------------------------------------------------------------------
# Layout Constants
# -------------------------------------------------------------------------
CELL_SIZE   = 64
WALL_WIDTH  = 10
GAP         = 4
BOARD_OFFSET_X = 20
BOARD_OFFSET_Y = 30
SIDEBAR_X   = BOARD_OFFSET_X + 9 * CELL_SIZE + 30
SIDEBAR_WIDTH = 240
WINDOW_W    = SIDEBAR_X + SIDEBAR_WIDTH + 20
WINDOW_H    = BOARD_OFFSET_Y + 9 * CELL_SIZE + 30

def board_to_pixel(row, col):
    x = BOARD_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y

def pixel_to_cell(px, py):
    col = (px - BOARD_OFFSET_X) // CELL_SIZE
    row = (py - BOARD_OFFSET_Y) // CELL_SIZE
    if 0 <= row < 9 and 0 <= col < 9: return row, col
    return None

def pixel_to_wall_slot(px, py, orientation):
    col_f = (px - BOARD_OFFSET_X) / CELL_SIZE
    row_f = (py - BOARD_OFFSET_Y) / CELL_SIZE
    if orientation == 'H':
        row, col = int(row_f - 0.5), int(col_f)
    else:
        row, col = int(row_f), int(col_f - 0.5)
    if 0 <= row <= 7 and 0 <= col <= 7: return row, col
    return None

class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font_title  = pygame.font.SysFont('Segoe UI', 36, bold=True)
        self.font_header = pygame.font.SysFont('Segoe UI', 20, bold=True)
        self.font_medium = pygame.font.SysFont('Segoe UI', 18)
        self.font_small  = pygame.font.SysFont('Segoe UI', 15)
        self.buttons = []
        self._build_buttons()

    def _build_buttons(self):
        bx = SIDEBAR_X
        # Grouped controls
        self.buttons = [
            {'label': 'Move Mode',    'action': 'mode_move',  'rect': pygame.Rect(bx, 280, 220, 40)},
            {'label': 'Wall Mode',    'action': 'mode_wall',  'rect': pygame.Rect(bx, 325, 220, 40)},
            {'label': 'Horizontal',      'action': 'orient_H',   'rect': pygame.Rect(bx, 370, 105, 35)},
            {'label': 'Vertical',        'action': 'orient_V',   'rect': pygame.Rect(bx + 115, 370, 105, 35)},
            {'label': 'Restart Game', 'action': 'reset',      'rect': pygame.Rect(bx, 565, 220, 45)},
        ]

    def draw_all(self, board, game_mode, mouse_pos):
        self.screen.fill(BG_COLOR)
        self._draw_board(board, mouse_pos)
        self._draw_sidebar(board, game_mode, mouse_pos)
        if board.winner:
            self._draw_winner(board.winner)

    def _draw_board(self, board, mouse_pos):
        # Draw the Board Container
        board_rect = pygame.Rect(BOARD_OFFSET_X-8, BOARD_OFFSET_Y-8, 9*CELL_SIZE+16, 9*CELL_SIZE+16)
        pygame.draw.rect(self.screen, BOARD_BG, board_rect, border_radius=10)

        # Highlight Goal Zones (Blue for AI top goal, Red for Human bottom goal)
        for c in range(9):
            # AI Goal (Row 8) - Player 2 goal
            self._draw_cell_highlight(8, c, PLAYER2_SOFT)
            # Human Goal (Row 0) - Player 1 goal
            self._draw_cell_highlight(0, c, PLAYER1_SOFT)

        # Draw Cells
        for r in range(9):
            for c in range(9):
                rect = pygame.Rect(BOARD_OFFSET_X + c*CELL_SIZE + GAP, BOARD_OFFSET_Y + r*CELL_SIZE + GAP, 
                                   CELL_SIZE - GAP*2, CELL_SIZE - GAP*2)
                pygame.draw.rect(self.screen, CELL_COLOR, rect, border_radius=4)

        # Move Highlights
        if board.mode == 'move' and not board.winner:
            highlight_color = (220, 80, 60, 90) if board.current_turn == 1 else (60, 120, 220, 90)
            for (r, c) in board.get_valid_pawn_moves():
                self._draw_cell_highlight(r, c, highlight_color)

        # Wall Preview and Placed Walls
        if board.mode == 'wall' and not board.winner:
            slot = pixel_to_wall_slot(mouse_pos[0], mouse_pos[1], board.wall_orientation)
            if slot: self._draw_wall_preview(slot[0], slot[1], board.wall_orientation, board)
        
        for (wr, wc, direction) in board.placed_walls:
            self._draw_wall(wr, wc, direction)

        self._draw_pawn(board.player1['row'], board.player1['col'], PLAYER1_COLOR, "1")
        self._draw_pawn(board.player2['row'], board.player2['col'], PLAYER2_COLOR, "2")

    def _draw_cell_highlight(self, r, c, color):
        s = pygame.Surface((CELL_SIZE - GAP*2, CELL_SIZE - GAP*2), pygame.SRCALPHA)
        s.fill(color)
        self.screen.blit(s, (BOARD_OFFSET_X + c*CELL_SIZE + GAP, BOARD_OFFSET_Y + r*CELL_SIZE + GAP))

    def _draw_pawn(self, row, col, color, label):
        x, y = board_to_pixel(row, col)
        pygame.draw.circle(self.screen, (0, 0, 0, 60), (x+3, y+3), 22) # Shadow
        pygame.draw.circle(self.screen, color, (x, y), 22)
        pygame.draw.circle(self.screen, (255,255,255), (x, y), 22, 2) # Border
        txt = self.font_header.render(label, True, (255,255,255))
        self.screen.blit(txt, (x - txt.get_width()//2, y - txt.get_height()//2))

    def _draw_wall(self, row, col, direction):
        color = (200, 140, 40)
        if direction == 'H':
            rect = pygame.Rect(BOARD_OFFSET_X + col*CELL_SIZE + GAP, 
                               BOARD_OFFSET_Y + (row+1)*CELL_SIZE - WALL_WIDTH//2, 
                               CELL_SIZE*2 - GAP, WALL_WIDTH)
        else:
            rect = pygame.Rect(BOARD_OFFSET_X + (col+1)*CELL_SIZE - WALL_WIDTH//2, 
                               BOARD_OFFSET_Y + row*CELL_SIZE + GAP, 
                               WALL_WIDTH, CELL_SIZE*2 - GAP)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)

    def _draw_wall_preview(self, row, col, direction, board):
        is_valid = board.can_place_wall(row, col, direction)
        color = (100, 255, 100, 150) if is_valid else (255, 100, 100, 150)
        # Similar logic to _draw_wall but using a transparent Surface
        w, h = (CELL_SIZE*2 - GAP, WALL_WIDTH) if direction == 'H' else (WALL_WIDTH, CELL_SIZE*2 - GAP)
        x = BOARD_OFFSET_X + col*CELL_SIZE + GAP if direction == 'H' else BOARD_OFFSET_X + (col+1)*CELL_SIZE - WALL_WIDTH//2
        y = BOARD_OFFSET_Y + (row+1)*CELL_SIZE - WALL_WIDTH//2 if direction == 'H' else BOARD_OFFSET_Y + row*CELL_SIZE + GAP
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(color)
        self.screen.blit(s, (x, y))

    def _draw_sidebar(self, board, game_mode, mouse_pos):
        bx = SIDEBAR_X
        pygame.draw.rect(self.screen, SIDEBAR_BG, (bx-15, 0, SIDEBAR_WIDTH+30, WINDOW_H))
        
        # Header
        title = self.font_title.render("QUORIDOR", True, ACCENT_COLOR)
        self.screen.blit(title, (bx, 30))
        
        # Turn Indicator Box
        turn_rect = pygame.Rect(bx, 100, 220, 60)
        color = PLAYER1_COLOR if board.current_turn == 1 else PLAYER2_COLOR
        pygame.draw.rect(self.screen, color, turn_rect, border_radius=8)
        turn_txt = self.font_header.render(f"PLAYER {board.current_turn}'s TURN", True, (255,255,255))
        self.screen.blit(turn_txt, (bx + 110 - turn_txt.get_width()//2, 118))

        # Status Info
        p1_walls = self.font_medium.render(f"Player 1 Walls: {board.player1['walls']}", True, PLAYER1_COLOR)
        p2_walls = self.font_medium.render(f"Player 2 Walls: {board.player2['walls']}", True, PLAYER2_COLOR)
        self.screen.blit(p1_walls, (bx, 180))
        self.screen.blit(p2_walls, (bx, 210))

        # Button Sections
        label = self.font_small.render("ACTIONS", True, TEXT_DIM)
        self.screen.blit(label, (bx, 255))
        for btn in self.buttons:
            self._draw_button(btn, board, mouse_pos)

        # Keyboard Help
        help_y = 440
        pygame.draw.line(self.screen, BUTTON_COLOR, (bx, help_y-10), (bx+220, help_y-10))
        for line in ["W: Toggle Mode", "H/V: Orientation", "R: Restart", "Esc: Main Menu"]:
            h_txt = self.font_small.render(line, True, TEXT_DIM)
            self.screen.blit(h_txt, (bx, help_y))
            help_y += 22

    def _draw_button(self, btn, board, mouse_pos):
        rect, action = btn['rect'], btn['action']
        is_active = (action == 'mode_move' and board.mode == 'move') or \
                    (action == 'mode_wall' and board.mode == 'wall') or \
                    (action == 'orient_H' and board.wall_orientation == 'H') or \
                    (action == 'orient_V' and board.wall_orientation == 'V')
        
        bg_color = BUTTON_ACTIVE if is_active else (BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR)
        pygame.draw.rect(self.screen, bg_color, rect, border_radius=6)
        txt = self.font_small.render(btn['label'], True, (255,255,255))
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    def _draw_winner(self, winner):
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        msg = f"PLAYER {winner} WINS!"
        txt = self.font_title.render(msg, True, ACCENT_COLOR)
        self.screen.blit(txt, (WINDOW_W//2 - txt.get_width()//2, WINDOW_H//2 - 20))

    def get_button_action(self, pos):
        for btn in self.buttons:
            if btn['rect'].collidepoint(pos): return btn['action']
        return None

    def is_board_click(self, pos):
        return (BOARD_OFFSET_X <= pos[0] < BOARD_OFFSET_X + 9*CELL_SIZE and 
                BOARD_OFFSET_Y <= pos[1] < BOARD_OFFSET_Y + 9*CELL_SIZE)