"""合轴序列定义 —— 爱达千 (Aemeath + Denia + Chisa) 17s 轴

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
from typing import Optional


def get_default_rotation() -> "RotationState":
    """获取默认轮换状态（给 combo_config.py 使用）。"""
    from src.combo.sequences import RotationState
    return RotationState()


class RotationStepFlag(IntEnum):
    NORMAL = auto()
    MECHA_PHASE = auto()    # 爱弥斯机甲形态（机兵）
    INTRO_SWITCH = auto()   # 变奏入场


# 每一步: (角色key, 动作列表, 下一步角色key, 标记)
# 动作列表: [('e',), ('q',), ('r',), ('a', N), ('jump_a',), ('E',), ('intro',)]
#
# 17s 定时参考 (18步 × ~0.94s/步):
#   暖机期 (step 1-4):    ~3.8s  千咲/EQ/R → 爱弥斯/A2 → 达妮娅 → 爱弥斯
#   输出期 (step 5-12):   ~7.5s  千咲电锯 → 达妮娅 → 爱弥斯机兵 → 循环
#   收尾期 (step 13-18):  ~5.7s  机兵终结 → 千咲满协奏 → 2x变奏 → 爱弥斯爆发
#   总计: ~17s

AIDA_QIAN_17S = [
    # ── 1: 千咲 e q r a3 → 爱弥斯 ──
    ('chisa',    [('e',), ('q',), ('r',), ('a', 3)],                                          'aemeath', RotationStepFlag.NORMAL),
    # ── 2: 爱弥斯 a2 → 达妮娅 ──
    ('aemeath',  [('a', 2)],                                                                    'denia',   RotationStepFlag.NORMAL),
    # ── 3: 达妮娅 e q r a1 → 爱弥斯 ──
    ('denia',    [('e',), ('q',), ('r',), ('a', 1)],                                 'aemeath', RotationStepFlag.NORMAL),
    # ── 4: 爱弥斯 a3 e → 千咲 ──
    ('aemeath',  [('a', 3), ('e',)],                                                            'chisa',   RotationStepFlag.NORMAL),
    # ── 5: 千咲 a4 → 达妮娅 ──
    ('chisa',    [('a', 4)],                                                                    'denia',   RotationStepFlag.NORMAL),
    # ── 6: 达妮娅 a2 a3 → 千咲 ──
    ('denia',    [('a', 2), ('a', 3)],                                                         'chisa',   RotationStepFlag.NORMAL),
    # ── 7: 千咲 a5 跳a E(开电锯) → 达妮娅 ──
    ('chisa',    [('a', 5), ('jump_a',), ('E',)],                                              'denia',   RotationStepFlag.NORMAL),
    # ── 8: 达妮娅 a4 → 爱弥斯(机兵形态) ──
    ('denia',    [('a', 4)],                                                                    'aemeath', RotationStepFlag.MECHA_PHASE),
    # ── 9: 爱弥斯(机甲) a2 a3 → 千咲 ──
    ('aemeath',  [('a', 2), ('a', 3)],                                                         'chisa',   RotationStepFlag.MECHA_PHASE),
    # ── 10: 千咲(电锯) a2 → 达妮娅 ──
    ('chisa',    [('a', 2)],                                                                    'denia',   RotationStepFlag.NORMAL),
    # ── 11: 达妮娅 a1 a2 E → 千咲 ──
    ('denia',    [('a', 1), ('a', 2), ('E',)],                                                  'chisa',   RotationStepFlag.NORMAL),
    # ── 12: 千咲(电锯) a3 → 爱弥斯(机兵形态) ──
    ('chisa',    [('a', 3)],                                                                    'aemeath', RotationStepFlag.MECHA_PHASE),
    # ── 13: 爱弥斯(机甲) a4 e → 达妮娅 ──
    ('aemeath',  [('a', 4), ('e',)],                                                            'denia',   RotationStepFlag.MECHA_PHASE),
    # ── 14: 达妮娅 E2 → 千咲 ──
    ('denia',    [('E',)],                                                                       'chisa',   RotationStepFlag.NORMAL),
    # ── 15: 千咲(电锯)a4(满协奏→变奏爱) → 爱弥斯 ──
    ('chisa',    [('a', 4)],                                                                    'aemeath', RotationStepFlag.NORMAL),
    # ── 16: 爱弥斯 变奏入场 → 达妮娅 ──
    ('aemeath',  [('intro',)],                                                                  'denia',   RotationStepFlag.INTRO_SWITCH),
    # ── 17: 达妮娅 r2 → 爱弥斯 ──
    ('denia',    [('r',)],                                                                       'aemeath', RotationStepFlag.NORMAL),
    # ── 18: 爱弥斯 变奏入场 q r1 → 完成 ──
    ('aemeath',  [('intro',), ('q',), ('r',)],                                       None,      RotationStepFlag.INTRO_SWITCH),
]

CHAR_KEY_TO_INDEX = {
    'chisa': 0,
    'aemeath': 1,
    'denia': 2,
}

INDEX_TO_CHAR_KEY = {v: k for k, v in CHAR_KEY_TO_INDEX.items()}


class RotationState:
    """共享旋转状态。每个 combo 角色通过 self.task.rotation 访问。"""

    def __init__(self, sequence=None):
        self.seq = sequence or AIDA_QIAN_17S
        self.step_index = 0
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
        self.char_entry_tracker.clear()

    def is_done(self):
        return self.step_index >= len(self.seq)

    def reset(self):
        self.step_index = 0
        self.char_entry_tracker.clear()

    def get_next_step_for_char(self, char_key):
        """获取指定角色下一个要执行的步骤索引（从当前扫描）。"""
        for i in range(self.step_index, len(self.seq)):
            if self.seq[i][0] == char_key:
                return i
        return -1


# ComboTab 显示用序列 — 爱达千 17s 轴步骤描述
AIDEQIAN_SEQUENCE = [
    {"desc": "千咲入场, E声骸大招, 普攻3段", "actions": ["入场", "E", "声骸", "大招", "普攻×3"]},
    {"desc": "切爱弥斯, 普攻2段", "actions": ["变奏", "普攻×2"]},
    {"desc": "切达妮娅, E声骸大招, 普攻", "actions": ["变奏", "E", "声骸", "大招", "普攻×2"]},
    {"desc": "切爱弥斯, E, 普攻3段", "actions": ["变奏", "普攻×3", "E"]},
    {"desc": "切千咲, 普攻4段攒协奏", "actions": ["变奏", "普攻×4"]},
    {"desc": "切达妮娅, 普攻2段", "actions": ["变奏", "普攻×2"]},
    {"desc": "千咲开电锯, 普攻5段跳攻", "actions": ["变奏", "普攻×5", "跳A", "E(电锯)"]},
    {"desc": "达妮娅普攻4段, 声骸召机兵", "actions": ["普攻×4", "声骸(机兵)"]},
    {"desc": "机兵站场, 千咲普攻", "actions": ["机兵", "普攻×3"]},
    {"desc": "千咲电锯普攻2段", "actions": ["普攻×2"]},
    {"desc": "达妮娅E, 普攻", "actions": ["E", "普攻×3"]},
    {"desc": "千咲电锯普攻3段, 声骸召机兵", "actions": ["普攻×3", "声骸(机兵)"]},
    {"desc": "机兵站场, 达妮娅普攻E", "actions": ["机兵", "普攻×4", "E"]},
    {"desc": "达妮娅强化E, 普攻", "actions": ["E", "普攻×2"]},
    {"desc": "千咲电锯满协奏, 变奏爱弥斯", "actions": ["普攻×4", "变奏"]},
    {"desc": "爱弥斯变奏入场", "actions": ["变奏入场"]},
    {"desc": "达妮娅大招, 普攻2段", "actions": ["大招", "普攻×2"]},
    {"desc": "爱弥斯变奏入场, 声骸大招, 普攻收尾", "actions": ["变奏入场", "声骸", "大招", "普攻"]},
]
