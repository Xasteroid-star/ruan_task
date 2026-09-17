"""路径检测单元测试。"""
from game.models import Arrow, Direction
from game.pathing import can_fly, cells_in_front

UP = Direction.UP
DOWN = Direction.DOWN
LEFT = Direction.LEFT
RIGHT = Direction.RIGHT


def test_cells_in_front_right():
    assert cells_in_front(Arrow(0, 0, RIGHT), 3, 3) == [(0, 1), (0, 2)]


def test_cells_in_front_up():
    assert cells_in_front(Arrow(2, 1, UP), 3, 3) == [(1, 1), (0, 1)]


def test_can_fly_no_blocker():
    remaining = {(2, 2)}
    assert can_fly(Arrow(0, 0, RIGHT), remaining, 3, 3) is True


def test_can_fly_blocked_right():
    remaining = {(0, 2)}
    assert can_fly(Arrow(0, 0, RIGHT), remaining, 3, 3) is False


def test_can_fly_blocked_up():
    remaining = {(0, 0)}
    assert can_fly(Arrow(2, 0, UP), remaining, 3, 3) is False


def test_can_fly_at_edge():
    # 贴边且朝外，前进路径为空 → 可飞出
    assert can_fly(Arrow(0, 0, LEFT), set(), 3, 3) is True


def test_can_fly_center_all_directions():
    # 中心箭头朝四个方向，均无阻挡 → 都可飞出
    for d in (UP, DOWN, LEFT, RIGHT):
        assert can_fly(Arrow(1, 1, d), set(), 3, 3) is True


def test_requirement_example_blocked():
    # → · · ↑ · ：第一个箭头朝右，但右侧有 ↑，不能飞出
    remaining = {(0, 3)}
    assert can_fly(Arrow(0, 0, RIGHT), remaining, 1, 5) is False


def test_requirement_example_clear():
    # ↑ · · · → ：最后一个箭头朝右，右侧无箭头，可飞出
    remaining = {(0, 0)}
    assert can_fly(Arrow(0, 4, RIGHT), remaining, 1, 5) is True
