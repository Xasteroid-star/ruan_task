"""游戏进度本地存档（JSON 文件，不涉及敏感信息）。"""
from __future__ import annotations

import json
import os

from .state import Game

# 存档位于项目根目录（game/ 的上一级），避免随包目录变化
SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "save.json")


def save_exists() -> bool:
    return os.path.exists(SAVE_PATH)


def save_game(game: Game):
    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(game.to_dict(), f, ensure_ascii=False, indent=2)


def load_game() -> Game:
    """从存档恢复一局游戏。文件缺失 / 损坏时抛出异常，由调用方处理。"""
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    game = Game()
    game.load_dict(data)
    return game


def clear_save():
    if os.path.exists(SAVE_PATH):
        os.remove(SAVE_PATH)
