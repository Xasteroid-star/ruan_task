"""生成 README 所需截图（使用虚拟显示驱动，无需真实窗口）。

用法：在项目根目录执行
    python tools/screenshots.py
输出到 screenshots/ 目录。
"""
import os
import sys

# 确保无论从哪个目录运行都能 import 项目根目录下的 game / main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from game.models import Arrow, Direction  # noqa: E402
from game.renderer import board_geometry, cell_center  # noqa: E402
from game.state import State  # noqa: E402
from main import App, Flying  # noqa: E402

OUT = "screenshots"


def save(app, name):
    app.draw()
    pygame.image.save(app.screen, os.path.join(OUT, f"{name}.png"))
    print(f"已生成 {OUT}/{name}.png")


def main():
    os.makedirs(OUT, exist_ok=True)
    app = App()

    # 1. 开始界面
    save(app, "1_start")

    # 2. 游戏界面（第 1 关）
    app.game.start()
    save(app, "2_playing")

    # 3. 碰撞反馈：手动构造抖动 + 红色提示
    app.shake[(0, 0)] = 16
    app.blocked_timer = 40
    app.draw()
    pygame.image.save(app.screen, os.path.join(OUT, "3_blocked.png"))
    print(f"已生成 {OUT}/3_blocked.png")
    app.shake.clear()
    app.blocked_timer = 0

    # 4. 箭头飞出动画
    level = app.game.current_level
    ox, oy, cell = board_geometry(level.rows, level.cols)
    cx, cy = cell_center(ox, oy, 0, 0, cell)
    app.flying.append(Flying(Arrow(0, 0, Direction.RIGHT), cx, cy))
    app.draw()
    pygame.image.save(app.screen, os.path.join(OUT, "4_flying.png"))
    print(f"已生成 {OUT}/4_flying.png")
    app.flying.clear()

    # 5. 通关界面
    app.game.state = State.LEVEL_CLEAR
    save(app, "5_level_clear")

    # 6. 失败界面
    app.game.state = State.GAME_OVER
    save(app, "6_game_over")

    pygame.quit()
    print("全部截图生成完毕")


if __name__ == "__main__":
    main()
