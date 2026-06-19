"""
爱达千 17s 合轴 — 爱弥斯/小艾 (Aemeath)

爱弥斯在轴中的职责:
  步骤 2:  a2                 (自动接普攻第2段)
  步骤 4:  a3 e
  步骤 9:  a2 a3              (机甲形态=机兵)
  步骤 13: a4 e               (机甲形态=机兵)
  步骤 16: 变奏入场
  步骤 18: 变奏入场 q r a1

机兵 = 爱弥斯的机甲形态。步骤 8/12 切入场后自动进入机甲模式，
支持普攻连段(a)和小技能(e)。
"""
import time

from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'aemeath'


class Aemeath(BaseChar):
    """爱弥斯 17s/25s 合轴版 — 巨剑/三光翼双周期循环。

    合轴要点:
      - 17s 巨剑周期: lib1（第一次解放），暖机后快速释放
      - 25s 三光翼周期: lib2（第二次解放），需要声骸后台蓄力
      - 小艾形态: 普攻2段+小技能 → 可合轴 (step 2/4)
      - 机兵形态: 普攻3段+小技能 → 激光出现切人 (step 9/13)
      - 吃2次变奏开大: step 16(变奏)×step 18(变奏+q+r+a1)

    周期映射:
      LIBERATION_COOLDOWN = 25  → 三光翼25s冷却
      INTRO_LIBERATION_DELAY = 14 → 入场后14s内可放巨剑
      LIBERATION_FORCE_DURATION = 30 → 30s后强制解锁巨剑
    """

    LIBERATION_COOLDOWN = 25
    LIBERATION_FORCE_DURATION = 30
    LIB2_PREPARE_WINDOW = 8
    INTRO_LIBERATION_DELAY = 14

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_liber = -1
        self.last_enhance_e = -1
        self.intro_liberation_time = -1
        self.pending_lib2 = False
        self._lib1_cast_count = 0
        self._lib2_cast_count = 0
        self.should_wait = False
        self.intro_time = -1

    def do_perform(self):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            rotation.reset()  # 循环轴: 从头开始,避免进入fallback长时间站场

        step = rotation.current_step
        if not step:
            return self.switch_next_char()
        if step[0] != _CHAR_KEY:
            return self.switch_next_char()

        # === 机甲形态入口：小延迟模拟变机甲动画 ===
        if step[3] == RotationStepFlag.MECHA_PHASE:
            self.sleep(0.15)

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

        if kind == 'e':   # 共鸣技能
            self.click_resonance(time_out=0.5)

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招 (爱弥斯超时后自然释放)
            self.click_liberation()

        elif kind == 'a':  # 普攻N段
            count = action[1]
            for _ in range(count):
                self.normal_attack()
                self.sleep(0.07)

        elif kind == 'intro':  # 变奏入场 — 等待入场动画即可
            self.wait_intro(0.8)

    def _do_fallback(self):
        """旋转完成后的后备动作，保持原 Aemeath 的 lib1→lib2 循环。"""
        self.intro_time = -1
        self.should_wait = False
        self._lib1_cast_count = 0
        self._lib2_cast_count = 0
        # 不清零 last_liber: 保留解放CD追踪,防止过早重入场时误判CD已好
        self.last_enhance_e = -1
        self.intro_liberation_time = -1
        self.pending_lib2 = False
        if self.has_intro:
            self.record_intro_liberation()
            self.continues_normal_attack(1.2)
            if self.check_outro() in {'char_linnai', 'char_lupa'}:
                self.intro_time = 14
            if self.check_outro() in {'chang_changli', 'char_changli2'}:
                self.intro_time = 10
        self.perform_everything()
        self._process_end_of_turn_liberations()
        self.switch_next_char()

    # === 以下方法从原始 Aemeath 直接复制，用于 fallback ===

    LIBERATION_COOLDOWN = 25
    LIBERATION_FORCE_DURATION = 30
    LIB2_PREPARE_WINDOW = 8
    INTRO_LIBERATION_DELAY = 14

    def lib2_cooldown_anchor(self):
        if self.last_liber >= 0:
            return self.last_liber
        combat_start = getattr(self.task, 'combat_start', -1)
        return combat_start if combat_start > 0 else -1

    def lib2_cooldown_left(self):
        anchor = self.lib2_cooldown_anchor()
        if anchor < 0:
            return 0
        elapsed = self.time_elapsed_accounting_for_freeze(anchor)
        return max(0, self.LIBERATION_COOLDOWN - elapsed)

    def liberation_cooldown_left(self):
        if self.last_liber < 0:
            return 0
        elapsed = self.time_elapsed_accounting_for_freeze(self.last_liber)
        return max(0, self.LIBERATION_COOLDOWN - elapsed)

    def lib1_unlock_anchor(self):
        if self.last_liber >= 0:
            return self.last_liber
        return getattr(self.task, 'combat_start', -1)

    def record_intro_liberation(self):
        self.intro_liberation_time = time.time()

    def intro_lib1_ready(self):
        return self.intro_liberation_time >= 0 and (
            self.time_elapsed_accounting_for_freeze(self.intro_liberation_time)
            <= self.INTRO_LIBERATION_DELAY)

    def lib1_unlocked(self):
        if self.intro_lib1_ready():
            return True
        anchor = self.lib1_unlock_anchor()
        return anchor >= 0 and (
            self.time_elapsed_accounting_for_freeze(anchor) >= self.LIBERATION_FORCE_DURATION)

    def can_cast_lib1(self):
        return self.liberation_cooldown_left() <= 0 and self.lib1_unlocked()

    def can_cast_liberation(self):
        return self.can_cast_lib1()

    def lib2_available(self):
        return bool(self.task.find_one('aemeath_lib2', threshold=0.7))

    def preparing_lib2(self):
        return self.lib2_cooldown_anchor() >= 0 and (
            self.lib2_cooldown_left() < self.LIB2_PREPARE_WINDOW)

    def should_wait_for_lib2(self):
        return self.pending_lib2 or self.preparing_lib2()

    def should_wait_for_enhance_e(self):
        return self.time_elapsed_accounting_for_freeze(self.last_enhance_e) > 12

    def record_enhance_e(self):
        self.last_enhance_e = time.time()

    def record_heavy_liberation(self):
        self.pending_lib2 = True

    def record_liberation(self, is_lib2):
        if is_lib2:
            self.pending_lib2 = False
            self.last_liber = time.time()
            self.last_enhance_e = self.last_liber
            self._lib2_cast_count += 1
        else:
            self.intro_liberation_time = -1
            self._lib1_cast_count += 1

    def _lib1_cast_this_turn(self):
        return self._lib1_cast_count > 0

    def _lib2_cast_this_turn(self):
        return self._lib2_cast_count > 0

    def _execute_lib2_guard(self, context_log=""):
        lib2_guard_start = time.time()
        self.logger.info(f'Aemeath [do_perform] waiting for lib2 before switching {context_log}')
        while not self._lib2_cast_this_turn():
            elapsed = time.time() - lib2_guard_start
            if elapsed > 13:
                self.logger.warning(f'Aemeath [do_perform] lib2 guard timed out (13s) {context_log}, casting switch')
                break
            # 不在准备窗口且模板也没出现 → 不等了,节约战场时间
            if elapsed > 2 and not self.should_wait_for_lib2() and not self.lib2_available():
                self.logger.debug(f'Aemeath [do_perform] not in lib2 window at {elapsed:.1f}s, skipping guard')
                break
            self.check_combat()
            if self.handle_heavy():
                self.task.next_frame()
                continue
            if self.lib2_available():
                if self.lib():
                    break
            if self.enhance_e_available():
                self.click_resonance(has_animation=True, send_click=True,
                                     animation_min_duration=0.5, time_out=1.5)
            self.click(after_sleep=0.01)
            self.task.next_frame()

    def _execute_lib1_or_fallback_guard(self):
        lib_guard_start = time.time()
        found_action = False
        while time.time() - lib_guard_start < 10.0:
            self.check_combat()
            # 解放CD还长且没有其他事可做 → 提前退出不等了
            if self.liberation_cooldown_left() > 5 and not self.enhance_e_available() and not self.lib2_available():
                self.logger.debug(f'Aemeath [do_perform] liberation CD too long, skipping fallback guard')
                break
            if self.liberation_available() and self.can_cast_lib1():
                self.lib()
                found_action = True
                self._execute_lib2_guard(context_log="(after forced lib1)")
                break
            elif self.enhance_e_available():
                self.click_resonance(has_animation=True, send_click=True,
                                     animation_min_duration=0.5, time_out=1.5)
                found_action = True
                break
            else:
                if not self.handle_heavy():
                    self.click(after_sleep=0.01)
                self.task.next_frame()
        if not found_action:
            self.logger.warning(
                'Aemeath [do_perform] 8s window elapsed with no available skill, '
                'allowing switch without liberation'
            )

    def _execute_post_lib2_combo(self):
        for i in range(3):
            self.check_combat()
            self.normal_attack()
            self.sleep(0.25)
        self.check_combat()
        e_available = self.enhance_e_available() or not self.task.has_cd('resonance')
        if e_available:
            self.click_resonance(has_animation=True, send_click=True, animation_min_duration=0.5, time_out=1.5)
            self.record_enhance_e()

    def _process_end_of_turn_liberations(self):
        if self._lib1_cast_this_turn() and not self._lib2_cast_this_turn():
            self._execute_lib2_guard(context_log="(initial lib1 cast)")
        elif not self._lib1_cast_this_turn() and not self._lib2_cast_this_turn():
            self._execute_lib1_or_fallback_guard()

    def lib(self):
        is_lib2 = self.lib2_available()
        if not is_lib2 and not self.can_cast_lib1():
            return False
        # lib2 也检查 CD,防止模板误识别在CD期间空按
        if is_lib2 and self.liberation_cooldown_left() > 0:
            return False
        if not self.click_liberation(wait_if_cd_ready=0):
            return False
        self.record_liberation(is_lib2)
        self.f_break()
        if is_lib2:
            self._execute_post_lib2_combo()
        return True

    def perform_everything(self):
        start = time.time()
        self.should_wait = self.should_wait_for_lib2() or self.should_wait_for_enhance_e()
        if not self.should_wait:
            self.should_wait = self.has_intro and self.liberation_cooldown_left() < 12
        while self.time_elapsed_accounting_for_freeze(start) < 1.2 or (
                self.should_wait and self.time_elapsed_accounting_for_freeze(start) < 3.6):
            self.cycle_start()
            if self.handle_heavy():
                self.f_break()
                start = time.time()
                self.should_wait = self.should_wait_for_lib2()
                self.task.next_frame()
                continue
            if self.intro_lib1_ready() and self.lib():
                start = time.time()
                self.should_wait = self.should_wait_for_lib2()
            elif self.enhance_e_available():
                if self.click_resonance(has_animation=True, send_click=True, animation_min_duration=0.5,
                                        time_out=1.5)[0]:
                    self.record_enhance_e()
                    self.click_echo(time_out=0)
                    self.f_break()
                    self.task.next_frame()
                if (self.intro_lib1_ready() and self.can_cast_lib1() and self.liberation_available()) or self.has_long_action():
                    start = time.time()
                else:
                    self.click(after_sleep=0.01)
                    return
            elif self.lib():
                start = time.time()
                self.should_wait = self.should_wait_for_lib2()
                continue
            elif self.click_resonance(send_click=False, time_out=0.5)[0]:
                self.click_echo(time_out=0)
                self.f_break()
            elif self.click_echo(time_out=0):
                pass
            else:
                self.click()
            self.cycle_sleep()

    def continue_in_intro(self):
        """判断是否在入场 buff 窗口内继续站场（适配 17s 巨剑/25s 三光翼周期）。"""
        return self.time_elapsed_accounting_for_freeze(self.last_liber) < 30 and \
            self.time_elapsed_accounting_for_freeze(self.last_perform) < self.intro_time

    def lib_cd_eminent(self):
        cd = self.task.get_cd('liberation')
        return self.lib1_unlocked() and (0 < cd < 1.5 or self.liberation_available())

    def enhance_e_available(self):
        return self.task.find_one('aemeath_e1', threshold=0.7) or self.task.find_one('aemeath_e2', threshold=0.7)

    def heavy_wait_highlight_down(self):
        self.task.mouse_down()
        ret = self.task.wait_until(lambda: not self.has_long_action(), time_out=1.2)
        self.task.mouse_up()
        self.sleep(0.01)
        return ret

    def handle_heavy(self):
        if not self.has_long_action():
            return False
        prepares_lib2 = self.preparing_lib2()
        if self.heavy_wait_highlight_down():
            if prepares_lib2:
                self.record_heavy_liberation()
            return True
        return False

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            if self.should_wait_for_lib2():
                return SwitchPriority.MUST
            return super().get_switch_priority(current_char, has_intro, target_low_con)
        step = rotation.current_step
        if step and step[0] == _CHAR_KEY:
            return SwitchPriority.MUST
        return SwitchPriority.NO

    def on_combat_end(self, chars):
        self.switch_other_char()
