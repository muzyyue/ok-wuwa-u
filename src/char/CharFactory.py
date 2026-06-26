from src.Labels import Labels
from src.char.Aemeath import Aemeath
from src.char.Augusta import Augusta
from src.char.Baizhi import Baizhi
from src.char.BaseChar import BaseChar, CharType, Elements, get_default_buff_time
from src.char.Brant import Brant
from src.char.Calcharo import Calcharo
from src.char.Camellya import Camellya
from src.char.Cantarella import Cantarella
from src.char.Carlotta import Carlotta
from src.char.Cartethyia import Cartethyia
from src.char.Changli import Changli
from src.char.Chisa import Chisa
from src.char.Chixia import Chixia
from src.char.Ciaccona import Ciaccona
from src.char.Danjin import Danjin
from src.char.Denia import Denia
from src.char.Douling import Douling
from src.char.Encore import Encore
from src.char.Galbrena import Galbrena
from src.char.HavocRover import HavocRover
from src.char.Hiyuki import Hiyuki
from src.char.Iuno import Iuno
from src.char.Jianxin import Jianxin
from src.char.Jinhsi import Jinhsi
from src.char.Jiyan import Jiyan
from src.char.Linnai import Linnai
from src.char.Lucilla import Lucilla
from src.char.Lucy import Lucy
from src.char.Luhesi import Luhesi
from src.char.Lupa import Lupa
from src.char.Mortefi import Mortefi
from src.char.Mornye import Mornye
from src.char.Phoebe import Phoebe
from src.char.Phrolova import Phrolova
from src.char.Qiuyuan import Qiuyuan
from src.char.Rebecca import Rebecca
from src.char.Roccia import Roccia
from src.char.Sanhua import Sanhua
from src.char.ShoreKeeper import ShoreKeeper
from src.char.Taoqi import Taoqi
from src.char.Verina import Verina
from src.char.Xiangliyao import Xiangliyao
from src.char.Xigelika import Xigelika
from src.char.Yinlin import Yinlin
from src.char.Youhu import Youhu
from src.char.Yuanwu import Yuanwu
from src.char.Zani import Zani
from src.char.Zhezhi import Zhezhi
from src.char.CustomCharLoader import load_custom_char_class

