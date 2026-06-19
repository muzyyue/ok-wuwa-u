from pathlib import Path

from ok import Logger

from src.combo.sequences import RotationState, get_default_rotation

logger = Logger.get_logger(__name__)


class ComboRotationConfig:
    """连招轮换配置 — 管理角色战斗逻辑的热切换。

    开启时，通过 CustomCharLoader 将 src/char_combo/ 中的连招优化版代码
    安装到 custom_chars 目录并启用，替换角色原本的 do_perform()。
    关闭时，卸载定制代码并清除缓存，角色恢复原始行为。
    """

    def __init__(self, task_config):
        if task_config is None:
            task_config = {}
        # 从全局配置读取连招轮换开关，默认关闭
        self._enabled = task_config.get('combo_rotation_enabled', False)
        # 同步 GUI 侧全局配置状态（桥接 ComboTab 开关与战斗逻辑）
        from src.combo.config import combo_config as _gui_config
        self._enabled = self._enabled or _gui_config.enabled
        self._was_enabled = self._enabled
        self.rotation_state = get_default_rotation()
        if self._enabled:
            self._install_all()

    @property
    def enabled(self):
        from src.combo.config import combo_config as _gui_config
        return self._enabled or _gui_config.enabled

    @enabled.setter
    def enabled(self, value):
        if value == self._enabled:
            return
        self._enabled = value
        # 同步到 GUI 侧全局配置
        from src.combo.config import combo_config as _gui_config
        _gui_config.enabled = value
        if value:
            self._install_all()   # 开启 → 安装连招代码
        else:
            self._uninstall_all() # 关闭 → 卸载连招代码

    def _install_all(self):
        """将所有支持连招轮换的角色代码安装到 CustomCharLoader 的 custom_chars 目录。"""
        combo_classes = _get_combo_char_classes()
        if not combo_classes:
            logger.warning('No combo char classes found to install')
            return
        from src.char.CustomCharLoader import save_custom_char_code
        combo_dir = Path(__file__).parent.parent / 'char_combo'
        if not combo_dir.exists():
            logger.warning(f'char_combo directory not found: {combo_dir}')
            return
        for char_name, cls in combo_classes.items():
            combo_file = combo_dir / f'{char_name}.py'
            if not combo_file.exists():
                logger.warning(f'Combo file not found: {combo_file}')
                continue
            try:
                code = combo_file.read_text(encoding='utf-8')
                save_custom_char_code(cls, code, use_custom=True)
                logger.info(f'Installed combo code for {char_name}')
            except Exception as e:
                logger.error(f'Failed to install combo code for {char_name}: {e}')
        self._was_enabled = True

    def _uninstall_all(self):
        """卸载所有角色的连招轮换代码，清除 CustomCharLoader 缓存以恢复原始类。"""
        from src.char.CustomCharLoader import remove_custom_char_code, clear_custom_char_cache
        combo_classes = _get_combo_char_classes()
        for char_name in combo_classes:
            try:
                remove_custom_char_code(char_name)
                logger.info(f'Removed combo code for {char_name}')
            except Exception as e:
                logger.error(f'Failed to remove combo code for {char_name}: {e}')
        clear_custom_char_cache()  # 确保缓存中的原始类也被清除
        self._was_enabled = False

    def reset_counters(self):
        """重置每场战斗的轮换计数器。"""
        self.rotation_state.reset()

    def on_combat_end(self):
        """战斗结束时调用，用于清理连招相关的战斗状态。"""
        self.reset_counters()


def _get_combo_char_classes():
    """扫描 char_combo/ 目录，返回 {类名: 原始类} 的映射表。

    只返回同时在 char_combo/ 中有 .py 文件且在 CharFactory 中注册过的角色。
    """
    combo_dir = Path(__file__).parent.parent / 'char_combo'
    if not combo_dir.exists():
        return {}
    combo_names = {f.stem for f in combo_dir.glob('*.py') if f.name != '__init__.py'}
    if not combo_names:
        return {}
    from src.char.CharFactory import char_dict
    result = {}
    for info in char_dict.values():
        cls = info.get('cls')
        if cls and cls.__name__ in combo_names:
            result[cls.__name__] = cls
    return result
