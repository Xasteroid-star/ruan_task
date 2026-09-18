"""程序化合成音效，无外部素材依赖（不引入版权问题，也不新增第三方库）。

使用标准库 array 生成 16-bit 单声道 PCM 波形，再交给 pygame.mixer 播放。
音频设备不可用时会静默降级为无音效，不影响游戏运行。
"""
from __future__ import annotations

import array
import math

import pygame

SAMPLE_RATE = 44100


def pre_init():
    """必须在 pygame.init() 之前调用，指定混音器为 16-bit 单声道。"""
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
    except pygame.error:
        pass


def _samples(freq_start: float, freq_end: float, duration: float,
             volume: float = 0.5, wave: str = "sine") -> array.array:
    """生成一段带淡入淡出包络的音波（频率在区间内线性扫过）。"""
    n = int(SAMPLE_RATE * duration)
    buf = array.array("h")
    attack = max(1, int(SAMPLE_RATE * 0.004))  # 4ms 起音，避免爆音
    for i in range(n):
        t = i / SAMPLE_RATE
        p = i / n
        freq = freq_start + (freq_end - freq_start) * p
        if wave == "square":
            v = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
        else:
            v = math.sin(2 * math.pi * freq * t)
        env = min(1.0, i / attack) * (1.0 - p)  # 线性衰减
        buf.append(int(v * volume * env * 32767))
    return buf


class SoundManager:
    """构建并播放各类音效；未初始化成功时所有 play 为空操作。"""

    def __init__(self):
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        if self.enabled:
            self._build()

    def _add(self, name, samples):
        try:
            self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())
        except pygame.error:
            pass

    def _build(self):
        # 飞出：短促上扬
        self._add("fly", _samples(500, 1400, 0.13, 0.4))
        # 碰撞：低沉下坠
        self._add("blocked", _samples(150, 80, 0.18, 0.55, "square"))
        # 提示：清脆短音
        self._add("hint", _samples(1000, 1000, 0.07, 0.3))
        # 通关：上扬长音
        self._add("clear", _samples(400, 900, 0.35, 0.45))
        # 失败：下坠长音
        self._add("fail", _samples(350, 120, 0.45, 0.5, "square"))

    def play(self, name: str):
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass
