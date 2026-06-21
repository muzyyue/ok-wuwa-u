"""合轴序列定义 —— 爱达千 (Aemeath + Denia + Chisa)轴

角色映射:
  千咲 (Chisa)
  爱弥斯/小艾 (Aemeath)
  达妮娅 (Denia)

机兵 = 爱弥斯的机甲形态（Aemeath 切换入场后进入机甲模式）

轴符号解析:
  e    = 共鸣技能 (resonance)
  q    = 声骸/深海 (echo)
  r    = 共鸣解放/大招 (liberation)
  aN   = 第N段普攻 (normal attack N times)
  跳a  = 跳跃攻击 (jump + click)
  E    = 强化小技能 (enhanced resonance, e.g. chainsaw startup)
  变奏 = 变奏入场 (intro switch)
"""
from enum import IntEnum, auto
def get_default_rotation() -> "RotationState":
    """获取默认轮换状态（给 combo_config.py 使用）。"""
    from src.combo.sequences import RotationState
    return RotationState()


class RotationStepFlag(IntEnum):
    NORMAL = auto()
    MECHA_PHASE = auto()    # 爱弥斯机甲形态（机兵）
    INTRO_SWITCH = auto()   # 变奏入场


# ────────────────────────────────────────────────────────────
# 新轴序列: 启动轮(20步) + 循环轮(21步) = 41步
#   启动轮 (steps 0-19):  首次战斗的完整流程
#   循环轮 (steps 20-40): 启动轮结束后, 变奏达a4E + 启动轮2-20步
#   循环结束时自动wrap到step 20 (LOOP_START=20)
# ────────────────────────────────────────────────────────────
#
# 动作列表: [('e',), ('q',), ('r',), ('a', N), ('jump_a',), ('E',), ('intro',), ('z',), ('f',)]
#
# 速度预期 (~0.6s/步, 41步 ≈ 25s 完整循环):
#   暖机 (steps  0-3):  千咲跳E→爱弥斯a23→千咲a4→达妮娅ERa12
#   爆发 (steps  4-9):  千咲a5→机兵a23→达妮娅a34→机兵a4e→千QRE→爱a光翼
#   电锯 (steps 10-13): 千ZQ→达E2→机兵a23e→达E3+a
#   变奏 (steps 14-18): 千a→变奏爱a3e→达a12Re→变奏机兵a3→达a1234
#   终结 (step    19):  机兵a4R(Z)EFa34EZR → 进入循环
#   循环 (step    20):  变奏达a4E → 重复step 1-19起点

