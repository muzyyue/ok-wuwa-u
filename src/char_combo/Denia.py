"""
爱达千 17s 合轴 — 达妮娅 (Denia)

达妮娅在轴中的职责:
   步骤 3:  e q r a1           (eqr间隔~0.1s,太快会吞小技能)
   步骤 6:  a2 a3
   步骤 8:  a4                 (爪子出现时切,之后换爱弥斯机甲形态)
   步骤 11: a1 a2 E
   步骤 13: a4 e               (机兵echo辅助中)
   步骤 14: E
   步骤 17: r
"""
from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'denia'


class Denia(BaseChar):
    """达妮娅 17s 合轴版 — 支持黑暗形态状态跟踪与合轴优化。

    合轴要点:
      - 常规形态: 4A + 2A + 2E → 黑暗形态（step 3/6/8）
      - 黑暗形态: 每个动作后摇都是合轴窗口（step 11/14/17）
      - 普攻「爪子」出现时 → 切人信号（step 8: a4）
      - 两次小技能后进入黑暗形态，之后 E 为强化技能
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resonance_count = 0  # 本轮上场共鸣次数，≥2 进黑暗形态

    def do_perform(self):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            rotation.reset()  # 循环轴: 从头开始,避免fallback

        step = rotation.current_step
        if not step:
            return self.switch_next_char()
        if step[0] != _CHAR_KEY:
            return self.switch_next_char()

        # === 执行本步骤动作 ===
        for action in step[1]:
            self._exec_action(action)

        rotation.advance()

        next_step = rotation.current_step
        next_is_intro = next_step and next_step[3] == RotationStepFlag.INTRO_SWITCH

        if next_is_intro:
            self.switch_next_char(free_intro=True)
        else:
            self.switch_next_char()

    def _exec_action(self, action):
        kind = action[0]

        if kind == 'e':   # 共鸣技能，0.1s间隔防吞
            self.click_resonance(time_out=0.5)
            self.sleep(0.1)
            self._resonance_count += 1  # 记录进入黑暗形态的进度

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招
            self.click_liberation()

        elif kind == 'a':  # 普攻N段
            count = action[1]
            for _ in range(count):
                self.normal_attack()
                self.sleep(0.07)

        elif kind == 'E':  # 强化小技能（黑暗形态下）
            self.click_resonance(time_out=0.5)
            self.sleep(0.15)

    def _do_fallback(self):
        """旋转完成后或无旋转时的后备动作（匹配原版 Denia 优化逻辑）。

        常规形态: 4A + 2A + 2E → 黑暗形态 → 全动作合轴切人。
        """
        if self.has_intro:
            self.wait_intro(1.2)
        self.continues_normal_attack(1.5)
        self.normal_attack()
        self.normal_attack()
        for _ in range(2):
            if self.resonance_available():
                self.click_resonance(time_out=0.5)
                self.sleep(0.1)
        self.click_liberation()
        self.click_echo(time_out=0)
        self.switch_next_char()

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            return super().get_switch_priority(current_char, has_intro, target_low_con)
        step = rotation.current_step
        if step and step[0] == _CHAR_KEY:
            return SwitchPriority.MUST
        # 黑暗形态下 (2+次共鸣后) 切人合轴收益高，但由步骤控制
        return SwitchPriority.NO
