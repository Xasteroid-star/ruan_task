"""棋盘运行时状态：箭头布局、点击处理、消除与失误判定、撤销历史。"""
from __future__ import annotations

from . import pathing
from .models import Arrow, Level


class Board:
    """一局游戏中的棋盘状态（对应单个关卡）。"""

    def __init__(self, level: Level):
        self.level = level
        self.rows = level.rows
        self.cols = level.cols
        # 剩余箭头：位置 -> 箭头
        self.arrows = {a.pos: a for a in level.arrows}
        self.max_mistakes = level.max_mistakes
        self.mistakes = 0
        # 移动历史，供「撤销」使用：("fly" | "blocked", Arrow)
        self.history: list[tuple[str, Arrow]] = []
        # 最近一次点击结果，供渲染层做动画 / 反馈
        self.last_fly = None       # 成功飞出的 Arrow
        self.last_blocked = None   # 被阻挡的 Arrow

    @property
    def remaining(self) -> int:
        return len(self.arrows)

    @property
    def is_cleared(self) -> bool:
        return not self.arrows

    @property
    def is_failed(self) -> bool:
        return self.mistakes >= self.max_mistakes

    def arrow_at(self, row: int, col: int) -> Arrow | None:
        return self.arrows.get((row, col))

    def click(self, row: int, col: int):
        """处理一次点击。返回 ("fly", Arrow) / ("blocked", Arrow) / None（点击空白）。"""
        self.last_fly = None
        self.last_blocked = None
        arrow = self.arrows.get((row, col))
        if arrow is None:
            return None
        remaining = set(self.arrows.keys())
        if pathing.can_fly(arrow, remaining, self.rows, self.cols):
            del self.arrows[(row, col)]
            self.history.append(("fly", arrow))
            self.last_fly = arrow
            return "fly", arrow
        self.mistakes += 1
        self.history.append(("blocked", arrow))
        self.last_blocked = arrow
        return "blocked", arrow

    def undo(self):
        """撤销上一步：恢复被消除的箭头，或返还一次失误。

        返回被撤销的 ("kind", Arrow)；无历史可撤销时返回 None。
        """
        if not self.history:
            return None
        kind, arrow = self.history.pop()
        if kind == "fly":
            self.arrows[arrow.pos] = arrow
        else:
            self.mistakes = max(0, self.mistakes - 1)
        return kind, arrow

    def hint(self) -> Arrow | None:
        """返回任意一个当前可安全飞出的箭头（不改变状态）。"""
        return pathing.find_flyable(list(self.arrows.values()), self.rows, self.cols)

    def solve(self) -> list[Arrow] | None:
        """返回能清空当前剩余箭头的完整顺序（供 AI 自动求解）。"""
        return pathing.solve(list(self.arrows.values()), self.rows, self.cols)
