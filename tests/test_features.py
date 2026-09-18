"""附加功能测试：撤销、提示、求解、计分与存档。"""
from game import pathing
from game.board import Board
from game.levels import LEVELS
from game.state import Game, State, score_for, stars_for


def test_undo_fly_restores_arrow():
    board = Board(LEVELS[0])  # 第 1 关 (0,0)→ 可飞出
    board.click(0, 0)
    assert board.arrow_at(0, 0) is None
    kind, arrow = board.undo()
    assert kind == "fly"
    assert board.arrow_at(0, 0) is not None


def test_undo_blocked_restores_mistake():
    board = Board(LEVELS[1])  # 第 2 关 (0,0)→ 被阻挡
    board.click(0, 0)
    assert board.mistakes == 1
    kind, _ = board.undo()
    assert kind == "blocked"
    assert board.mistakes == 0


def test_undo_empty_returns_none():
    board = Board(LEVELS[0])
    assert board.undo() is None


def test_hint_returns_flyable_arrow():
    board = Board(LEVELS[2])
    arrow = board.hint()
    assert arrow is not None
    remaining = set(board.arrows.keys())
    assert pathing.can_fly(arrow, remaining, board.rows, board.cols)


def test_solve_returns_full_order():
    board = Board(LEVELS[3])
    order = board.solve()
    assert order is not None
    assert len(order) == board.remaining


def test_stars_and_score():
    assert stars_for(0) == 3
    assert stars_for(1) == 2
    assert stars_for(2) == 1
    # 失误越少、用时越短，得分越高
    assert score_for(0, 10) > score_for(1, 10)
    assert score_for(0, 10) > score_for(0, 1000)


def test_score_accumulates_and_results_recorded():
    game = Game()
    game.start()
    for a in list(LEVELS[0].arrows):
        game.click(a.row, a.col)
        game.after_fly()
    assert game.state is State.LEVEL_CLEAR
    assert game.score > 0
    assert game.last_result["stars"] == 3  # 第 1 关 0 失误


def test_to_dict_load_dict_roundtrip():
    game = Game()
    game.start()
    game.click(0, 0)   # 第 1 关 (0,0)→ 可飞出
    game.after_fly()
    data = game.to_dict()
    game2 = Game()
    game2.load_dict(data)
    assert game2.state is State.PLAYING
    assert game2.board.remaining == game.board.remaining
    assert game2.board.mistakes == game.board.mistakes
    assert game2.score == game.score


def test_save_file_roundtrip(tmp_path, monkeypatch):
    import game.save as save_mod
    monkeypatch.setattr(save_mod, "SAVE_PATH", str(tmp_path / "save.json"))
    game = Game()
    game.start()
    game.click(0, 0)
    game.after_fly()
    save_mod.save_game(game)
    assert save_mod.save_exists()
    game2 = save_mod.load_game()
    assert game2.board.remaining == game.board.remaining
    assert game2.score == game.score
