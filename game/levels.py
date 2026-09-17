"""关卡数据：4 个难度递增、均可通关的关卡。"""
from __future__ import annotations

from .models import Arrow, Direction, Level

UP = Direction.UP
DOWN = Direction.DOWN
LEFT = Direction.LEFT
RIGHT = Direction.RIGHT

LEVELS = [
    # 第 1 关：教学关，所有箭头都无阻挡，任意顺序可清。
    Level("第 1 关", 3, 3, [
        Arrow(0, 0, RIGHT),
        Arrow(1, 1, UP),
        Arrow(2, 2, LEFT),
    ], max_mistakes=2),

    # 第 2 关：引入简单阻挡关系，需按 (0,2) → (0,0) → (3,0) → (3,2) 的顺序。
    Level("第 2 关", 4, 4, [
        Arrow(0, 0, RIGHT),
        Arrow(0, 2, DOWN),
        Arrow(3, 2, LEFT),
        Arrow(3, 0, UP),
    ], max_mistakes=3),

    # 第 3 关：多方向交错，含一条依赖链 + 两个自由箭头。
    Level("第 3 关", 5, 5, [
        Arrow(0, 0, RIGHT),
        Arrow(0, 3, DOWN),
        Arrow(3, 3, LEFT),
        Arrow(3, 0, DOWN),
        Arrow(2, 1, UP),
        Arrow(4, 4, LEFT),
    ], max_mistakes=3),

    # 第 4 关：两条依赖链相互衔接，需规划完整顺序。
    Level("第 4 关", 5, 5, [
        Arrow(0, 0, RIGHT),
        Arrow(0, 4, DOWN),
        Arrow(4, 4, LEFT),
        Arrow(1, 1, RIGHT),
        Arrow(1, 3, DOWN),
        Arrow(3, 3, LEFT),
        Arrow(3, 0, UP),
    ], max_mistakes=3),
]
