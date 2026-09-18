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


def solve(arrows: list[Arrow], rows: int, cols: int) -> list[Arrow] | None:
    """返回一个能清空给定剩余箭头的顺序（Arrow 列表）；若不可解则返回 None。

    采用「剥洋葱」式贪心：只要存在路径畅通的箭头就消除它。消除箭头只会让
    更多箭头变得可消除，因此贪心正确——能找到顺序当且仅当关卡可解。
    """
    remaining = list(arrows)
    remain_set = {a.pos for a in remaining}
    order = []
    while remaining:
        next_arrow = None
        for a in remaining:
            if can_fly(a, remain_set, rows, cols):
                next_arrow = a
                break
        if next_arrow is None:
            return None
        remaining.remove(next_arrow)
        remain_set.discard(next_arrow.pos)
        order.append(next_arrow)
    return order


def find_clear_order(level: Level) -> list[Arrow] | None:
    """返回一个能清空整关的点击顺序（兼容旧接口）。"""
    return solve(level.arrows, level.rows, level.cols)


def find_flyable(arrows: list[Arrow], rows: int, cols: int) -> Arrow | None:
    """返回当前剩余箭头中任意一个可安全飞出的箭头；无则返回 None（用于提示）。"""
    remain_set = {a.pos for a in arrows}
    for a in arrows:
        if can_fly(a, remain_set, rows, cols):
            return a
    return None


def is_solvable(level: Level) -> bool:
    """关卡是否存在合法的清空顺序。"""
    return find_clear_order(level) is not None
