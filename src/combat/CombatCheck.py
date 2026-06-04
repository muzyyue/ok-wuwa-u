import re
import time

import win32api

from ok import find_boxes_by_name, Logger, calculate_color_percentage
from ok import find_color_rectangles, get_mask_in_color_range, is_pure_black
from src import text_white_color
from src.Labels import Labels
from src.char.Roccia import Roccia
from src.task.BaseWWTask import BaseWWTask

logger = Logger.get_logger(__name__)


class CombatCheck(BaseWWTask):
    """战斗状态检测类，负责入战/脱战判定、锁敌、Boss 识别、击破检测等。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_combat = False
        self.skip_combat_check = False
        self.boss_lv_template = None
        self.boss_lv_mask = None
        self._in_liberation = False  # return True
        self.has_count_down = False
        self.sleep_check_interval = 0.4
        self.last_out_of_combat_time = 0
        self.boss_lv_box = None
        self.boss_health_box = None
        self.boss_health = None
        self.last_break_check_time = 0
        self.out_of_combat_reason = ""
        self.last_in_realm_not_combat = 0
        self._last_liberation = 0
        self.target_enemy_time_out = 3
        self.switch_char_time_out = 5
        self.combat_end_condition = None
        self.has_lavitator = False
        self.target_enemy_error_notified = False
        self.cds = {
        }
        self.esc_count = 0
        self.can_break = False

    @property
    def in_liberation(self):
        """当前是否处于大招动画中（期间跳过大部分战斗检测）。"""
        return self._in_liberation

    @in_liberation.setter
    def in_liberation(self, value):
        self._in_liberation = value
        if value:
            self._last_liberation = time.time()

    def on_combat_check(self):
        """角色可重写的入战检测钩子，返回 False 则强制脱战。"""
        return True

    def reset_to_false(self, reason=""):
        """强制脱战，记录原因并重置所有缓存状态。"""
        self.out_of_combat_reason = reason
        self.do_reset_to_false()
        return False

    def do_reset_to_false(self):
        """重置所有战斗相关状态到初始值。"""
        self.cds = {}
        self._in_combat = False
        self.boss_lv_mask = None
        self.esc_count = 0
        self.boss_lv_template = None
        self.in_liberation = False  # return True
        self.has_count_down = False
        self.last_out_of_combat_time = 0
        self.boss_lv_box = None
        self.boss_health = None
        self.boss_health_box = None
        self.last_in_realm_not_combat = 0
        self.has_lavitator = False
        self.can_break = False
        self.scene.set_not_in_combat()
        return False

    def check_f_break(self):
        """检测屏幕中是否出现 F 击破/处决交互（破盾、终结 QTE）。"""
        if not self.can_break and not self._in_liberation and time.time() - self.last_break_check_time > 1:
            self.last_break_check_time = time.time()
            if self.find_one(Labels.f_break_full, threshold=0.9):
                self.logger.debug('found f_break_full')
                self.can_break = True
                return True
            if self.find_one('f_break', box=self.box_of_screen(0.2, 0.2, 0.75,
                                                               0.8), target_height=720):
                if not self.is_pick_f():
                    self.can_break = True
                    return True

    def f_break(self):
        """执行 F 键击破操作（破盾/处决），成功后清除击破标记。"""
        if self.can_break or self.check_f_break():
            self.send_key('f', after_sleep=0.1)
            self.can_break = False

    def check_count_down(self):
        """检测屏幕中央的倒计时数字（如深境限时），切换进出战斗状态。"""
        count_down_area = self.box_of_screen_scaled(3840, 2160, 1820, 266, 2100,
                                                    340, name="check_count_down", hcenter=True)
        count_down = self.calculate_color_percentage(text_white_color,
                                                     count_down_area)

        if self.has_count_down:
            if count_down < 0.03:
                numbers = self.ocr(box=count_down_area, match=count_down_re)
                if self.debug:
                    self.screenshot(f'count_down disappeared {count_down:.2f}%')
                logger.info(f'count_down disappeared {numbers} {count_down:.2f}%')
                if not numbers:
                    self.has_count_down = False
                    return False
                else:
                    return True
            else:
                return True
        else:
            if count_down > 0.03:
                numbers = self.ocr(box=count_down_area, match=count_down_re)
                if numbers:
                    self.has_count_down = True
                logger.info(f'set count_down to {self.has_count_down}  {numbers} {count_down:.2f}%')
            return self.has_count_down

    @property
    def target_area_box(self):
        """返回屏幕中心区域用于 OCR 读取敌方等级/名称的区域。"""
        return self.box_of_screen(0.1, 0.10, 0.9, 0.9, hcenter=True, name="target_area_box")

    def is_boss(self):
        """通过 Boss 破盾/锁定图标模板判断当前目标是否为 Boss。"""
        return self.find_one('boss_break_shield') or self.find_one('boss_break_lock')

    def do_check_in_combat(self, target):
        """核心入战检测逻辑：大招中直接返回 True；
        已入战时检查锁敌/Boss血量/倒计时；
        未入战时通过锁敌图标或敌方血量条判定入战。"""
        if self.in_liberation:
            return True
        if self._in_combat:
            if self.scene.in_combat() is not None:
                return self.scene.in_combat()
            self.check_f_break()
            if current_char := self.get_current_char():
                if current_char.skip_combat_check():
                    return self.scene.set_in_combat()
            if not self.on_combat_check():
                self.log_info('on_combat_check failed')
                return self.reset_to_false(reason='on_combat_check failed')
            if self.has_target():
                self.last_in_realm_not_combat = 0
                return self.scene.set_in_combat()
            if self.combat_end_condition is not None and self.combat_end_condition():
                return self.reset_to_false(reason='end condition reached')
            if self.target_enemy(wait=True):
                logger.debug(f'retarget enemy succeeded')
                return self.scene.set_in_combat()
            if self.should_check_monthly_card() and self.handle_monthly_card():
                return self.scene.set_in_combat()
            logger.error('target_enemy failed, try recheck break out of combat')
            return self.reset_to_false(reason='target enemy failed')
        else:
            from src.task.AutoCombatTask import AutoCombatTask
            has_target = self.has_target()
            if not has_target and target:
                self.log_debug('try target')
                self.middle_click(after_sleep=0.1)
            in_combat = has_target or ((self.config.get('Auto Target') or not isinstance(self,
                                                                                         AutoCombatTask)) and self.check_health_bar())
            if in_combat:
                if not has_target and not self.target_enemy(wait=True):
                    if not self.target_enemy_error_notified:
                        self.target_enemy_error_notified = True
                        self.log_error('Target enemy failed, please disable Nvidia/AMD Filter or Sharpening!',
                                       notify=True)
                    return False
                self.has_lavitator = self.find_one('edge_levitator', threshold=0.65)
                self.log_info(f'enter combat {self.has_lavitator}')
                self._in_combat = self.load_chars()
                return self._in_combat

    def in_combat(self, target=False):
        """主入口：调用 do_check_in_combat 并捕获所有异常，确保不会因检测崩溃。"""
        self.in_sleep_check = True
        try:
            return self.do_check_in_combat(target)
        except Exception as e:
            logger.error(f'do_check_in_combat:', e)
        finally:
            self.in_sleep_check = False

    def ensure_levitator(self):
        """确保角色处于浮游工具状态，打开轮盘选择并激活浮游工具。"""
        if not self.config.get('Check Levitator', True):
            return True
        if levi := self.find_one('edge_levitator', threshold=0.6):
            self.log_debug('edge levitator found {}'.format(levi))
            return True
        if self.has_char(Roccia):
            if self.find_one('levitator_roccia', threshold=0.6):
                return True
        if self.is_open_world_auto_combat():
            return False
        start = time.time()
        self.sleep(0.2)
        if levi := self.find_one('edge_levitator', threshold=0.6):
            self.log_debug('recheck edge levitator found {}'.format(levi))
            return True
        while time.time() - start < 1 and self.in_team()[0]:
            self.send_key_down(self.key_config.get('Wheel Key'))
            self.sleep(0.4)
        if self.in_team()[0]:
            self.log_info('can not open wheel')
            self.send_key_up(self.key_config.get('Wheel Key'))
            self.sleep(0.1)
            return False
        levitator = self.wait_feature('wheel_levitator', threshold=0.65, box=self.box_of_screen(0.27, 0.16, 0.68, 0.76))
        self.sleep(0.1)
        if not levitator:
            self.send_key_up(self.key_config.get('Wheel Key'))
            raise Exception('no levitator tool in the tab wheel!')
        old = win32api.GetCursorPos()
        self.move(levitator.x, levitator.y)
        abs_pos = self.executor.interaction.capture.get_abs_cords(levitator.x, levitator.y)
        win32api.SetCursorPos(abs_pos)
        self.sleep(0.1)
        self.send_key_up(self.key_config.get('Wheel Key'))
        self.sleep(0.2)
        win32api.SetCursorPos(old)
        if not self.wait_feature('edge_levitator', threshold=0.6, time_out=1):
            if self.has_char(Roccia):
                if self.find_one('levitator_roccia', threshold=0.6):
                    return True
        self.log_debug(f'ensuring leviator succees {levitator}')
        return self.target_enemy()

    def log_time(self, start, name):
        logger.debug(f'check cost {name} {time.time() - start}')
        return True

    def ocr_lv_text(self):
        """在目标区域 OCR 读取敌方等级文本（如 lv.90）。"""
        lvs = self.ocr(box=self.target_area_box,
                       match=re.compile(r'lv\.\d{1,3}', re.IGNORECASE),
                       target_height=540, name='lv_text')
        return lvs

    def get_target_names(self):
        """根据运行模式（云游戏/16:9宽屏/标准）返回对应的锁敌模板名称。"""
        has_name = 'has_target'
        no_name = 'no_target'
        if self.is_browser():
            has_name += '_cloud'
            no_name += '_cloud'
        elif self.width == 1600:
            has_name += '_169'
            no_name += '_169'
        return has_name, no_name

    def has_target(self, double_check=False):
        """检测锁敌标识（has_target / no_target），在多区域多分辨率下匹配。"""
        threshold = 0.6
        has_name, no_name = self.get_target_names()
        scale = 1.2 if self.is_browser() else 1.1
        best = self.find_best_match_in_box(self.get_box_by_name(has_name).scale(scale), [has_name, no_name],
                                           threshold=threshold)
        if not best:
            best = self.find_best_match_in_box(self.get_box_by_name('box_target_enemy_long'),
                                               [has_name, no_name],
                                               threshold=threshold)
        if not best:
            best = self.find_best_match_in_box(self.get_box_by_name('target_box_long2'), [has_name, no_name],
                                               threshold=threshold)

        if not best:
            best = self.find_best_match_in_box(self.get_box_by_name(has_name).scale(1.1, 2.0),
                                               [has_name, no_name],
                                               threshold=threshold)
            if best and self.esc_count == 0:
                if double_check:
                    logger.error(f'try fix bear echo')
                    self.send_key('esc', after_sleep=2)
                    self.send_key('esc', after_sleep=1.5)
                    self.esc_count = 1
                    return False
                else:
                    self.sleep(1)
                    return self.has_target(double_check=True)
        return best and best.name == has_name

    def target_enemy(self, wait=True):
        """锁定敌人：中键点击尝试锁敌，wait=True 时循环重试直到超时。"""
        if not wait:
            self.middle_click()
        else:
            if self.has_target():
                return True
            else:
                logger.info(f'target lost try retarget {self.target_enemy_time_out}')
                start = time.time()
                while time.time() - start < self.target_enemy_time_out:
                    self.middle_click(interval=0.2)
                    if self.has_target():
                        return True
                    self.next_frame()

    def has_health_bar(self):
        """通过颜色检测屏幕中是否有敌方血量条（红色普通 / 橙色 Boss）。"""
        if self._in_combat:
            min_height = self.height_of_screen(9 / 2160)
            max_height = min_height * 3
            min_width = self.width_of_screen(12 / 3840)
        else:
            min_height = self.height_of_screen(9 / 2160)
            max_height = min_height * 3
            min_width = self.width_of_screen(100 / 3840)

        boxes = find_color_rectangles(self.frame, enemy_health_color_red, min_width, min_height, max_height=max_height)

        if len(boxes) > 0:
            self.draw_boxes('enemy_health_bar_red', boxes, color='blue')
            return True
        else:
            boxes = find_color_rectangles(self.frame, boss_health_color, min_width, min_height * 1.3,
                                          box=self.box_of_screen(1269 / 3840, 58 / 2160, 2533 / 3840, 200 / 2160))
            if len(boxes) == 1:
                self.boss_health_box = boxes[0]
                self.boss_health_box.width = 10
                self.boss_health_box.x += 6
                self.boss_health = self.boss_health_box.crop_frame(self.frame)
                self.draw_boxes('boss_health', boxes, color='blue')
                return True
        return False

    def check_health_bar(self):
        """综合判断屏幕上是否有可战斗目标（血量条或 Boss 标记）。"""
        return self.has_health_bar() or self.is_boss()

    def keep_boss_text_white(self):
        """从 Boss 等级区域提取白色/橙色/红色文本，用于后续 OCR。"""
        cropped = self.boss_lv_box.crop_frame(self.frame)
        mask, area = get_mask_in_color_range(cropped, boss_white_text_color)
        if area / mask.shape[0] * mask.shape[1] < 0.05:
            mask, area = get_mask_in_color_range(cropped, boss_orange_text_color)
            if area / mask.shape[0] * mask.shape[1] < 0.05:
                mask, area = get_mask_in_color_range(cropped,
                                                     boss_red_text_color)
                if area / mask.shape[0] * mask.shape[1] < 0.05:
                    logger.error(f'keep_boss_text_white cant find text with the correct color')
                    return None, 0
        return cropped, mask


count_down_re = re.compile(r'\d\d')


def keep_only_white(frame):
    frame[frame != 255] = 0
    return frame


target_enemy_color_yellow = {  # 锁敌/瞄准状态下的黄色准星或标记颜色
    'r': (0x84, 0xAD),
    'g': (0x84, 0xAF),
    'b': (0x20, 0x6F)
}

enemy_health_color_red = {  # 普通敌方红色血量条颜色范围
    'r': (174, 225),
    'g': (55, 85),
    'b': (55, 76)
}

enemy_health_color_black = {  # 血量条底部的黑色背景区域
    'r': (10, 55),
    'g': (28, 50),
    'b': (18, 70)
}

boss_white_text_color = {  # Boss 名称/等级的白色文字
    'r': (200, 255),
    'g': (200, 255),
    'b': (200, 255)
}

boss_orange_text_color = {  # Boss 名称/等级的橙色文字
    'r': (218, 218),
    'g': (178, 178),
    'b': (68, 68)
}

boss_red_text_color = {  # Boss 名称/等级的红色文字
    'r': (200, 230),
    'g': (70, 90),
    'b': (60, 80)
}

boss_health_color = {  # Boss 橙色血量条颜色范围
    'r': (245, 255),
    'g': (30, 185),
    'b': (4, 75)
}

aim_color = {  # 瞄准/准星指示器颜色
    'r': (150, 213),
    'g': (148, 185),
    'b': (22, 62)
}
