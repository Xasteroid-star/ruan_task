"""游戏状态机与整体流程控制。"""
from __future__ import annotations

from enum import Enum, auto

from . import levels as level_data
from .board import Board


class State(Enum):
    START = auto()        # 开始界面
    PLAYING = auto()      # 游戏中
    LEVEL_CLEAR = auto()  # 本关通关
    ALL_CLEAR = auto()    # 全部关卡通关
    GAME_OVER = auto()    # 失误耗尽失败


class Game:
    """整体游戏流程：关卡推进、失误、重开。

    状态迁移时机由渲染层控制（等动画 / 反馈结束后再调用 after_fly / after_blocked），
    这样飞出与碰撞动画能完整播放后再切换界面。
    """

    def __init__(self, levels=None):
        self.levels = levels if levels is not None else level_data.LEVELS
        self.state = State.START
        self.level_index = 0
        self.board = Board(self.levels[0])

    @property
    def current_level(self):
        return self.levels[self.level_index]

    def start(self):
        """从开始界面进入第 1 关。"""
        self.level_index = 0
        self._reset_board()
        self.state = State.PLAYING

    def restart(self):
        """重新开始当前关卡，恢复到初始状态。"""
        self._reset_board()
        self.state = State.PLAYING

    def _reset_board(self):
        self.board = Board(self.current_level)

    def click(self, row: int, col: int):
        """处理一次棋盘点击，仅在 PLAYING 状态下生效。"""
        if self.state is not State.PLAYING:
            return None
        return self.board.click(row, col)

    def after_fly(self):
        """飞出动画结束后调用：判断是否通关。"""
        if self.board.is_cleared:
            if self.level_index + 1 < len(self.levels):
                self.state = State.LEVEL_CLEAR
            else:
                self.state = State.ALL_CLEAR

    def after_blocked(self):
        """碰撞反馈结束后调用：判断是否失误耗尽。"""
        if self.board.is_failed:
            self.state = State.GAME_OVER

    def next_level(self):
        """通关后进入下一关。"""
        self.level_index += 1
        self._reset_board()
        self.state = State.PLAYING
