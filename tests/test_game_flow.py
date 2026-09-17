"""游戏流程状态机测试。"""
from game.models import Arrow, Direction, Level
from game.pathing import find_clear_order
from game.state import Game, State


def test_play_through_all_builtin_levels():
    """按求解器给出的顺序点击，应能打通全部关卡。"""
    game = Game()
    game.start()
    assert game.state is State.PLAYING
    while True:
        order = find_clear_order(game.current_level)
        assert order is not None, f"{game.current_level.name} 不可解"
        for arrow in order:
            assert game.click(arrow.row, arrow.col)[0] == "fly"
            game.after_fly()
        if game.state is State.ALL_CLEAR:
            break
        assert game.state is State.LEVEL_CLEAR
        game.next_level()
    assert game.level_index == len(game.levels) - 1


def test_game_over_on_mistakes():
    level = Level("测试关", 3, 3, [
        Arrow(0, 0, Direction.RIGHT),
        Arrow(0, 2, Direction.LEFT),  # 与 (0,0) 互相阻挡
    ], max_mistakes=2)
    game = Game([level])
    game.start()
    for _ in range(2):
        assert game.click(0, 0)[0] == "blocked"
        game.after_blocked()
    assert game.state is State.GAME_OVER


def test_restart_resets_board():
    game = Game()
    game.start()
    assert game.board.remaining == 3
    game.click(0, 0)   # 第 1 关 (0,0)→ 可飞出
    game.after_fly()
    assert game.board.remaining == 2
    game.restart()
    assert game.board.remaining == 3
    assert game.board.mistakes == 0
    assert game.state is State.PLAYING
