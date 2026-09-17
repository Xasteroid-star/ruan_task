"""数据模型：方向、箭头、关卡。均为纯数据，无 pygame 依赖。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    """箭头朝向，其值为行进方向向量 (dr, dc)。"""

    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

    @property
    def vector(self) -> tuple[int, int]:
        return self.value


@dataclass(frozen=True)
class Arrow:
    """棋盘上的一个箭头：网格坐标 (row, col) + 朝向。"""

    row: int
    col: int
    direction: Direction

    @property
    def pos(self) -> tuple[int, int]:
        return (self.row, self.col)


@dataclass
class Level:
    """一个关卡：网格尺寸、箭头列表、允许失误次数。"""

    name: str
    rows: int
    cols: int
    arrows: list[Arrow]
    max_mistakes: int = 3
