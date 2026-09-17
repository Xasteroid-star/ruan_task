"""pygame 绘制：棋盘、箭头、飞出 / 碰撞动画、HUD 与各界面。"""
from __future__ import annotations

import math

import pygame

from . import config


def board_origin(cols: int) -> tuple[int, int]:
    """返回棋盘左上角像素坐标（水平居中）。"""
    board_px = cols * config.CELL_SIZE
    x = (config.WINDOW_WIDTH - board_px) // 2
    return x, config.BOARD_TOP


def cell_center(origin_x: int, origin_y: int, row: int, col: int) -> tuple[int, int]:
    """返回格子中心的像素坐标。"""
    cx = origin_x + col * config.CELL_SIZE + config.CELL_SIZE // 2
    cy = origin_y + row * config.CELL_SIZE + config.CELL_SIZE // 2
    return cx, cy


def _load_font(size: int) -> pygame.font.Font:
    """优先加载支持中文的系统字体，失败则回退默认字体。"""
    for name in ("microsoftyahei", "msyh", "simhei", "simsun", "dengxian"):
        path = pygame.font.match_font(name)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


class Renderer:
    """缓存字体，提供各界面绘制。"""

    def __init__(self):
        pygame.font.init()
        self.font_title = _load_font(48)
        self.font_large = _load_font(32)
        self.font_medium = _load_font(26)
        self.font_small = _load_font(20)

    # ---------- 通用 ----------
    def draw_text(self, screen, text, font, color, center=None, topleft=None):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center is not None:
            rect.center = center
        elif topleft is not None:
            rect.topleft = topleft
        screen.blit(surface, rect)

    def draw_button(self, screen, rect, text, hover=False):
        color = config.BUTTON_HOVER if hover else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        self.draw_text(screen, text, self.font_medium, config.BUTTON_TEXT, center=rect.center)

    # ---------- 按钮区域 ----------
    def start_button_rect(self):
        w, h = 240, 64
        return pygame.Rect((config.WINDOW_WIDTH - w) // 2,
                           config.WINDOW_HEIGHT // 2 + 80, w, h)

    def restart_button_rect(self):
        return pygame.Rect(config.WINDOW_WIDTH - 150, 34, 120, 46)

    def next_button_rect(self):
        w, h = 240, 64
        return pygame.Rect((config.WINDOW_WIDTH - w) // 2,
                           config.WINDOW_HEIGHT // 2 + 40, w, h)

    # ---------- 箭头 ----------
    def draw_arrow(self, screen, cx, cy, direction, cell, color):
        """在 (cx, cy) 处画一个指向 direction 的箭头（杆 + 三角头）。"""
        dr, dc = direction.vector
        half = cell * 0.36
        head = cell * 0.26
        tip = (cx + dc * half, cy + dr * half)
        tail = (cx - dc * half, cy - dr * half)
        px, py = -dr, dc  # 垂直于朝向的向量
        base = (tip[0] - dc * head, tip[1] - dr * head)
        p1 = (base[0] + px * head, base[1] + py * head)
        p2 = (base[0] - px * head, base[1] - py * head)
        pygame.draw.line(screen, color, tail, tip, max(3, int(cell * 0.09)))
        pygame.draw.polygon(screen, color, [tip, p1, p2])

    # ---------- 棋盘 ----------
    def draw_board(self, screen, game, flying, shake):
        level = game.current_level
        ox, oy = board_origin(level.cols)
        cell = config.CELL_SIZE
        board_rect = pygame.Rect(ox - 10, oy - 10,
                                 level.cols * cell + 20, level.rows * cell + 20)
        pygame.draw.rect(screen, config.BOARD_COLOR, board_rect, border_radius=12)
        for r in range(level.rows):
            for c in range(level.cols):
                rect = pygame.Rect(ox + c * cell, oy + r * cell, cell, cell)
                pygame.draw.rect(screen, config.CELL_COLOR, rect)
                pygame.draw.rect(screen, config.LINE_COLOR, rect, 1)
        # 正常箭头
        for pos, arrow in game.board.arrows.items():
            if pos in shake:
                continue
            cx, cy = cell_center(ox, oy, *pos)
            self.draw_arrow(screen, cx, cy, arrow.direction, cell, config.ARROW_COLOR)
        # 被碰撞的箭头：抖动 + 变红
        for pos, frames in shake.items():
            arrow = game.board.arrow_at(*pos)
            if arrow is None:
                continue
            cx, cy = cell_center(ox, oy, *pos)
            offset = math.sin(frames * 0.9) * cell * 0.08
            dr, dc = arrow.direction.vector
            cx += dc * offset
            cy += dr * offset
            self.draw_arrow(screen, cx, cy, arrow.direction, cell, config.BLOCKED_COLOR)
        # 飞出动画中的箭头
        for f in flying:
            self.draw_arrow(screen, f.x, f.y, f.arrow.direction, cell, config.ARROW_COLOR)

    # ---------- 各界面 ----------
    def draw_start(self, screen):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "一箭又一箭", self.font_title, config.TEXT_COLOR, center=(cx, cy - 140))
        self.draw_text(screen, "点击箭头，让它飞出棋盘", self.font_medium, config.TEXT_COLOR, center=(cx, cy - 50))
        self.draw_text(screen, "前方有箭头阻挡时无法飞出，并消耗一次失误机会",
                       self.font_small, config.MUTED_COLOR, center=(cx, cy - 10))
        rect = self.start_button_rect()
        self.draw_button(screen, rect, "开始游戏", rect.collidepoint(pygame.mouse.get_pos()))

    def draw_playing(self, screen, game, flying, shake, blocked_timer):
        level = game.current_level
        board = game.board
        # 顶部信息栏
        pygame.draw.rect(screen, config.HUD_COLOR,
                         pygame.Rect(0, 0, config.WINDOW_WIDTH, config.HUD_HEIGHT))
        self.draw_text(screen, level.name, self.font_large, config.TEXT_COLOR, topleft=(24, 24))
        self.draw_text(screen, f"剩余箭头：{board.remaining}", self.font_medium, config.TEXT_COLOR, topleft=(24, 66))
        self.draw_text(screen, f"失误：{board.mistakes}/{board.max_mistakes}", self.font_medium,
                       config.BLOCKED_COLOR if board.mistakes > 0 else config.TEXT_COLOR, topleft=(230, 66))
        rect = self.restart_button_rect()
        self.draw_button(screen, rect, "重新开始", rect.collidepoint(pygame.mouse.get_pos()))
        # 棋盘与反馈
        self.draw_board(screen, game, flying, shake)
        if blocked_timer > 0:
            self.draw_text(screen, "被阻挡！", self.font_large, config.BLOCKED_COLOR,
                           center=(config.WINDOW_WIDTH // 2, config.HUD_HEIGHT + 15))

    def draw_level_clear(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "通关！", self.font_title, config.TEXT_COLOR, center=(cx, cy - 100))
        self.draw_text(screen, f"{game.current_level.name} 已完成", self.font_medium,
                       config.MUTED_COLOR, center=(cx, cy - 40))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "进入下一关", rect.collidepoint(pygame.mouse.get_pos()))

    def draw_all_clear(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "恭喜通关全部关卡！", self.font_title, config.TEXT_COLOR, center=(cx, cy - 100))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "再玩一次", rect.collidepoint(pygame.mouse.get_pos()))

    def draw_game_over(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "挑战失败", self.font_title, config.BLOCKED_COLOR, center=(cx, cy - 100))
        self.draw_text(screen, "失误次数已耗尽", self.font_medium, config.MUTED_COLOR, center=(cx, cy - 40))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "重新开始", rect.collidepoint(pygame.mouse.get_pos()))
