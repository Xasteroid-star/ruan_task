"""pygame 绘制：棋盘、箭头、飞出 / 碰撞动画、HUD、工具栏与各界面。"""
from __future__ import annotations

import math
import os

import pygame

from . import config
from .models import Direction


def board_origin(rows: int, cols: int) -> tuple[int, int]:
    """返回棋盘左上角像素坐标（水平居中、在棋盘区域内垂直居中）。"""
    cell = config.cell_size(rows, cols)
    board_w = cols * cell
    board_h = rows * cell
    x = (config.WINDOW_WIDTH - board_w) // 2
    area_h = config.WINDOW_HEIGHT - config.TOOLBAR_HEIGHT - config.BOARD_TOP
    y = config.BOARD_TOP + (area_h - board_h) // 2
    return x, y


def board_geometry(rows: int, cols: int) -> tuple[int, int, int]:
    """返回 (棋盘左上 x, 棋盘左上 y, 单格像素)。"""
    cell = config.cell_size(rows, cols)
    ox, oy = board_origin(rows, cols)
    return ox, oy, cell


def cell_center(origin_x: int, origin_y: int, row: int, col: int, cell: int) -> tuple[int, int]:
    """返回格子中心的像素坐标。"""
    cx = origin_x + col * cell + cell // 2
    cy = origin_y + row * cell + cell // 2
    return cx, cy


def format_time(seconds: float) -> str:
    """把秒数格式化为 mm:ss。"""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def _load_font(size: int) -> pygame.font.Font:
    """加载支持中文的系统字体；失败则回退默认字体（仅 ASCII）。

    某些 Windows 环境上 pygame 的 match_font / SysFont 会因系统字体表中存在
    异常条目而抛 TypeError，因此这里直接用已知路径加载中文字体文件。
    """
    windir = os.environ.get("WINDIR", r"C:\Windows")
    for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "Deng.ttf", "msyh.ttf"):
        path = os.path.join(windir, "Fonts", name)
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except pygame.error:
                continue
    return pygame.font.Font(None, size)


