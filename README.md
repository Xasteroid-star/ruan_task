# 一箭又一箭

一款使用 Python + Pygame 开发的点击式箭头解谜小游戏。

## 游戏简介

棋盘网格中放置了朝向上、下、左、右四种方向的箭头。点击某个箭头：

- 若它朝向前方到棋盘边界之间没有其他箭头阻挡，箭头会飞出棋盘并被消除；
- 若路径上存在其他箭头，则无法消除，并产生碰撞反馈（抖动、变红、文字提示），同时消耗一次失误机会。

清空当前关卡全部箭头即可进入下一关；失误次数耗尽则本关失败，可重新开始。本作内置 4 个难度递增、均可通关的关卡。

## 开发环境

- Python 3.8+
- Pygame 2.x

## 安装和运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行游戏
python main.py
```

## 游戏操作说明

- 鼠标左键点击箭头：尝试让它飞出棋盘；
- 点击被阻挡的箭头会消耗失误机会，注意观察箭头方向与阻挡关系；
- 点击右上角「重新开始」按钮：当前关卡恢复初始状态；
- 清空本关后点击「进入下一关」，失败后点击「重新开始」。

## 游戏截图

### 开始界面

![开始界面](screenshots/1_start.png)

### 游戏界面

![游戏界面](screenshots/2_playing.png)

### 碰撞反馈

![碰撞反馈](screenshots/3_blocked.png)

### 箭头飞出

![箭头飞出](screenshots/4_flying.png)

### 通关界面

![通关界面](screenshots/5_level_clear.png)

### 失败界面

![失败界面](screenshots/6_game_over.png)

## 测试

```bash
python -m pytest tests/ -v
```

## 目录结构

```
task2/
├── main.py           # 入口与主循环
├── game/             # 游戏逻辑（models/pathing/board/levels/state）与渲染（renderer/config）
├── tests/            # 单元测试
├── tools/            # 截图生成等辅助脚本
├── screenshots/      # 游戏截图
└── requirements.txt
```

## 开发说明

本项目借助 AIGC 工具（Claude Code）辅助开发。核心路径检测算法与关卡数据为无 pygame 依赖的纯逻辑实现，可通过单元测试验证；图形界面与动画由 Pygame 完成。
