"""窗口与绘制相关常量。"""

# 窗口
WINDOW_WIDTH = 720
WINDOW_HEIGHT = 840
FPS = 60

# 布局
HUD_HEIGHT = 150      # 顶部信息栏高度
TOOLBAR_HEIGHT = 76   # 底部按钮工具栏高度
BOARD_TOP = 168       # 棋盘区域上边缘
BOARD_MARGIN = 24     # 棋盘区域四周留白
CELL_SIZE_MAX = 122   # 单格像素上限（随关卡行列自适应缩小）

# 颜色 (R, G, B) —— 浅色简洁风，参考微信小游戏《一箭又一箭》
BG_COLOR = (243, 240, 233)       # 背景底部（暖白）
BG_TOP_COLOR = (236, 242, 247)   # 背景顶部（浅蓝灰，冷→暖微渐变）
DOT_COLOR = (213, 209, 200)      # 背景点阵
DECO_ARROW = (150, 158, 180)     # 背景装饰箭头底色 (RGB)
DECO_ARROW_ALPHA = 26            # 装饰箭头透明度
HUD_COLOR = (255, 255, 255)      # 顶栏 / 底栏白底
TOOLBAR_COLOR = (255, 255, 255)
BOARD_COLOR = (255, 255, 255)    # 棋盘面板白底
CELL_COLOR = (250, 249, 245)     # 极浅格子
LINE_COLOR = (227, 224, 216)     # 浅灰网格线 / 分隔线
BOARD_BORDER = (214, 210, 200)   # 棋盘面板边框
BOARD_SHADOW = (222, 219, 210)   # 棋盘面板投影
TEXT_COLOR = (44, 46, 56)        # 深灰主文字
MUTED_COLOR = (150, 147, 138)    # 次级文字
ARROW_COLOR = (52, 54, 62)       # 近黑细线箭头
BLOCKED_COLOR = (231, 74, 76)    # 碰撞红
HOVER_CELL_COLOR = (233, 239, 252)  # 悬停格子浅蓝
BUTTON_COLOR = (88, 122, 220)
BUTTON_HOVER = (112, 142, 232)
BUTTON_TEXT = (255, 255, 255)
BUTTON_DISABLED = (206, 204, 198)

# 附加功能配色
GOLD = (208, 150, 40)
GREEN = (60, 168, 104)
STAR_COLOR = (240, 178, 48)
STAR_EMPTY = (220, 217, 209)
HINT_COLOR = (240, 178, 48)

# 计分
BASE_SCORE = 1000       # 每关基础分
TIME_BONUS_CAP = 300    # 快速通关最多奖励分
MISTAKE_PENALTY = 100   # 每次失误扣分
MIN_LEVEL_SCORE = 100   # 单关最低得分


def cell_size(rows: int, cols: int) -> int:
    """根据关卡行列自适应计算单格像素，使棋盘在窗口内居中且不被裁切。"""
    board_area_w = WINDOW_WIDTH - 2 * BOARD_MARGIN
    board_area_h = (WINDOW_HEIGHT - TOOLBAR_HEIGHT - BOARD_TOP) - 2 * BOARD_MARGIN
    return min(CELL_SIZE_MAX, board_area_w // cols, board_area_h // rows)
