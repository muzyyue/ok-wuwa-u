"""达妮娅 - 角色自动战斗逻辑（合轴型，4次入场一轮）。

入场1:  E(0.1s) → Echo → R → A → E 入黑暗形态 → 合轴
入场2:  A2+A3 → 合轴
入场3:  E+R → 变奏爱弥斯
入场4:  R → 切人收尾
"""
import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Denia(BaseChar):
    """达妮娅的自动化战斗控制类。

    暖机:     E(0.1s) → Echo → R → A → E → 合轴
    阶段A-1: 变奏 → A2+A3 → 合轴
    阶段A-2: 变奏 → E+R → 变奏爱弥斯
    阶段B:   变奏 → R → 切人
    """

    def do_perform(self):
        # ── 变奏入场 ──────────────────────────────────────────
        if self.has_intro:
            self.wait_intro(1.2)
            self.sleep(0.15)
            if getattr(self, '_dark_form_until', 0) > time.time():
                phase = getattr(self, '_hezhou_phase', 0)
                if phase == 0:
                    # 阶段A-1: a2 + a3 → 合轴切人
                    self.normal_attack()
                    self.normal_attack()
                    self._hezhou_phase = 1
                    self.switch_next_char()
                    return
                elif phase == 1:
                    # 阶段A-2: e + r → 变奏爱弥斯
                    self.click_resonance(time_out=0.5)
                    if self.click_liberation():
                        self.f_break()
                    self._hezhou_phase = 2
                    self.switch_next_char()
                    return
                elif phase == 2:
                    # 阶段B: r → 切人收尾
                    self.click_liberation()
                    self.switch_next_char()
                    return

            # 黑暗形态已过期 → 走下面的暖机重入

        # ── 暖机（首次入场 或 变奏入场但无黑暗形态）─────────────
        # 普通形态: e(0.1s) → qr + a → 进入黑暗形态 → 合轴
        self.check_combat()
        self.sleep(0.05)
        self.click_resonance(time_out=0.5)
        self.sleep(0.05)
        self.click_echo(time_out=0)
        self.sleep(0.05)
        self.click_liberation()
        self.sleep(0.05)
        self.normal_attack()

        # 进入黑暗形态
        self._dark_form_until = time.time() + 3
        self._hezhou_phase = 0
        self.switch_next_char()             # 合轴切走

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        """达妮娅作为快速副C: 变奏入场时强制切回，平时正常轮换。"""
        if has_intro:
            return SwitchPriority.MUST
        return SwitchPriority.NORMAL
