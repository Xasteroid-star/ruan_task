"""关卡数据校验与可解性测试。"""
from game import levels
from game.pathing import find_clear_order


def test_at_least_three_levels():
    assert len(levels.LEVELS) >= 3


def test_levels_solvable():
    for level in levels.LEVELS:
        order = find_clear_order(level)
        assert order is not None, f"{level.name} 不可解"
        assert len(order) == len(level.arrows)


def test_arrows_within_board_and_unique():
    for level in levels.LEVELS:
        positions = [(a.row, a.col) for a in level.arrows]
        assert len(positions) == len(set(positions)), f"{level.name} 存在重复位置"
        for r, c in positions:
            assert 0 <= r < level.rows and 0 <= c < level.cols, f"{level.name} 箭头越界 ({r},{c})"


def test_max_mistakes_positive():
    for level in levels.LEVELS:
        assert level.max_mistakes > 0