class Renderer:
    """缓存字体，提供各界面绘制。"""

    # 底部工具栏按钮：(key, 文案, 宽度)
    TOOLBAR_ITEMS = [
        ("undo", "撤销", 88),
        ("hint", "提示", 88),
        ("ai", "AI 求解", 104),
        ("restart", "重新开始", 120),
        ("save", "保存", 88),
    ]

    def __init__(self):
        pygame.font.init()
        self.font_title = _load_font(48)
        self.font_large = _load_font(32)
        self.font_medium = _load_font(26)
        self.font_small = _load_font(20)
        self.bg = self._make_background()

    def _make_background(self) -> pygame.Surface:
        """预生成背景：冷→暖渐变 + 点阵纹理 + 大号箭头水印。"""
        w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        surf = pygame.Surface((w, h))
        top = config.BG_TOP_COLOR
        bottom = config.BG_COLOR
        for y in range(h):
            t = y / h
            color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
            pygame.draw.line(surf, color, (0, y), (w, y))
        # 点阵纹理（呼应原版「点阵」玩法）
        step = 26
        for gy in range(step // 2, h, step):
            for gx in range(step // 2, w, step):
                pygame.draw.circle(surf, config.DOT_COLOR, (gx, gy), 1)
        # 四角大号箭头水印（低透明度）
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        rgba = config.DECO_ARROW + (config.DECO_ARROW_ALPHA,)
        deco = [
            (120, 320, Direction.LEFT, 170),
            (w - 120, 300, Direction.RIGHT, 180),
            (130, h - 300, Direction.DOWN, 160),
            (w - 130, h - 320, Direction.UP, 160),
        ]
        for cx, cy, d, size in deco:
            self.draw_arrow(overlay, cx, cy, d, size, rgba)
        surf.blit(overlay, (0, 0))
        return surf

    def draw_background(self, screen):
        screen.blit(self.bg, (0, 0))

    # ---------- 通用 ----------
    def draw_text(self, screen, text, font, color, center=None, topleft=None, topright=None):
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center is not None:
            rect.center = center
        elif topleft is not None:
            rect.topleft = topleft
        elif topright is not None:
            rect.topright = topright
        screen.blit(surface, rect)

    def draw_button(self, screen, rect, text, hover=False, enabled=True):
        if not enabled:
            color = config.BUTTON_DISABLED
        else:
            color = config.BUTTON_HOVER if hover else config.BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=8)
        self.draw_text(screen, text, self.font_medium, config.BUTTON_TEXT, center=rect.center)

    def draw_stars(self, screen, cx, cy, stars, max_stars=3):
        """绘制星级评价（★ 与空星）。"""
        spacing = 58
        total = (max_stars - 1) * spacing
        x0 = cx - total // 2
        for i in range(max_stars):
            color = config.STAR_COLOR if i < stars else config.STAR_EMPTY
            self.draw_text(screen, "★", self.font_large, color, center=(x0 + i * spacing, cy))

    def _draw_banner(self, screen, text, color, y):
        """屏幕中部临时横幅提示（带半透明底）。"""
        surf = self.font_large.render(text, True, color)
        rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2, y))
        pad = pygame.Rect(rect.x - 20, rect.y - 8, rect.w + 40, rect.h + 16)
        overlay = pygame.Surface(pad.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, pad.topleft)
        screen.blit(surf, rect)

    def draw_toast(self, screen, text):
        """底部临时提示（如「已保存进度」）。"""
        surf = self.font_medium.render(text, True, (255, 255, 255))
        rect = surf.get_rect(center=(config.WINDOW_WIDTH // 2,
                                     config.WINDOW_HEIGHT - config.TOOLBAR_HEIGHT - 28))
        pad = rect.inflate(30, 14)
        overlay = pygame.Surface(pad.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, pad.topleft)
        screen.blit(surf, rect)

    # ---------- 按钮区域 ----------
    def start_button_rect(self):
        return pygame.Rect((config.WINDOW_WIDTH - 260) // 2,
                           config.WINDOW_HEIGHT // 2 + 70, 260, 60)

    def continue_button_rect(self):
        return pygame.Rect((config.WINDOW_WIDTH - 260) // 2,
                           config.WINDOW_HEIGHT // 2 + 148, 260, 60)

    def next_button_rect(self):
        return pygame.Rect((config.WINDOW_WIDTH - 260) // 2,
                           config.WINDOW_HEIGHT // 2 + 92, 260, 60)

    def toolbar_button_rects(self) -> dict[str, pygame.Rect]:
        """返回底部工具栏各按钮的矩形（key -> Rect）。"""
        y = config.WINDOW_HEIGHT - config.TOOLBAR_HEIGHT + 16
        h = 44
        gap = 10
        total = sum(w for _, _, w in self.TOOLBAR_ITEMS) + gap * (len(self.TOOLBAR_ITEMS) - 1)
        x = (config.WINDOW_WIDTH - total) // 2
        rects = {}
        for key, _, w in self.TOOLBAR_ITEMS:
            rects[key] = pygame.Rect(x, y, w, h)
            x += w + gap
        return rects

    def draw_toolbar(self, screen, rects, disabled=()):
        mouse = pygame.mouse.get_pos()
        for key, text, _ in self.TOOLBAR_ITEMS:
            rect = rects[key]
            if key in disabled:
                color = config.BUTTON_DISABLED
            else:
                color = config.BUTTON_HOVER if rect.collidepoint(mouse) else config.BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=8)
            self.draw_text(screen, text, self.font_small, config.BUTTON_TEXT, center=rect.center)

    # ---------- 箭头 ----------
    def draw_arrow(self, screen, cx, cy, direction, cell, color):
        """在 (cx, cy) 处画一个指向 direction 的箭头（细杆 + 三角头）。"""
        dr, dc = direction.vector
        half = cell * 0.34
        head = cell * 0.22
        tip = (cx + dc * half, cy + dr * half)
        tail = (cx - dc * half, cy - dr * half)
        px, py = -dr, dc  # 垂直于朝向的向量
        base = (tip[0] - dc * head, tip[1] - dr * head)
        p1 = (base[0] + px * head, base[1] + py * head)
        p2 = (base[0] - px * head, base[1] - py * head)
        pygame.draw.line(screen, color, tail, tip, max(2, int(cell * 0.055)))
        pygame.draw.polygon(screen, color, [tip, p1, p2])

    # ---------- 棋盘 ----------
    def _cell_at_mouse(self, ox, oy, cell, rows, cols):
        """返回鼠标当前悬停的网格 (row, col)；不在棋盘内返回 None。"""
        mx, my = pygame.mouse.get_pos()
        c = (mx - ox) // cell
        r = (my - oy) // cell
        if 0 <= r < rows and 0 <= c < cols:
            return r, c
        return None

    def draw_board(self, screen, game, flying, shake, hint_pos=None):
        level = game.current_level
        ox, oy, cell = board_geometry(level.rows, level.cols)
        pad = 12
        board_rect = pygame.Rect(ox - pad, oy - pad,
                                 level.cols * cell + pad * 2, level.rows * cell + pad * 2)
        # 面板：投影 + 白底 + 细边框
        pygame.draw.rect(screen, config.BOARD_SHADOW, board_rect.move(0, 3), border_radius=16)
        pygame.draw.rect(screen, config.BOARD_COLOR, board_rect, border_radius=16)
        pygame.draw.rect(screen, config.BOARD_BORDER, board_rect, 1, border_radius=16)
        hover_cell = self._cell_at_mouse(ox, oy, cell, level.rows, level.cols)
        for r in range(level.rows):
            for c in range(level.cols):
                rect = pygame.Rect(ox + c * cell, oy + r * cell, cell, cell)
                if (r, c) == hover_cell and (r, c) in game.board.arrows:
                    pygame.draw.rect(screen, config.HOVER_CELL_COLOR, rect, border_radius=6)
                else:
                    pygame.draw.rect(screen, config.CELL_COLOR, rect, border_radius=6)
                pygame.draw.rect(screen, config.LINE_COLOR, rect, 1, border_radius=6)
        # 提示高亮：呼吸式金色描边
        if hint_pos is not None:
            hr, hc = hint_pos
            rect = pygame.Rect(ox + hc * cell, oy + hr * cell, cell, cell)
            pulse = 3 + int(2 * (1 + math.sin(pygame.time.get_ticks() * 0.008)))
            pygame.draw.rect(screen, config.HINT_COLOR, rect.inflate(10, 10),
                             width=pulse, border_radius=10)
        # 正常箭头
        for pos, arrow in game.board.arrows.items():
            if pos in shake:
                continue
            cx, cy = cell_center(ox, oy, pos[0], pos[1], cell)
            self.draw_arrow(screen, cx, cy, arrow.direction, cell, config.ARROW_COLOR)
        # 被碰撞的箭头：抖动 + 变红
        for pos, frames in shake.items():
            arrow = game.board.arrow_at(*pos)
            if arrow is None:
                continue
            cx, cy = cell_center(ox, oy, pos[0], pos[1], cell)
            offset = math.sin(frames * 0.9) * cell * 0.08
            dr, dc = arrow.direction.vector
            cx += dc * offset
            cy += dr * offset
            self.draw_arrow(screen, cx, cy, arrow.direction, cell, config.BLOCKED_COLOR)
        # 飞出动画中的箭头
        for f in flying:
            self.draw_arrow(screen, f.x, f.y, f.arrow.direction, cell, config.ARROW_COLOR)

    # ---------- 各界面 ----------
    def draw_start(self, screen, has_save=False):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        # 装饰箭头
        for i, d in enumerate((Direction.UP, Direction.RIGHT, Direction.LEFT)):
            self.draw_arrow(screen, cx - 96 + i * 96, cy - 258, d, 64, config.ARROW_COLOR)
        self.draw_text(screen, "一箭又一箭", self.font_title, config.TEXT_COLOR, center=(cx, cy - 168))
        self.draw_text(screen, "点击箭头，让它飞出棋盘", self.font_medium,
                       config.TEXT_COLOR, center=(cx, cy - 104))
        self.draw_text(screen, "前方有箭头阻挡时无法飞出，并消耗一次失误机会",
                       self.font_small, config.MUTED_COLOR, center=(cx, cy - 62))
        mouse = pygame.mouse.get_pos()
        start_rect = self.start_button_rect()
        self.draw_button(screen, start_rect, "开始游戏", start_rect.collidepoint(mouse))
        if has_save:
            cont_rect = self.continue_button_rect()
            self.draw_button(screen, cont_rect, "继续游戏", cont_rect.collidepoint(mouse))

    def draw_playing(self, screen, game, flying, shake, blocked_timer,
                     hint_pos=None, ai_active=False, can_undo=True):
        level = game.current_level
        board = game.board
        w = config.WINDOW_WIDTH
        # 顶部信息栏
        pygame.draw.rect(screen, config.HUD_COLOR, pygame.Rect(0, 0, w, config.HUD_HEIGHT))
        pygame.draw.line(screen, config.LINE_COLOR,
                         (0, config.HUD_HEIGHT - 1), (w, config.HUD_HEIGHT - 1))
        self.draw_text(screen, level.name, self.font_large, config.TEXT_COLOR, topleft=(24, 18))
        self.draw_text(screen, f"剩余箭头：{board.remaining}", self.font_medium,
                       config.TEXT_COLOR, topleft=(24, 72))
        remaining_mistakes = max(0, board.max_mistakes - board.mistakes)
        mistake_color = config.BLOCKED_COLOR if remaining_mistakes == 0 else config.TEXT_COLOR
        self.draw_text(screen, f"剩余失误：{remaining_mistakes}/{board.max_mistakes}",
                       self.font_medium, mistake_color, topleft=(24, 108))
        # 右侧：得分 + 计时
        self.draw_text(screen, f"得分 {game.score}", self.font_medium,
                       config.GOLD, topright=(w - 24, 22))
        self.draw_text(screen, f"时间 {format_time(game.elapsed)}", self.font_medium,
                       config.TEXT_COLOR, topright=(w - 24, 72))
        # 底部工具栏
        bar_top = config.WINDOW_HEIGHT - config.TOOLBAR_HEIGHT
        pygame.draw.rect(screen, config.TOOLBAR_COLOR, pygame.Rect(0, bar_top, w, config.TOOLBAR_HEIGHT))
        pygame.draw.line(screen, config.LINE_COLOR, (0, bar_top), (w, bar_top))
        rects = self.toolbar_button_rects()
        disabled = tuple(k for k in ("undo",) if not can_undo)
        self.draw_toolbar(screen, rects, disabled)
        # 棋盘与反馈
        self.draw_board(screen, game, flying, shake, hint_pos)
        if ai_active:
            self._draw_banner(screen, "AI 求解中…", config.GOLD, config.HUD_HEIGHT + 26)
        elif blocked_timer > 0:
            self._draw_banner(screen, "被阻挡！", config.BLOCKED_COLOR, config.HUD_HEIGHT + 26)

    def draw_level_clear(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "通关！", self.font_title, config.GREEN, center=(cx, cy - 150))
        self.draw_text(screen, f"{game.current_level.name} 已完成", self.font_medium,
                       config.MUTED_COLOR, center=(cx, cy - 90))
        res = game.last_result
        if res:
            self.draw_stars(screen, cx, cy - 36, res["stars"])
            self.draw_text(
                screen,
                f"得分 +{res['score']}    用时 {format_time(res['time'])}    失误 {res['mistakes']}",
                self.font_medium, config.TEXT_COLOR, center=(cx, cy + 24))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "进入下一关", rect.collidepoint(pygame.mouse.get_pos()))

    def draw_all_clear(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "恭喜通关全部关卡！", self.font_title, config.GOLD, center=(cx, cy - 150))
        self.draw_text(screen, f"总分 {game.score}", self.font_large, config.TEXT_COLOR,
                       center=(cx, cy - 70))
        self.draw_text(screen, f"累计获得 {game.total_stars} 星", self.font_medium,
                       config.MUTED_COLOR, center=(cx, cy - 22))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "再玩一次", rect.collidepoint(pygame.mouse.get_pos()))

    def draw_game_over(self, screen, game):
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.draw_text(screen, "挑战失败", self.font_title, config.BLOCKED_COLOR, center=(cx, cy - 150))
        self.draw_text(screen, "失误次数已耗尽", self.font_medium, config.MUTED_COLOR,
                       center=(cx, cy - 90))
        self.draw_text(screen, f"还剩 {game.board.remaining} 个箭头", self.font_small,
                       config.MUTED_COLOR, center=(cx, cy - 50))
        rect = self.next_button_rect()
        self.draw_button(screen, rect, "重新开始", rect.collidepoint(pygame.mouse.get_pos()))
