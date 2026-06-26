"""
爱达千 25s 合轴 — 爱弥斯/小艾 (Aemeath)

爱弥斯在轴中的职责:
   步骤 1:  a2 a3 e             (小艾: 普攻2+3段+小技能)
   步骤 5:  a2 a3               (机兵: 普攻2+3段)
   步骤 7:  a4 e                (机兵: 普攻4段+小技能)
    步骤 9:  a e                 (小艾: 光翼+小技能)
   步骤 12: a2 a3 e             (机兵: 普攻2+3段+小技能)
    步骤 15: intro a3 a4 e       (变奏入场+普攻3+4段+小技能)
   步骤 17: intro a3            (变奏入场+普攻3段)
    步骤 19: a4 r a e f a3 a4 e z r (机兵终结连段)

机兵 = 爱弥斯的机甲形态。Aemeath 以 MECHA_PHASE 标记入场后
自动进入机甲模式，支持普攻连段(a)、小技能(e)、重击(z)、F击破(f)。
"""
import time

from src.char.BaseChar import BaseChar, SwitchPriority
from src.combo.sequences import RotationStepFlag

_CHAR_KEY = 'aemeath'


class Aemeath(BaseChar):
    """爱弥斯 25s 合轴版 — 双形态循环。

    合轴要点:
      - 小艾形态: 普攻2段+小技能 → 光翼触发
      - 机兵形态: 普攻+小技能+重击+F → 终结激光切人
      - 吃2次变奏开大后全技能爆发 (step 19: a4REFa34EZR)
      - 循环由 StepSequence 驱动, fallback 为原版逻辑

    周期映射:
      LIBERATION_COOLDOWN = 25  → 25s冷却
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
        self._resonance_rate = 0  # 共鸣率累计 (光翼共奏/过载获得), 满4点解锁完整大招
        self.should_wait = False
        self.intro_time = -1

    def do_perform(self):
        # 从共享的连招轮换状态获取当前该谁上场、做什么动作
        rotation = self.task.combo_config.rotation_state
        if rotation.is_done():
            self.logger.info(f'[combo] {_CHAR_KEY} rotation done (idx={rotation.step_index}) → reset')
            rotation.reset()
        idx = rotation.step_index  # 日志用,放在 reset 之后

        step = rotation.current_step       # step = ('aemeath', [('a',2)], 'denia', NORMAL)
        if not step:
            self.logger.info(f'[combo] {_CHAR_KEY} step is None → switch')
            return self.switch_next_char()
        if step[0] != _CHAR_KEY:           # step 标记的角色不是'我吗 → 切给正确的角色
            self.logger.info(f'[combo] {_CHAR_KEY} step {idx} is for {step[0]} → switch')
            return self.switch_next_char()

        self.logger.info(f'[combo] {_CHAR_KEY} step {idx} enter: actions={step[1]} flag={step[3].name} next={step[2]}')

        # === 入场缓冲：确保角色就位后再发动作 ===
        # 变奏入场：等落地动画播完
        if self.has_intro and (not step[1] or step[1][0][0] != 'intro'):
            self.logger.info(f'[combo] {_CHAR_KEY} has_intro=True → wait intro landing')
            self.wait_intro(0.4, click=True)
        # 普通切人：游戏有极短的进场过渡，普攻 click 易被吞
        elif not self.has_intro:
            self.logger.info(f'[combo] {_CHAR_KEY} normal switch → settle 0.5s')
            self.sleep(0.5)

        # === 机甲形态入口：小延迟模拟变机甲动画 ===
        if step[3] == RotationStepFlag.MECHA_PHASE:
            self.logger.info(f'[combo] {_CHAR_KEY} mecha phase → sleep 0.15s')
            self.sleep(0.15)

        # === 执行本步骤动作 ===
        for action in step[1]:     # step[1] = [('a', 2)] → 依次执行每个动作
            self._exec_action(action)

        rotation.advance()        # 本步骤完成,推进到下一步
        # 读取下一步信息,判断下一位入场方式
        next_step = rotation.current_step
        next_is_intro = next_step and next_step[3] == RotationStepFlag.INTRO_SWITCH
        next_char = next_step[0] if next_step else None

        self.logger.info(f'[combo] {_CHAR_KEY} step {idx} done → advance to {rotation.step_index}, switch to {next_char} (free_intro={next_is_intro})')

        if next_is_intro:
            self.switch_next_char(free_intro=True)   # 下一步要求变奏入场(协奏值已满)
        else:
            self.switch_next_char()                  # 普通切人(无入场技)

    def _exec_action(self, action):
        kind = action[0]
        self.logger.info(f'[combo]  {_CHAR_KEY} exec {action}')

        if kind == 'e':   # 共鸣技能 (只有强化E/光翼共奏才获得共鸣率)
            is_enhanced = self.enhance_e_available()
            clicked, dur, animated = self.click_resonance(time_out=0.5)
            if clicked and is_enhanced:
                self._resonance_rate += 1
                self.logger.info(f'[combo]  {_CHAR_KEY} 光翼共奏 → 共鸣率+1 (dur={dur:.2f}s) total={self._resonance_rate}')
            elif clicked:
                self.logger.info(f'[combo]  {_CHAR_KEY} 普通E, 未获得共鸣率 (enhanced={is_enhanced})')
            else:
                self.logger.warning(f'[combo]  {_CHAR_KEY} E FAILED ({clicked}, {dur:.2f}s, {animated})')

        elif kind == 'ezr':  # 预输入连段: E → 长按重击(预输入) → R(预输入)
            self.logger.info(f'[combo]  {_CHAR_KEY} ezr pre-input combo')
            ezr_enhanced = self.enhance_e_available()
            e_clicked, e_dur, e_anim = self.click_resonance(time_out=0.3)   # 点E
            if e_clicked and ezr_enhanced:
                self._resonance_rate += 1                    # 光翼共奏才加共鸣率
                self.logger.info(f'[combo]  {_CHAR_KEY} ezr 光翼共奏 → 共鸣率+1 (dur={e_dur:.2f}s) total={self._resonance_rate}')
            elif e_clicked:
                self.logger.info(f'[combo]  {_CHAR_KEY} ezr 普通E, 未获得共鸣率 (enhanced={ezr_enhanced})')
            else:
                self.logger.warning(f'[combo]  {_CHAR_KEY} ezr E FAILED ({e_clicked}, {e_dur:.2f}s, {e_anim})')
            self.task.mouse_down()                # 立即按住重击(预输入,在E动画期间)
            self.sleep(0.6)                       # 等E打完+重击蓄力出来
            if self._resonance_rate >= 4:          # 共鸣率满4点才释放 ezr 中的 R
                self.click_liberation()           # 按住重击的同时按R(预输入)
                self.logger.info(f'[combo]  {_CHAR_KEY} ezr liberation fired (共鸣率≥4)')
            else:
                self.logger.info(f'[combo]  {_CHAR_KEY} ezr skip liberation (共鸣率={self._resonance_rate}<4)')
            self.sleep(0.3)                       # 等R+重击打完
            self.task.mouse_up()                  # 松开重击

        elif kind == 'q':  # 声骸
            self.click_echo(time_out=0.5)

        elif kind == 'r':  # 大招（消耗4点共鸣率, click_liberation 自带时停记录）
            if self._resonance_rate >= 4:
                self.click_liberation()
                self.logger.info(f'[combo]  {_CHAR_KEY} liberation fired (共鸣率≥4)')
            else:
                self.logger.info(f'[combo]  {_CHAR_KEY} skip liberation — 共鸣率={self._resonance_rate}<4, normal attack instead')
                self.normal_attack()

        elif kind == 'a':  # 第N段普攻（a2 = 一段平a打出第二下,只按1次）
            self.logger.info(f'[combo]  {_CHAR_KEY} normal_attack BEFORE')
            self.normal_attack()
            self.logger.info(f'[combo]  {_CHAR_KEY} normal_attack AFTER  → sleep 0.07')
            self.sleep(0.07)

        elif kind == 'z':  # 重击 (heavy attack)
            self.heavy_attack(duration=0.4)

        elif kind == 'f':  # F键击破/下落攻击
            self.f_break()

        elif kind == 'intro':  # 变奏入场 — 等待入场动画即可
            self.wait_intro(0.8)

    def _do_fallback(self):
        """旋转完成后的后备动作，保持原 Aemeath 的 lib1→lib2 循环。"""
        self.logger.info(f'[combo] {_CHAR_KEY} fallback — rotation done or no matching step')
        self._resonance_rate = 0
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
