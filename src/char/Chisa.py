"""千咲 - 角色自动战斗逻辑（支持 DPS/辅助双模式）。

千咲可根据配置切换主输出或辅助模式，辅助模式下快速释放技能后切人。
"""
from src.char.BaseChar import BaseChar, CharType, get_default_buff_time

# 辅助模式每次上场最大驻场时间
_SUPPORT_MAX_STAY = 2.0


class Chisa(BaseChar):
    """千咲的自动化战斗控制类。

    辅助模式：入场技 + 声骸 + 大招 + 共鸣技 + 普攻（实时检查 forte 满开电锯）→ 切人
    DPS 模式：完整的技能循环（含解放延长驻场 + forte 满电锯爆发）
    """

    def is_dps_config(self):
        return self.task and self.task.char_config.get("Chisa DPS")

    def get_char_type(self):
        if self.is_dps_config():
            return CharType.MAIN_DPS
        return super().get_char_type()

    def get_buff_time(self):
        if self.is_dps_config():
            return get_default_buff_time(CharType.MAIN_DPS)
        return super().get_buff_time()

    def do_perform(self):
        if not self.is_dps_config():
            return self.do_fast_support()
        return self.do_dps_perform()

    def do_fast_support(self):
        """辅助模式：快速释放技能上 buff 后切人给主C输出。

        对比旧版改动:
          - 移除了 continues_normal_attack(0.8) (不检查 forte)
          - 改用普攻循环实时检查 is_forte_full()，满则立刻开电锯
          - 电锯只长按 E 触发不执行重击，后台自动完成不损失
          - 抬头检查 is_con_full() 协奏满即切
          - 1.5s 超时保护（原约 4.7s = 0.8 普攻 + 1.2 长按 E + 3.5 重击）
        """
        self.check_f_on_switch = True
        if self.has_intro:
            self.record_support_buff()
        if self.flying():
            self.wait_down()
        self.click_echo(time_out=0)
        if self.click_liberation():
            self.record_support_buff()
            self.f_break()
        # 空中释放E,切人
        if self.flying():
            self.click_resonance(time_out=0.3)
            self.switch_next_char()

        # 普攻循环：实时检查 forte / concerto / 超时
        start = time.time()
        while self.time_elapsed_accounting_for_freeze(start) < _SUPPORT_MAX_STAY:
            self.check_combat()
            if self.is_forte_full():
                self._quick_chainsaw()
                break
            if self.is_con_full():
                break
            self.click()
            self.task.next_frame()
        self.switch_next_char()

    def _quick_chainsaw(self):
        """快速触发电锯（长按 E），触发后立即切人由后台自动完成。"""
        if self.flying():
            self.wait_down()
        self.task.send_key(self.get_resonance_key(), down_time=1.0)
        self.sleep(0.05)

    def record_support_buff(self):
        self.last_buff_time = time.time()

    def switch_out(self, con_full=False):
        support_buff_time = self.last_buff_time
        super().switch_out(con_full=con_full)
        if not self.is_dps_config():
            self.last_buff_time = support_buff_time

    def do_dps_perform(self):
        """DPS 模式：完整的技能循环。

        对比旧版改动:
          - perform_forte 失败后不再重试（防止死循环普攻）
          - 循环中增加 is_con_full() 协奏满即切
          - 增加 is_first_engage 超时保护减少首次站场
          - 增加 resort 机制：大招/共鸣未好时提前退出
        """
        timeout = 2.5
        self.check_f_on_switch = True
        if self.has_intro:
            self.continues_normal_attack(0.8)
            timeout = 2.3
        if self.flying():
            self.wait_down()
        self.click_echo()
        start = time.time()
        under_liber = False
        tried_forte = False  # 防止 perform_forte 失败后反复重试
        while self.time_elapsed_accounting_for_freeze(start) < timeout:
            self.check_combat()
            if self.time_elapsed_accounting_for_freeze(start) < 0.5 and self.click_liberation():
                start = time.time()
                under_liber = True
                timeout = 10
                self.f_break()
                self.sleep(0.2)
            if self.time_elapsed_accounting_for_freeze(start) < 0.5 \
                    and not self.is_forte_full() and self.click_resonance()[0]:
                start = time.time()
                if timeout != 10:
                    timeout = 1.7
            if not tried_forte and (under_liber or self.is_dps_config()) and self.is_forte_full():
                tried_forte = True  # 无论成功失败，只尝试一次
                if self.perform_forte():
                    self.check_f_on_switch = False
                    return self.switch_next_char()
                # 失败 fallthrough → 下次循环走 tried_forte 退出
            if self.is_con_full():
                break
            # forte 满了但 perform_forte 已失败过 → 不重试，直接切
            if tried_forte and self.is_forte_full():
                break
            self.click()
            self.task.next_frame()
        self.switch_next_char()

    def perform_forte(self):
        if self.flying():
            self.wait_down()
        self.task.send_key(self.get_resonance_key(), down_time=1.2)
        if self.is_forte_full():
            return False
        self.heavy_attack(3.5)
        return True
