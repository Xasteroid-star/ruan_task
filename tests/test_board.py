"""棋盘交互与失误判定测试。"""
from game.board import Board
from game.levels import LEVELS


def test_fly_removes_arrow():
    board = Board(LEVELS[0])  # 第 1 关 (0,0)→ 无阻挡
    kind, arrow = board.click(0, 0)
    assert kind == "fly"
    assert board.arrow_at(0, 0) is None
    assert board.mistakes == 0


def test_blocked_consumes_mistake():
    board = Board(LEVELS[1])  # 第 2 关 (0,0)→ 被 (0,2) 阻挡
    kind, arrow = board.click(0, 0)
    assert kind == "blocked"
    assert board.arrow_at(0, 0) is not None  # 未被消除
    assert board.mistakes == 1


def test_click_empty_returns_none():
    board = Board(LEVELS[0])
    assert board.click(0, 1) is None
    assert board.mistakes == 0


def test_fail_when_mistakes_exhausted():
    board = Board(LEVELS[1])  # max_mistakes = 3
    for _ in range(3):
        board.click(0, 0)  # 每次都被阻挡，消耗失误
    assert board.is_failed is True


def test_clear_when_all_removed():
    board = Board(LEVELS[0])
    for a in list(LEVELS[0].arrows):
        board.click(a.row, a.col)
    assert board.is_cleared is True
