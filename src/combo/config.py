"""合轴配置单例 — ComboRotationTab 使用的简单配置接口。"""


class _ComboConfig:
    """合轴配置单例，管理开关状态与轮次计数器。"""

    def __init__(self):
        self._enabled = False
        self._counters = {}

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if value == self._enabled:
            return
        self._enabled = value
        # 启用/禁用时重置计数器
        self.reset_counters()
        # 同步安装/卸载合轴角色代码（桥接 GUI 开关与战斗逻辑）
        if value:
            _install_combo_chars()
        else:
            _uninstall_combo_chars()

    def get_rotation_count(self, key: str) -> int:
        """获取指定角色的总轮次数。"""
        return self._counters.get(key, {}).get("total", 0)

    def get_current_rotation(self, key: str) -> int:
        """获取指定角色的当前轮次。"""
        return self._counters.get(key, {}).get("current", 0)

    def increment_rotation(self, key: str):
        """递增指定角色的轮次计数。"""
        if key not in self._counters:
            self._counters[key] = {"current": 0, "total": 10}
        self._counters[key]["current"] = (self._counters[key]["current"] + 1) % self._counters[key]["total"]
        self._counters[key]["total"] += 1

    def reset_counters(self):
        """重置所有角色的轮次计数。"""
        for key in list(self._counters.keys()):
            self._counters[key] = {"current": 0, "total": 10}


# 全局单例
combo_config = _ComboConfig()


def _get_combo_char_classes():
    """扫描 char_combo/ 目录，返回 {类名: 原始类} 的映射表。
    
    只返回同时在 char_combo/ 中有 .py 文件且在 CharFactory 中注册过的角色。
    从 combo_config 复用此方法以保持一致性。
    """
    from src.combo.combo_config import _get_combo_char_classes as _orig
    return _orig()


def _install_combo_chars():
    """安装合轴角色定制代码到 CustomCharLoader。"""
    from pathlib import Path
    from src.char.CustomCharLoader import save_custom_char_code

    combo_classes = _get_combo_char_classes()
    if not combo_classes:
        return
    combo_dir = Path(__file__).parent.parent / 'char_combo'
    for char_name, cls in combo_classes.items():
        combo_file = combo_dir / f'{char_name}.py'
        if not combo_file.exists():
            continue
        try:
            code = combo_file.read_text(encoding='utf-8')
            save_custom_char_code(cls, code, use_custom=True)
        except Exception:
            pass


def _uninstall_combo_chars():
    """卸载合轴角色定制代码，恢复原始角色逻辑。"""
    from src.char.CustomCharLoader import remove_custom_char_code, clear_custom_char_cache

    combo_classes = _get_combo_char_classes()
    for char_name in combo_classes:
        try:
            remove_custom_char_code(char_name)
        except Exception:
            pass
    clear_custom_char_cache()
