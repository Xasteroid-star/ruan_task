"""游戏状态机与整体流程控制。"""
from __future__ import annotations

from enum import Enum, auto

from . import config
from . import levels as level_data
from .board import Board
from .models import Arrow, Direction


class State(Enum):
    START = auto()        # 开始界面
    PLAYING = auto()      # 游戏中
    LEVEL_CLEAR = auto()  # 本关通关
    ALL_CLEAR = auto()    # 全部关卡通关
    GAME_OVER = auto()    # 失误耗尽失败


def stars_for(mistakes: int) -> int:
    """根据失误次数折算星级：0 失误 3 星，1 失误 2 星，其余 1 星。"""
    if mistakes == 0:
        return 3
    if mistakes == 1:
        return 2
    return 1


def score_for(mistakes: int, elapsed: float) -> int:
    """计算单关得分：基础分 + 快速通关奖励 - 失误扣分。"""
    time_bonus = max(0, round(config.TIME_BONUS_CAP - elapsed))
    return max(config.MIN_LEVEL_SCORE,
               config.BASE_SCORE + time_bonus - mistakes * config.MISTAKE_PENALTY)


class Game:
    """整体游戏流程：关卡推进、失误、重开、计时、计分与存档。

    状态迁移时机由渲染层控制（等动画 / 反馈结束后再调用 after_fly / after_blocked），
    这样飞出与碰撞动画能完整播放后再切换界面。
    """

    def __init__(self, levels=None):
        self.levels = levels if levels is not None else level_data.LEVELS
        self.state = State.START
        self.level_index = 0
        self.board = Board(self.levels[0])
        # 附加功能状态
        self.elapsed = 0.0            # 当前关卡累计秒数
        self.score = 0                # 累计总分
        self.level_results: list[dict] = []  # 每关 {stars, score, time, mistakes}

    @property
    def current_level(self):
        return self.levels[self.level_index]

    # ---------- 流程 ----------
    def start(self):
        """从开始界面进入第 1 关（全新一局）。"""
        self.level_index = 0
        self.score = 0
        self.level_results = []
        self.elapsed = 0.0
        self._reset_board()
        self.state = State.PLAYING

    def restart(self):
        """重新开始当前关卡，恢复到初始状态（保留已通关卡的累计得分）。"""
        self.elapsed = 0.0
        self._reset_board()
        self.state = State.PLAYING

    def _reset_board(self):
        self.board = Board(self.current_level)

    def tick(self, dt: float):
        """由主循环每帧调用，累计当前关卡用时（秒）。"""
        if self.state is State.PLAYING:
            self.elapsed += dt

    def click(self, row: int, col: int):
        """处理一次棋盘点击，仅在 PLAYING 状态下生效。"""
        if self.state is not State.PLAYING:
            return None
        return self.board.click(row, col)

    def undo(self):
        """撤销上一步（仅在 PLAYING 下生效）。"""
        if self.state is not State.PLAYING:
            return None
        return self.board.undo()

    def hint(self):
        """返回一个可安全飞出的箭头。"""
        return self.board.hint()

    def solve(self):
        """返回能清空当前剩余箭头的顺序。"""
        return self.board.solve()

    # ---------- 动画结束后的状态迁移 ----------
    def after_fly(self):
        """飞出动画结束后调用：判断是否通关，并结算本关得分。"""
        if self.board.is_cleared:
            self._finish_level()
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
        self.elapsed = 0.0
        self._reset_board()
        self.state = State.PLAYING

    def _finish_level(self):
        """结算当前关卡：星级、单关得分并入累计总分。"""
        stars = stars_for(self.board.mistakes)
        level_score = score_for(self.board.mistakes, self.elapsed)
        self.score += level_score
        self.level_results.append({
            "stars": stars,
            "score": level_score,
            "time": round(self.elapsed, 1),
            "mistakes": self.board.mistakes,
        })

    @property
    def last_result(self) -> dict | None:
        """最近一次通关的结果（用于通关/全部通关界面展示）。"""
        return self.level_results[-1] if self.level_results else None

    @property
    def total_stars(self) -> int:
        return sum(r["stars"] for r in self.level_results)

    # ---------- 存档 ----------
    def to_dict(self) -> dict:
        return {
            "version": 1,
            "level_index": self.level_index,
            "mistakes": self.board.mistakes,
            "arrows": [{"row": a.row, "col": a.col, "dir": a.direction.name}
                       for a in self.board.arrows.values()],
            "elapsed": round(self.elapsed, 1),
            "score": self.score,
            "level_results": self.level_results,
        }

    def load_dict(self, data: dict):
        """从存档字典恢复游戏状态（用于「继续游戏」）。"""
        self.level_index = min(int(data.get("level_index", 0)), len(self.levels) - 1)
        self.score = int(data.get("score", 0))
        self.elapsed = float(data.get("elapsed", 0.0))
        self.level_results = data.get("level_results", [])
        self.state = State.PLAYING
        self._reset_board()
        self.board.arrows = {}
        for a in data.get("arrows", []):
            arrow = Arrow(int(a["row"]), int(a["col"]), Direction[a["dir"]])
            self.board.arrows[arrow.pos] = arrow
        self.board.mistakes = max(0, min(int(data.get("mistakes", 0)), self.board.max_mistakes))
