"""
爱达千 17s轴 — 针对爱达千优化的17秒循环连招。

特点:
  - 固定17秒循环轴，最大化输出窗口
  - 优先级：大招 → 共鸣技能 → 平A循环
  - 在循环窗口内自动切换入场/退场
  - 可通过 ComboTab 配置启停
"""
import time

from src.char.BaseChar import BaseChar


class Aideqian(BaseChar):
    """爱达千 17s轴 — 固定17秒循环连招，循环优先级: 大招 > 共鸣技能 > 平A。"""
    ROTATION_CYCLE = 17  # 17秒循环窗口
    LIBERATION_COOLDOWN = 22
    SKILL_COOLDOWN = 8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cycle_start = -1
        self.last_skill = -1

    def cycle_time(self):
        """当前循环内的经过时间。"""
        if self.cycle_start < 0:
            return 0
        return time.time() - self.cycle_start

    def cycle_remaining(self):
        """当前循环剩余时间。"""
        return max(0, self.ROTATION_CYCLE - self.cycle_time())

    def countdown(self):
        if self.is_current_resonance_available():
            self.add_sequence(lambda: self.switch_next_char())
        elif self.is_liberation_available() and self.cycle_time() < self.ROTATION_CYCLE * 0.7:
            self.add_sequence(lambda: self.switch_next_char())
