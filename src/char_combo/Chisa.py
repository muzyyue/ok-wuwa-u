"""
爱达千 25s 合轴 — 千咲 (Chisa)

千咲在轴中的职责:
   步骤 0:  jump_a e a3        (跳A+E+普攻3段)
   步骤 2:  a4                 (普攻4段)
   步骤 4:  a5                 (普攻5段)
   步骤 8:  q r e              (声骸+大招+E)
    步骤 10: a                  (普攻→切达妮娅)
   步骤 14: a                  (普攻→满协奏变奏爱)
"""
import time

from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'chisa'


class Chisa(BaseChar):
    """千咲 25s 合轴版 — 跳A入场 + 电锯形态 + 重击/声骸爆发。

    合轴要点:
      - 入场: 跳A+E+普攻3段快速暖机 (step 0)
      - 电锯爆发: a4+a5 叠协奏 (step 2/4)
      - 命理套爆发: 声骸+大招+E (step 8)
      - 奶套窗口: 重击+声骸 (step 10)
      - 满协奏变奏: 普攻后触发变奏切爱弥斯 (step 14)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chainsaw_active = False  # 电锯是否已激活

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

        # === 执行本步骤动作 ===
        for action in step[1]:
            self._exec_action(action)

        rotation.advance()

        # 判断是否需要变奏切人
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

        if kind == 'e':   # 共鸣技能
            # 在空中释放按E，切人
            self.click_resonance(time_out=0.3)

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招（click_liberation 自带时停记录）
            self.click_liberation()

        elif kind == 'a':  # 第N段普攻（a2 = 一段平a打出第二下,只按1次）
            self.normal_attack()
            self.sleep(0.07)

        elif kind == 'jump_a':  # 跳A
            self.task.send_key(self.task.key_config.get('Jump Key', 'Space'))
            self.sleep(0.05)
            self.normal_attack()

        elif kind == 'z':  # 重击 (heavy attack)
            self.heavy_attack(duration=0.4)

        elif kind == 'E':  # 开电锯 → E全程按住,不放f_break防止打断
            if self.flying():
                self.wait_down()
            self._chainsaw_active = True
            self.check_f_on_switch = False  # 电锯期间不发F键
            self.task.send_key_down(self.get_resonance_key())  # 按下E不松
            self.sleep(0.3)  # 等待电锯启动动画
            if not self.is_forte_full():
                self.heavy_attack(3.5)  # 电锯攻击(全程E按住)
            self.sleep(0.05)
            self.task.send_key_up(self.get_resonance_key())  # 松开发E

    def _do_fallback(self):
        """旋转完成后或无旋转时的后备动作（匹配原版优化逻辑）。

        含电锯流程: E → 声骸 → 大招 → 普攻(实时检查forte) → forte满开电锯 → 切人。
        """
        self.logger.info(f'[combo] {_CHAR_KEY} fallback — rotation done or no matching step')
        self.check_f_on_switch = True
        if self.has_intro:
            self.continues_normal_attack(0.8)
        if self.flying() and not self.liberation_available() and not self.resonance_available():
            self.wait_down()
        self.click_echo()
        start = time.time()
        timeout = 2.5
        under_liber = False
        tried_forte = False
        while time.time() - start < timeout:
            self.check_combat()
            if time.time() - start < 0.5 and self.click_liberation():
                start = time.time()
                under_liber = True
                timeout = 10
                self.sleep(0.2)
            if time.time() - start < 0.5 and not self.is_forte_full() and self.click_resonance()[0]:
                start = time.time()
                if timeout != 10:
                    timeout = 1.7
            if not tried_forte and (under_liber or True) and self.is_forte_full():
                tried_forte = True  # 无论成功失败，只尝试一次
                if self._perform_forte():
                    self.check_f_on_switch = False
                    self._chainsaw_active = True
                    return self.switch_next_char()
                # 失败 fallthrough → 下次循环走 tried_forte 退出
            if tried_forte and self.is_forte_full():
                break
            if self.is_con_full():
                break
            self.click()
            self.task.next_frame()
        self.switch_next_char()

    def _perform_forte(self):
        if self.flying():
            self.wait_down()
        self.task.send_key(self.get_resonance_key(), down_time=1.2)
        if self.is_forte_full():
            return False
        self.heavy_attack(3.5)
        return True

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            return super().get_switch_priority(current_char, has_intro, target_low_con)
        step = rotation.current_step
        if step and step[0] == _CHAR_KEY:
            return SwitchPriority.MUST
        return SwitchPriority.NO