# ============================================================
# 角色注册表 — 定义所有可用角色的类、定位、属性和协奏检索引擎。
# 添加新角色时在此处注册，系统会自动完成创建、配置和热更新。
# ============================================================
_char_dict_raw = {
    Labels.char_yinlin: {'cls': Yinlin, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ELECTRIC},
    Labels.char_verina: {'cls': Verina, 'char_type': CharType.HEALER,
                         'ring_index': Elements.SPECTRO},
    Labels.char_shorekeeper: {'cls': ShoreKeeper, 'char_type': CharType.HEALER,
                              'ring_index': Elements.SPECTRO},
    Labels.char_taoqi: {'cls': Taoqi, 'char_type': CharType.HEALER,
                        'ring_index': Elements.HAVOC},
    (Labels.char_rover, Labels.char_rover_male): {'cls': HavocRover, 'char_type': CharType.MAIN_DPS},
    Labels.char_encore: {'cls': Encore, 'char_type': CharType.MAIN_DPS,
                         'ring_index': Elements.FIRE},
    Labels.char_jianxin: {'cls': Jianxin, 'char_type': CharType.HEALER,
                          'ring_index': Elements.WIND},
    (Labels.char_sanhua, Labels.char_sanhua2): {'cls': Sanhua, 'char_type': CharType.SUB_DPS,
                                                'ring_index': Elements.ICE},
    (Labels.char_jinhsi, Labels.char_jinhsi2): {'cls': Jinhsi, 'char_type': CharType.MAIN_DPS,
                                                'ring_index': Elements.SPECTRO},
    Labels.char_yuanwu: {'cls': Yuanwu, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ELECTRIC},
    (Labels.chang_changli, Labels.char_changli2): {'cls': Changli, 'char_type': CharType.MAIN_DPS,
                                                   'ring_index': Elements.FIRE},
    Labels.char_chixia: {'cls': Chixia, 'char_type': CharType.MAIN_DPS,
                         'ring_index': Elements.FIRE},
    Labels.char_danjin: {'cls': Danjin, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.HAVOC},
    Labels.char_baizhi: {'cls': Baizhi, 'char_type': CharType.HEALER,
                         'ring_index': Elements.ICE},
    Labels.char_calcharo: {'cls': Calcharo, 'char_type': CharType.MAIN_DPS,
                           'ring_index': Elements.ELECTRIC},
    Labels.char_jiyan: {'cls': Jiyan, 'char_type': CharType.MAIN_DPS,
                        'ring_index': Elements.WIND},
    Labels.char_mortefi: {'cls': Mortefi, 'char_type': CharType.SUB_DPS,
                          'ring_index': Elements.FIRE},
    Labels.char_zhezhi: {'cls': Zhezhi, 'char_type': CharType.SUB_DPS,
                         'ring_index': Elements.ICE},
    Labels.char_xiangliyao: {'cls': Xiangliyao, 'char_type': CharType.MAIN_DPS,
                             'ring_index': Elements.ELECTRIC},
    Labels.char_camellya: {'cls': Camellya, 'char_type': CharType.MAIN_DPS,
                           'ring_index': Elements.HAVOC},
    Labels.char_youhu: {'cls': Youhu, 'char_type': CharType.HEALER,
                        'ring_index': Elements.ICE},
    (Labels.char_carlotta, Labels.char_carlotta2): {'cls': Carlotta, 'char_type': CharType.MAIN_DPS,
                                                    'ring_index': Elements.ICE},
    Labels.char_roccia: {'cls': Roccia, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.HAVOC},
    Labels.char_phoebe: {'cls': Phoebe, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.SPECTRO},
    Labels.char_brant: {'cls': Brant, 'char_type': CharType.HEALER, 'ring_index': Elements.FIRE},
    Labels.char_cantarella: {'cls': Cantarella, 'char_type': CharType.HEALER, 'ring_index': Elements.HAVOC},
    (Labels.char_zani, Labels.char_zani2): {'cls': Zani, 'char_type': CharType.MAIN_DPS,
                                            'ring_index': Elements.SPECTRO},
    Labels.char_ciaccona: {'cls': Ciaccona, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.WIND},
    Labels.char_cartethyia: {'cls': Cartethyia, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.WIND},
    Labels.char_lupa: {'cls': Lupa, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.FIRE},
    Labels.char_phrolova: {'cls': Phrolova, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.HAVOC},
    Labels.Augusta: {'cls': Augusta, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.ELECTRIC},
    Labels.char_iuno: {'cls': Iuno, 'char_type': CharType.SUB_DPS,
                       'ring_index': Elements.WIND},
    Labels.char_galbrena: {'cls': Galbrena, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.FIRE},
    Labels.char_chouyuan: {'cls': Qiuyuan, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.WIND},
    Labels.char_chisa: {'cls': Chisa, 'char_type': CharType.HEALER, 'buff_time': 12,
                        'ring_index': Elements.HAVOC},
    Labels.char_denia: {'cls': Denia, 'char_type': CharType.SUB_DPS, 'buff_time': 14, 'ring_index': Elements.FIRE},
    Labels.char_douling: {'cls': Douling, 'char_type': CharType.HEALER, 'ring_index': Elements.ELECTRIC},
    Labels.char_linnai: {'cls': Linnai, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.SPECTRO},
    (Labels.char_moning, Labels.char_moning_new): {'cls': Mornye, 'char_type': CharType.HEALER,
                                                   'ring_index': Elements.FIRE},
    Labels.char_aemeath: {'cls': Aemeath, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.FIRE},
    Labels.char_xigelika: {'cls': Xigelika, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.WIND},
    Labels.char_luhesi: {'cls': Luhesi, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.SPECTRO},
    Labels.char_hiyuki: {'cls': Hiyuki, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.ICE},
    Labels.char_lucilla: {'cls': Lucilla, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.ICE,
                          'target_box_short_combat_check': True},
    Labels.char_lucy: {'cls': Lucy, 'char_type': CharType.MAIN_DPS, 'ring_index': Elements.SPECTRO},
    Labels.char_rebecca: {'cls': Rebecca, 'char_type': CharType.SUB_DPS, 'ring_index': Elements.ELECTRIC},
}