AIDA_QIAN_NEW = [
    # ═══════════════════ 启动轮 (Startup) ═══════════════════
    #  0: 千跳aEa3 → 爱弥斯
    ('chisa',    [('jump_a',), ('e',), ('a', 3)],                            'aemeath', RotationStepFlag.NORMAL),
    #  1: 爱a23E（切换机兵） → 千咲
    ('aemeath',  [('a', 2), ('a', 3), ('e',)],                                'chisa',   RotationStepFlag.NORMAL),
    #  2: 千a4 → 达妮娅
    ('chisa',    [('a', 4)],                                                   'denia',   RotationStepFlag.NORMAL),
    #  3: 达EqRa12 → 千咲
    ('denia',    [('e',), ('q',), ('r',), ('a', 1), ('a', 2)],                        'chisa',   RotationStepFlag.NORMAL),
    #  4: 千a5 → 爱弥斯(机兵)
    ('chisa',    [('a', 5)],                                                   'aemeath', RotationStepFlag.MECHA_PHASE),
    #  5: 机兵a23 → 达妮娅
    ('aemeath',  [('a', 2), ('a', 3)],                                         'denia',   RotationStepFlag.MECHA_PHASE),
    #  6: 达a34 → 爱弥斯(机兵)
    ('denia',    [('a', 3), ('a', 4)],                                         'aemeath', RotationStepFlag.MECHA_PHASE),
    #  7: 机兵a4E → 千咲
    ('aemeath',  [('a', 4), ('e',)],                                           'chisa',   RotationStepFlag.MECHA_PHASE),
    #  8: 千QRE(命理套开Q) → 爱弥斯
    ('chisa',    [('q',), ('r',), ('e',)],                                     'aemeath', RotationStepFlag.NORMAL),
    #  9: 爱a光翼 → 千咲
    ('aemeath',  [('a',),('e',)],                                                      'chisa',   RotationStepFlag.NORMAL),
    # 10: 千ZQ(奶套开Q,Z:共鸣回路状态下的a) → 达妮娅
    ('chisa',    [('a',)],                                              'denia',   RotationStepFlag.NORMAL),
    # 11: 达E2 → 爱弥斯(机兵)
    ('denia',    [('E',)],                                                      'aemeath', RotationStepFlag.MECHA_PHASE),
    # 12: 机兵a23E → 达妮娅
    ('aemeath',  [('a', 2), ('a', 3), ('e',)],                                 'denia',   RotationStepFlag.MECHA_PHASE),
    # 13: 达E3(平a自动释放) → 千咲
    ('denia',    [('E',)],                                              'chisa',   RotationStepFlag.NORMAL),
    # 14: 千a → 爱弥斯(变奏)
    ('chisa',    [('a',)],                                                      'aemeath', RotationStepFlag.INTRO_SWITCH),
    # 15: 变奏爱a3E(3达以下打a34E) → 达妮娅
    ('aemeath',  [('intro',), ('a', 3), ('a', 4), ('e',)],                               'denia',   RotationStepFlag.NORMAL),
    # 16: 达(a12)R2(E,没满协奏补) → 爱弥斯(变奏)
    ('denia',    [('a', 1), ('a', 2), ('r',), ('e',)],                         'aemeath', RotationStepFlag.INTRO_SWITCH),
    # 17: 变奏机兵a3 → 达妮娅
    ('aemeath',  [('intro',), ('a', 3)],                                        'denia',   RotationStepFlag.INTRO_SWITCH),
    # 18: 达a1234(a4可选) → 爱弥斯
    ('denia',    [('a', 1), ('a', 2), ('a', 3), ('a', 4)],                     'aemeath', RotationStepFlag.NORMAL),
    # 19: 机兵a4R(Z)EFa34EZR → 达妮娅(进入循环)
    ('aemeath',  [('a', 4), ('r',), ('q',), ('e',), ('f',), ('a', 3), ('a', 4), ('ezr',)], 'denia', RotationStepFlag.NORMAL),

    # ═══════════════════ 循环轮 (Loop) ═══════════════════
    # 20(L0): 变奏达a4E → 千咲
    ('denia',    [('intro',), ('a', 4), ('e',)],                              'chisa',   RotationStepFlag.INTRO_SWITCH),
    # 21(L1): 千跳aEa3 → 爱弥斯
    ('chisa',    [('jump_a',), ('e',), ('a', 3)],                            'aemeath', RotationStepFlag.NORMAL),
    # 22(L2): 爱a23E → 千咲
    ('aemeath',  [('a', 2), ('a', 3), ('e',)],                                'chisa',   RotationStepFlag.NORMAL),
    # 23(L3): 千a4 → 达妮娅
    ('chisa',    [('a', 4)],                                                   'denia',   RotationStepFlag.NORMAL),
    # 24(L4): 达EqRa12 → 千咲
    ('denia',    [('e',), ('q',), ('r',), ('a', 1), ('a', 2)],                        'chisa',   RotationStepFlag.NORMAL),
    # 25(L5): 千a5 → 爱弥斯(机兵)
    ('chisa',    [('a', 5)],                                                   'aemeath', RotationStepFlag.MECHA_PHASE),
    # 26(L6): 机兵a23 → 达妮娅
    ('aemeath',  [('a', 2), ('a', 3)],                                         'denia',   RotationStepFlag.MECHA_PHASE),
    # 27(L7): 达a34 → 爱弥斯(机兵)
    ('denia',    [('a', 3), ('a', 4)],                                         'aemeath', RotationStepFlag.MECHA_PHASE),
    # 28(L8): 机兵a4E → 千咲
    ('aemeath',  [('a', 4), ('e',)],                                           'chisa',   RotationStepFlag.MECHA_PHASE),
    # 29(L9): 千QRE → 爱弥斯
    ('chisa',    [('q',), ('r',), ('e',)],                                     'aemeath', RotationStepFlag.NORMAL),
    # 30(L10): 爱a光翼 → 千咲
    ('aemeath',  [('a',),('e',)],                                                      'chisa',   RotationStepFlag.NORMAL),
    # 31(L11): 千ZQ → 达妮娅
    ('chisa',    [('a',)],                                              'denia',   RotationStepFlag.NORMAL),
    # 32(L12): 达E2 → 爱弥斯(机兵)
    ('denia',    [('E',)],                                                      'aemeath', RotationStepFlag.MECHA_PHASE),
    # 33(L13): 机兵a23E → 达妮娅
    ('aemeath',  [('a', 2), ('a', 3), ('e',)],                                 'denia',   RotationStepFlag.MECHA_PHASE),
    # 34(L14): 达E3(平a自动释放) → 千咲
    ('denia',    [('E',)],                                              'chisa',   RotationStepFlag.NORMAL),
    # 35(L15): 千a → 爱弥斯(变奏)
    ('chisa',    [('a',)],                                                      'aemeath', RotationStepFlag.INTRO_SWITCH),
    # 36(L16): 变奏爱a3E → 达妮娅
    ('aemeath',  [('intro',), ('a', 3), ('a', 4), ('e',)],                               'denia',   RotationStepFlag.NORMAL),
    # 37(L17): 达a12R2(E,没满协奏补) → 爱弥斯(变奏)
    ('denia',    [('a', 1), ('a', 2), ('r',), ('e',)],                         'aemeath', RotationStepFlag.INTRO_SWITCH),
    # 38(L18): 变奏机兵a3 → 达妮娅
    ('aemeath',  [('intro',), ('a', 3)],                                        'denia',   RotationStepFlag.INTRO_SWITCH),
    # 39(L19): 达a1234(a4可选) → 爱弥斯
    ('denia',    [('a', 1), ('a', 2), ('a', 3), ('a', 4)],                     'aemeath', RotationStepFlag.NORMAL),
    # 40(L20): 机兵a4R(Z)EFa34EZR → 达妮娅(循环起点)
    ('aemeath',  [('a', 4), ('r',), ('q',), ('e',), ('f',), ('a', 3), ('a', 4), ('ezr',)], 'denia', RotationStepFlag.NORMAL),
]

