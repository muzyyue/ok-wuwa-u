"""
爱达千 25s 合轴 — 达妮娅 (Denia)

达妮娅在轴中的职责:
    步骤 3:  r a1 a2            (首次出场: 大+普攻2段)
   步骤 6:  a3 a4              (普攻3+4段)
   步骤 11: E                  (暗形态强化E)
    步骤 13: E                  (暗形态强化E)
   步骤 16: a1 a2 r e          (变奏入场后普攻2段+大+E补协奏)
   步骤 18: a1 a2 a3 a4        (满段普攻收尾, a4可选)
"""
from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'denia'


class Denia(BaseChar):
    """达妮娅 25s 合轴版 — 暗形态爆发 + 协奏补位。

    合轴要点:
      - 首次出场: E → 大 → 普攻2段快速叠协奏 (step 3)
      - 暗形态强化: E2 暗形态爆发 (step 11)
      - E3+平a自动释放 (step 13)
      - 协奏补位: a1 a2 → 大 → E补满协奏 (step 16)
      - 满段收尾: a1 a2 a3 a4 循环末端 (step 18)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resonance_count = 0  # 本轮上场共鸣次数，≥2 进黑暗形态

    def do_perform(self):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            self.logger.info(f'[combo] {_CHAR_KEY} rotation done (idx={rotation.step_index}) → reset')
            rotation.reset()
        idx = rotation.step_index

        step = rotation.current_step
        if not step:
            self.logger.info(f'[combo] {_CHAR_KEY} step is None → switch')
            return self.switch_next_char()
        if step[0] != _CHAR_KEY:
            self.logger.info(f'[combo] {_CHAR_KEY} step {idx} is for {step[0]} → switch')
            return self.switch_next_char()

        self.logger.info(f'[combo] {_CHAR_KEY} step {idx} enter: actions={step[1]} flag={step[3].name} next={step[2]}')

        # === 入场缓冲 ===
        if self.has_intro and (not step[1] or step[1][0][0] != 'intro'):
            self.logger.info(f'[combo] {_CHAR_KEY} has_intro=True → wait intro landing')
            self.wait_intro(0.4, click=True)
        elif not self.has_intro:
            self.logger.info(f'[combo] {_CHAR_KEY} normal switch → settle 0.12s')
            self.sleep(0.12)

        # === 执行本步骤动作 ===
        for action in step[1]:
            self._exec_action(action)

        rotation.advance()

        next_step = rotation.current_step
        next_is_intro = next_step and next_step[3] == RotationStepFlag.INTRO_SWITCH
        next_char = next_step[0] if next_step else None

        self.logger.info(f'[combo] {_CHAR_KEY} step {idx} done → advance to {rotation.step_index}, switch to {next_char} (free_intro={next_is_intro})')

        if next_is_intro:
            self.switch_next_char(free_intro=True)
        else:
            self.switch_next_char()

    def _exec_action(self, action):
        kind = action[0]
        self.logger.info(f'[combo]  {_CHAR_KEY} exec {action}')

        if kind == 'e':   # 共鸣技能，0.1s间隔防吞
            self.click_resonance(time_out=0.5)
            self.sleep(0.1)
            self._resonance_count += 1  # 记录进入黑暗形态的进度

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招（click_liberation 自带时停记录）
            self.click_liberation()

        elif kind == 'a':  # 第N段普攻（a2 = 一段平a打出第二下,只按1次）
            self.normal_attack()
            self.sleep(0.07)

        elif kind == 'intro':  # 变奏入场
            self.wait_intro(0.8)

        elif kind == 'E':  # 强化小技能（黑暗形态下）
            self.click_resonance(time_out=0.5)
            self.sleep(0.15)
            self._resonance_count += 1

    def _do_fallback(self):
        """旋转完成后或无旋转时的后备动作（匹配原版 Denia 优化逻辑）。

        常规形态: 4A + 2A + 2E → 黑暗形态 → 全动作合轴切人。
        """
        self.logger.info(f'[combo] {_CHAR_KEY} fallback — rotation done or no matching step')
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
