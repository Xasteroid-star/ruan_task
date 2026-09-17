"""入口：初始化 pygame，主循环，处理输入与动画。"""
from __future__ import annotations

import sys

import pygame

from game import config
from game.renderer import Renderer, board_origin, cell_center
from game.state import Game, State


class Flying:
    """一个正在飞出棋盘的箭头动画。"""

    SPEED = 22  # 每帧移动的像素

    def __init__(self, arrow, x, y):
        self.arrow = arrow
        self.x = float(x)
        self.y = float(y)
        dr, dc = arrow.direction.vector
        self.dx = dc * self.SPEED
        self.dy = dr * self.SPEED

    def update(self):
        self.x += self.dx
        self.y += self.dy

    @property
    def done(self) -> bool:
        return (self.x < -80 or self.x > config.WINDOW_WIDTH + 80
                or self.y < -80 or self.y > config.WINDOW_HEIGHT + 80)


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.game = Game()
        # 动画 / 反馈状态
        self.flying = []           # list[Flying]
        self.shake = {}            # {(row, col): 剩余帧数}
        self.blocked_timer = 0     # "被阻挡" 文字剩余显示帧数
        self.pending_fly = False
        self.pending_blocked = False

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(config.FPS)

    # ---------- 输入 ----------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.on_click(event.pos)

    def on_click(self, pos):
        state = self.game.state
        if state == State.START:
            if self.renderer.start_button_rect().collidepoint(pos):
                self.game.start()
                self._clear_effects()
        elif state == State.PLAYING:
            if self.renderer.restart_button_rect().collidepoint(pos):
                self.game.restart()
                self._clear_effects()
                return
            if self.flying or self.shake:
                return  # 动画进行中，忽略棋盘点击
            row, col = self.cell_at(pos)
            if row is None:
                return
            result = self.game.click(row, col)
            if result is None:
                return
            kind, arrow = result
            if kind == "fly":
                ox, oy = board_origin(self.game.current_level.cols)
                cx, cy = cell_center(ox, oy, arrow.row, arrow.col)
                self.flying.append(Flying(arrow, cx, cy))
                self.pending_fly = True
            else:
                self.shake[arrow.pos] = 16
                self.blocked_timer = 40
                self.pending_blocked = True
        elif state == State.LEVEL_CLEAR:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.next_level()
                self._clear_effects()
        elif state == State.ALL_CLEAR:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.start()
                self._clear_effects()
        elif state == State.GAME_OVER:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.restart()
                self._clear_effects()

    def cell_at(self, pos):
        """像素坐标 -> 网格 (row, col)；点击在棋盘外返回 None。"""
        level = self.game.current_level
        ox, oy = board_origin(level.cols)
        x, y = pos
        c = (x - ox) // config.CELL_SIZE
        r = (y - oy) // config.CELL_SIZE
        if 0 <= r < level.rows and 0 <= c < level.cols:
            return r, c
        return None

    # ---------- 更新 ----------
    def update(self):
        for f in self.flying:
            f.update()
        self.flying = [f for f in self.flying if not f.done]
        if self.pending_fly and not self.flying:
            self.pending_fly = False
            self.game.after_fly()
        for pos in list(self.shake):
            self.shake[pos] -= 1
            if self.shake[pos] <= 0:
                del self.shake[pos]
        if self.pending_blocked and not self.shake:
            self.pending_blocked = False
            self.game.after_blocked()
        if self.blocked_timer > 0:
            self.blocked_timer -= 1

    def _clear_effects(self):
        self.flying.clear()
        self.shake.clear()
        self.blocked_timer = 0
        self.pending_fly = False
        self.pending_blocked = False

    # ---------- 绘制 ----------
    def draw(self):
        self.screen.fill(config.BG_COLOR)
        state = self.game.state
        if state == State.START:
            self.renderer.draw_start(self.screen)
        elif state == State.PLAYING:
            self.renderer.draw_playing(self.screen, self.game, self.flying, self.shake, self.blocked_timer)
        elif state == State.LEVEL_CLEAR:
            self.renderer.draw_level_clear(self.screen, self.game)
        elif state == State.ALL_CLEAR:
            self.renderer.draw_all_clear(self.screen, self.game)
        elif state == State.GAME_OVER:
            self.renderer.draw_game_over(self.screen, self.game)
        pygame.display.flip()


if __name__ == "__main__":
    App().run()
