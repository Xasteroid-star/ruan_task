"""入口：初始化 pygame，主循环，处理输入与动画。"""
from __future__ import annotations

import json
import sys

import pygame

from game import audio, config, save
from game.renderer import Renderer, board_geometry, cell_center
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
        audio.pre_init()
        pygame.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption("一箭又一箭")
        self.clock = pygame.time.Clock()
        self.renderer = Renderer()
        self.game = Game()
        self.audio = audio.SoundManager()
        # 动画 / 反馈状态
        self.flying = []           # list[Flying]
        self.shake = {}            # {(row, col): 剩余帧数}
        self.blocked_timer = 0     # "被阻挡" 文字剩余显示帧数
        self.pending_fly = False
        self.pending_blocked = False
        # 附加功能状态
        self.hint_pos = None       # 提示高亮的箭头位置 (row, col)
        self.ai_solution = []      # AI 自动求解剩余步骤
        self.ai_cooldown = 0.0     # AI 每步间隔（秒）
        self.toast_text = ""
        self.toast_timer = 0

    def run(self):
        while True:
            dt = self.clock.tick(config.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()

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
                save.clear_save()
                self._clear_effects()
                self._stop_ai()
            elif save.save_exists() and self.renderer.continue_button_rect().collidepoint(pos):
                self._continue()
        elif state == State.PLAYING:
            self._on_playing_click(pos)
        elif state == State.LEVEL_CLEAR:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.next_level()
                self._clear_effects()
        elif state == State.ALL_CLEAR:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.start()
                save.clear_save()
                self._clear_effects()
        elif state == State.GAME_OVER:
            if self.renderer.next_button_rect().collidepoint(pos):
                self.game.restart()
                self._clear_effects()

    def _on_playing_click(self, pos):
        rects = self.renderer.toolbar_button_rects()
        # 重新开始与保存随时可用（可中断 AI）
        if rects["restart"].collidepoint(pos):
            self._stop_ai()
            self.game.restart()
            self._clear_effects()
            return
        if rects["save"].collidepoint(pos):
            self._do_save()
            return
        # 动画或 AI 进行中，忽略其余操作
        if self.ai_solution or self.flying or self.shake:
            return
        if rects["undo"].collidepoint(pos):
            self._do_undo()
            return
        if rects["hint"].collidepoint(pos):
            self._do_hint()
            return
        if rects["ai"].collidepoint(pos):
            self._start_ai()
            return
        row, col = self.cell_at(pos)
        if row is None:
            return
        result = self.game.click(row, col)
        if result is None:
            return
        kind, arrow = result
        if kind == "fly":
            self._spawn_fly(arrow)
        else:
            self._spawn_blocked(arrow)

    def cell_at(self, pos):
        """像素坐标 -> 网格 (row, col)；点击在棋盘外返回 None。"""
        level = self.game.current_level
        ox, oy, cell = board_geometry(level.rows, level.cols)
        x, y = pos
        c = (x - ox) // cell
        r = (y - oy) // cell
        if 0 <= r < level.rows and 0 <= c < level.cols:
            return r, c
        return None

    # ---------- 动作 ----------
    def _spawn_fly(self, arrow):
        level = self.game.current_level
        ox, oy, cell = board_geometry(level.rows, level.cols)
        cx, cy = cell_center(ox, oy, arrow.row, arrow.col, cell)
        self.flying.append(Flying(arrow, cx, cy))
        self.pending_fly = True
        self.hint_pos = None
        self.audio.play("fly")

    def _spawn_blocked(self, arrow):
        self.shake[arrow.pos] = 16
        self.blocked_timer = 40
        self.pending_blocked = True
        self.audio.play("blocked")

    def _do_undo(self):
        if self.game.undo() is not None:
            self.hint_pos = None
            self.audio.play("hint")

    def _do_hint(self):
        arrow = self.game.hint()
        if arrow is not None:
            self.hint_pos = arrow.pos
            self.audio.play("hint")

    def _start_ai(self):
        order = self.game.solve()
        if order:
            self.ai_solution = list(order)
            self.ai_cooldown = 0.2
            self.hint_pos = None

    def _stop_ai(self):
        self.ai_solution = []

    def _do_save(self):
        try:
            save.save_game(self.game)
            self._toast("已保存进度")
            self.audio.play("hint")
        except OSError:
            self._toast("保存失败")

    def _continue(self):
        try:
            self.game = save.load_game()
            self._clear_effects()
            self._stop_ai()
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            self._toast("读取存档失败")

    def _toast(self, text):
        self.toast_text = text
        self.toast_timer = 90  # 约 1.5 秒

    # ---------- 更新 ----------
    def update(self, dt):
        self.game.tick(dt)
        for f in self.flying:
            f.update()
        self.flying = [f for f in self.flying if not f.done]
        if self.pending_fly and not self.flying:
            self.pending_fly = False
            self.game.after_fly()
            if self.game.state in (State.LEVEL_CLEAR, State.ALL_CLEAR):
                self.audio.play("clear")
        for pos in list(self.shake):
            self.shake[pos] -= 1
            if self.shake[pos] <= 0:
                del self.shake[pos]
        if self.pending_blocked and not self.shake:
            self.pending_blocked = False
            self.game.after_blocked()
            if self.game.state is State.GAME_OVER:
                self.audio.play("fail")
        if self.blocked_timer > 0:
            self.blocked_timer -= 1
        if self.toast_timer > 0:
            self.toast_timer -= 1
        self._update_ai(dt)

    def _update_ai(self, dt):
        if not self.ai_solution:
            return
        if self.flying or self.shake:
            return
        self.ai_cooldown -= dt
        if self.ai_cooldown > 0:
            return
        arrow = self.ai_solution.pop(0)
        result = self.game.click(arrow.row, arrow.col)
        if result is not None and result[0] == "fly":
            self._spawn_fly(arrow)
        self.ai_cooldown = 0.35

    def _clear_effects(self):
        self.flying.clear()
        self.shake.clear()
        self.blocked_timer = 0
        self.pending_fly = False
        self.pending_blocked = False
        self.hint_pos = None

    # ---------- 绘制 ----------
    def draw(self):
        self.renderer.draw_background(self.screen)
        state = self.game.state
        if state == State.START:
            self.renderer.draw_start(self.screen, save.save_exists())
        elif state == State.PLAYING:
            self.renderer.draw_playing(
                self.screen, self.game, self.flying, self.shake, self.blocked_timer,
                hint_pos=self.hint_pos,
                ai_active=bool(self.ai_solution),
                can_undo=bool(self.game.board.history)
                and not (self.flying or self.shake or self.ai_solution))
        elif state == State.LEVEL_CLEAR:
            self.renderer.draw_level_clear(self.screen, self.game)
        elif state == State.ALL_CLEAR:
            self.renderer.draw_all_clear(self.screen, self.game)
        elif state == State.GAME_OVER:
            self.renderer.draw_game_over(self.screen, self.game)
        if self.toast_timer > 0:
            self.renderer.draw_toast(self.screen, self.toast_text)
        pygame.display.flip()


if __name__ == "__main__":
    App().run()
