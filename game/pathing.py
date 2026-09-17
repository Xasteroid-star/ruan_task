"""路径检测与关卡可解性求解。纯函数，无 pygame 依赖，便于单元测试。"""
from __future__ import annotations

from .models import Arrow, Level


def cells_in_front(arrow: Arrow, rows: int, cols: int) -> list[tuple[int, int]]:
    """返回箭头前进方向上、到棋盘边界之间的所有网格坐标（不含自身）。"""
    dr, dc = arrow.direction.vector
    cells = []
    r, c = arrow.row + dr, arrow.col + dc
    while 0 <= r < rows and 0 <= c < cols:
        cells.append((r, c))
        r += dr
        c += dc
    return cells


def can_fly(arrow: Arrow, remaining, rows: int, cols: int) -> bool:
    """判断箭头当前能否飞出棋盘：前进路径上没有其他箭头。

    remaining 为剩余箭头的坐标集合（(row, col)）。
    """
    return all(pos not in remaining for pos in cells_in_front(arrow, rows, cols))


def find_clear_order(level: Level) -> list[Arrow] | None:
    """返回一个能清空整关的点击顺序（Arrow 列表）；若不可解则返回 None。

    采用「剥洋葱」式贪心：只要存在路径畅通的箭头就消除它。消除箭头只会让
    更多箭头变得可消除，因此贪心正确——能找到顺序当且仅当关卡可解。
    """
    arrows = list(level.arrows)
    remaining = {a.pos for a in arrows}
    order = []
    while arrows:
        next_arrow = None
        for a in arrows:
            if can_fly(a, remaining, level.rows, level.cols):
                next_arrow = a
                break
        if next_arrow is None:
            return None
        arrows.remove(next_arrow)
        remaining.discard(next_arrow.pos)
        order.append(next_arrow)
    return order


def is_solvable(level: Level) -> bool:
    """关卡是否存在合法的清空顺序。"""
    return find_clear_order(level) is not None
