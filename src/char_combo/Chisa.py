"""
爱达千 17s 合轴 — 千咲 (Chisa)

千咲在轴中的职责:
  步骤 1:  e q r a3          (eqr间隔~0.2s)
  步骤 5:  a4
  步骤 7:  a5 跳a E           (开电锯)
   步骤 10: a2                 (电锯形态)
  步骤 12: a3
  步骤 15: a4                 (电锯终结→满协奏→变奏)
"""
import time

from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'chisa'


class Chisa(BaseChar):
    """千咲 17s 合轴版 — 支持电锯模式与后台自动收益。

    合轴要点:
      - 入场: E → 声骸 → 大招 → 3~5段普攻 → 跳A开电锯 (step 1/5/7)
      - 电锯第 2~3 段在后台自动完成长按效果，切人不损失 (step 10/12)
      - 电锯终结 (a4) 满协奏 → 变奏切爱弥斯 (step 15)
      - 千咲切人 CD 转好后立刻切回 (严格管理)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chainsaw_active = False  # 电锯是否已激活

    def do_perform(self):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            rotation.reset()  # 循环轴: 从头开始,避免fallback

        step = rotation.current_step
        if not step:
            return self.switch_next_char()
        if step[0] != _CHAR_KEY:
            # 不是我的轮次，让系统切到正确的角色
            return self.switch_next_char()

        # === 执行本步骤动作 ===
        for action in step[1]:
            self._exec_action(action)

        # 前进到下一步
        rotation.advance()

        # 判断是否需要变奏切人
        next_step = rotation.current_step
        next_is_intro = next_step and next_step[3] == RotationStepFlag.INTRO_SWITCH

        if next_is_intro:
            self.switch_next_char(free_intro=True)
        else:
            self.switch_next_char()

    def _exec_action(self, action):
        kind = action[0]

        if kind == 'e':   # 共鸣技能
            # 在空中释放按E，切人
            self.click_resonance(time_out=0.3)

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招 → 接 f_break 补伤害
            self.click_liberation()
            self.f_break()

        elif kind == 'a':  # 普攻N段
            count = action[1]
            for _ in range(count):
                self.normal_attack()
                self.sleep(0.07)

        elif kind == 'jump_a':  # 跳A
            self.task.send_key(self.task.key_config.get('Jump Key', 'Space'))
            self.sleep(0.05)
            self.normal_attack()

        elif kind == 'E':  # 开电锯 → 触发后立即切人，后台自动完成
            if self.flying():
                self.wait_down()
            self._chainsaw_active = True
            # 只长按E激活电锯，不执行重击——电锯第2~3段后台自动
            self.task.send_key(self.get_resonance_key(), down_time=1.0)
            self.f_break()

    def _do_fallback(self):
        """旋转完成后或无旋转时的后备动作（匹配原版优化逻辑）。

        含电锯流程: E → 声骸 → 大招 → 普攻(实时检查forte) → forte满开电锯 → 切人。
        """
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