CHAR_KEY_TO_INDEX = {
    'chisa': 0,
    'aemeath': 1,
    'denia': 2,
}

INDEX_TO_CHAR_KEY = {v: k for k, v in CHAR_KEY_TO_INDEX.items()}


class RotationState:
    """共享旋转状态。每个 combo 角色通过 self.task.rotation 访问。

    支持启动轮+循环轮两段结构:
      - 首次从 step 0 (千咲) 开始执行启动轮 (20步)
      - 到达 step 20 (循环轮起点) 后 _startup_done=True
      - is_done() 后 reset() 回到 LOOP_START=20 重复循环
    """

    LOOP_START = 20  # 循环轮起始索引（0-indexed）

    def __init__(self, sequence=None):
        self.seq = sequence or AIDA_QIAN_NEW
        self.step_index = 0
        self._startup_done = False
        self.char_entry_tracker = {}  # char_key → 在本步骤中是否已执行

    @property
    def current_step(self):
        if 0 <= self.step_index < len(self.seq):
            return self.seq[self.step_index]
        return None

    @property
    def current_char_key(self):
        return self.current_step[0] if self.current_step else None

    @property
    def current_actions(self):
        return self.current_step[1] if self.current_step else []

    @property
    def next_char_key(self):
        return self.current_step[2] if self.current_step else None

    @property
    def current_flag(self):
        return self.current_step[3] if self.current_step else RotationStepFlag.NORMAL

    def advance(self):
        if self.step_index < len(self.seq):
            self.step_index += 1
        if not self._startup_done and self.step_index == self.LOOP_START:
            self._startup_done = True
        self.char_entry_tracker.clear()

    def is_done(self):
        return self.step_index >= len(self.seq)

    def reset(self, full_reset=False):
        if full_reset:
            self.step_index = 0
            self._startup_done = False
        else:
            self.step_index = self.LOOP_START if self._startup_done else 0
        self.char_entry_tracker.clear()

    def get_next_step_for_char(self, char_key):
        """获取指定角色下一个要执行的步骤索引（从当前扫描）。"""
        for i in range(self.step_index, len(self.seq)):
            if self.seq[i][0] == char_key:
                return i
        return -1


# ComboTab 显示用序列 — 爱达千 新轴步骤描述
# 注意: aN 表示第N段普攻（只按1下）, 不是按N下
AIDEQIAN_SEQUENCE = [
    {"desc": "千咲 跳A, E, a3", "actions": ["跳A", "E", "a3"]},
    {"desc": "爱弥斯 a2, a3, E", "actions": ["a2", "a3", "E"]},
    {"desc": "千咲 a4", "actions": ["a4"]},
    {"desc": "达妮娅 大招, a1, a2", "actions": ["大招", "a1", "a2"]},
    {"desc": "千咲 a5", "actions": ["a5"]},
    {"desc": "机兵 a2, a3", "actions": ["机兵", "a2", "a3"]},
    {"desc": "达妮娅 a3, a4", "actions": ["a3", "a4"]},
    {"desc": "机兵 a4, E", "actions": ["机兵", "a4", "E"]},
    {"desc": "千咲 声骸, 大招, E", "actions": ["声骸", "大招", "E"]},
    {"desc": "爱弥斯 a(光翼), E", "actions": ["a(光翼)", "E"]},
    {"desc": "千咲 a", "actions": ["a"]},
    {"desc": "达妮娅 强化E", "actions": ["强化E"]},
    {"desc": "机兵 a2, a3, E", "actions": ["机兵", "a2", "a3", "E"]},
    {"desc": "达妮娅 强化E", "actions": ["强化E"]},
    {"desc": "千咲 a, 变奏爱弥斯", "actions": ["a", "变奏"]},
    {"desc": "爱弥斯 变奏, a3, a4, E", "actions": ["变奏", "a3", "a4", "E"]},
    {"desc": "达妮娅 a1, a2, 大招, E", "actions": ["a1", "a2", "大招", "E"]},
    {"desc": "机兵 变奏, a3", "actions": ["变奏", "a3"]},
    {"desc": "达妮娅 a1, a2, a3, a4", "actions": ["a1", "a2", "a3", "a4"]},
    {"desc": "机兵 a4, 大招, a, E, F, a3, a4, E, Z, 大招", "actions": ["机兵", "a4", "大招", "a", "E", "F", "a3", "a4", "E", "Z重击", "大招"]},
    {"desc": "[循环] 达妮娅 变奏, a4, E", "actions": ["变奏", "a4", "E"]},
]