# 构建最终的角色字典，处理多标签映射（如男女漂泊者共用同一类）并填充默认buff_time
char_dict = {}
for keys, value in _char_dict_raw.items():
    value = dict(value)
    value.setdefault('buff_time', get_default_buff_time(value.get('char_type', CharType.MAIN_DPS)))
    if isinstance(keys, tuple):
        for key in keys:
            char_dict[key] = value
    else:
        char_dict[keys] = value

char_names = char_dict.keys()  # 所有已注册的角色名称列表


def _get_char_type(task, info):
    """从注册信息中提取角色定位（主C/副C/奶妈），默认主输出。"""
    return info.get('char_type', CharType.MAIN_DPS)


def _get_buff_time(task, info):
    """从注册信息中提取延奏buff持续时间，未指定则按定位取默认值。"""
    char_type = _get_char_type(task, info)
    return info.get('buff_time', get_default_buff_time(char_type))


def _apply_char_config(task, char, info):
    """将注册表中的定位和buff时间配置应用到角色实例上。"""
    if char and info:
        char.set_char_type(_get_char_type(task, info))
        char.set_buff_time(_get_buff_time(task, info))
        char.target_box_short_combat_check = info.get('target_box_short_combat_check', False)
    return char


def get_char_by_pos(task, box, index, old_char):
    """通过图像识别定位并创建/复用角色实例。

    流程:
      1. 如果 old_char 置信度高，优先在附近查找同名角色复用实例。
      2. 若类型因 CustomCharLoader 热替换而变化，则创建新实例。
      3. 否则用 find_best_match_in_box 在全角色范围内匹配。
      4. 实在找不到时返回旧实例或兜底的 BaseChar。

    Args:
        task: BaseCombatTask 实例。
        box: 角色头像UI区域坐标。
        index: 队伍位置 (0/1/2)。
        old_char: 上一帧该位置的角色对象，可能复用。

    Returns:
        BaseChar: 角色实例（已配置定位和buff时间）。
    """
    highest_confidence = 0
    info = None
    name = "unknown"
    char = None
    if old_char and old_char.confidence > 0.92 and old_char.char_name in char_names:
        char = task.find_one(old_char.char_name, box=box, threshold=0.6)
        if char:
            info = char_dict.get(old_char.char_name)
            cls = load_custom_char_class(info.get('cls'))
            if type(old_char) is not cls:
                return _apply_char_config(task, cls(task, index, char_name=old_char.char_name,
                                                    confidence=char.confidence,
                                                    ring_index=info.get('ring_index', -1),
                                                    char_type=_get_char_type(task, info),
                                                    buff_time=_get_buff_time(task, info)), info)
            _apply_char_config(task, old_char, info)
            return old_char
    if not char:
        char = task.find_best_match_in_box(box, char_names, threshold=0.6)
        if char:
            info = char_dict.get(char.name)
            name = char.name
            cls = load_custom_char_class(info.get('cls'))
            return _apply_char_config(task, cls(task, index, char_name=name, confidence=char.confidence,
                                                ring_index=info.get('ring_index', -1),
                                                char_type=_get_char_type(task, info),
                                                buff_time=_get_buff_time(task, info)), info)
    task.log_info(f'could not find char {index} {info} {highest_confidence}')
    if old_char:
        return old_char  # 保持上一帧的角色不变，避免空指针
    if task.debug:
        task.screenshot(f'could not find char {index}')
    return BaseChar(task, index, char_name=name)  # 创建兜底实例


def is_float(s):
    """判断字符串是否可以转为浮点数（用于配置项校验）。"""
    try:
        float(s)
        return True
    except ValueError:
        return False
