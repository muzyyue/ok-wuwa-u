"""
角色代码热替换模块 — 允许在不重启程序的情况下动态替换角色的战斗逻辑。

工作流程:
  1. 用户编写定制版角色代码，保存在 {config_folder}/custom_chars/<ClassName>.py
  2. CharFactory 创建角色时调用 load_custom_char_class() 检查是否启用定制版
  3. 如果启用，则从文件动态加载替代类，代替源码中的原始 BaseChar 子类
  4. 禁用后自动清除缓存，恢复原始行为

此机制被 src/combo/combo_config.py 用于安装/卸载连招轮换版本的字符实现。
"""
import importlib.util
import inspect
import json
from pathlib import Path

from ok import Logger
from ok.util.config import Config

logger = Logger.get_logger(__name__)

# 定制角色代码的存储目录名和模式配置文件
CUSTOM_CHAR_FOLDER = "custom_chars"
CUSTOM_CHAR_MODES_FILE = "custom_chars.json"

# 类缓存: { "ClassName": (mtime_ns, size, class_ref) }
# 通过文件修改时间和大小判断是否需要重新加载
_custom_class_cache = {}


def get_custom_char_folder(create=False):
    """获取存放定制角色代码的目录路径。

    Args:
        create: 如果目录不存在则创建。

    Returns:
        Path: custom_chars 目录的绝对路径。
    """
    folder = Path(Config.config_folder) / CUSTOM_CHAR_FOLDER
    if create:
        folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_custom_char_modes_file():
    """获取记录各角色定制模式开关状态的 JSON 文件路径。"""
    return get_custom_char_folder(create=True) / CUSTOM_CHAR_MODES_FILE


def get_custom_char_file(char_cls_or_name):
    """获取指定角色的定制代码文件路径。"""
    class_name = _get_class_name(char_cls_or_name)
    return get_custom_char_folder(create=True) / f"{class_name}.py"


def _get_class_name(char_cls_or_name):
    """统一处理传入的是类对象还是字符串类名。"""
    if isinstance(char_cls_or_name, str):
        return char_cls_or_name
    return char_cls_or_name.__name__


def load_custom_char_modes():
    """从 JSON 文件加载所有角色的定制模式开关状态。"""
    path = get_custom_char_modes_file()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"load custom char modes failed: {e}")
        return {}
    return data if isinstance(data, dict) else {}


def save_custom_char_modes(modes):
    """将定制模式开关状态保存到 JSON 文件。"""
    path = get_custom_char_modes_file()
    path.write_text(json.dumps(modes, ensure_ascii=False, indent=2), encoding="utf-8")


def is_custom_char_enabled(char_cls_or_name):
    """检查指定角色是否开启了定制模式。"""
    class_name = _get_class_name(char_cls_or_name)
    return bool(load_custom_char_modes().get(class_name, {}).get("use_custom"))


def set_custom_char_enabled(char_cls_or_name, enabled):
    """设置指定角色的定制模式开关状态。"""
    class_name = _get_class_name(char_cls_or_name)
    modes = load_custom_char_modes()
    modes.setdefault(class_name, {})["use_custom"] = bool(enabled)
    save_custom_char_modes(modes)
    clear_custom_char_cache(class_name)


def has_custom_char_code(char_cls_or_name):
    """检查指定角色是否有定制代码文件存在。"""
    return get_custom_char_file(char_cls_or_name).exists()


def remove_custom_char_code(char_cls_or_name):
    """删除指定角色的定制代码文件并关闭定制模式。"""
    path = get_custom_char_file(char_cls_or_name)
    path.unlink(missing_ok=True)
    set_custom_char_enabled(char_cls_or_name, False)
    return path


def read_builtin_char_code(char_cls):
    """读取角色源码中的原始 Python 代码。"""
    path = inspect.getsourcefile(char_cls)
    if not path:
        raise RuntimeError(f"Cannot find source file for {char_cls.__name__}")
    return Path(path).read_text(encoding="utf-8")


def read_custom_or_builtin_char_code(char_cls):
    """优先读取定制代码，不存在则回退到源码。"""
    path = get_custom_char_file(char_cls)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return read_builtin_char_code(char_cls)


def save_custom_char_code(char_cls, code, use_custom=True):
    """保存并应用角色的定制代码。

    先将代码写入 custom_chars/<ClassName>.py，然后尝试编译并加载。
    如果加载失败则自动回滚到上一份有效代码（或删除文件）。

    Args:
        char_cls: 原始角色类。
        code: 定制版 Python 源码字符串。
        use_custom: 写入后是否立即启用定制模式。

    Returns:
        Path: 写入的定制代码文件路径。
    """
    path = get_custom_char_file(char_cls)
    old_code = path.read_text(encoding="utf-8") if path.exists() else None
    old_enabled = is_custom_char_enabled(char_cls)
    compile(code, str(path), "exec")  # 预编译检查语法
    try:
        path.write_text(code, encoding="utf-8")
        clear_custom_char_cache(char_cls)
        if use_custom:
            _load_custom_char_class_from_file(char_cls, path)
        set_custom_char_enabled(char_cls, use_custom)
    except Exception:
        # 写入或加载失败，回滚到旧状态
        if old_code is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(old_code, encoding="utf-8")
        set_custom_char_enabled(char_cls, old_enabled)
        raise
    return path


def clear_custom_char_cache(char_cls_or_name=None):
    """清除定制类缓存。

    不传参时清除全部缓存；传入类名/类对象时只清除对应的一个缓存条目。
    """
    if char_cls_or_name is None:
        _custom_class_cache.clear()
    else:
        _custom_class_cache.pop(_get_class_name(char_cls_or_name), None)


def load_custom_char_class(char_cls):
    """如果开启了定制模式且存在定制代码，返回定制类；否则返回原始类。

    这是 CharFactory 调用的入口函数，用于决定使用哪个类创建角色实例。
    """
    if not is_custom_char_enabled(char_cls):
        return char_cls

    path = get_custom_char_file(char_cls)
    if not path.exists():
        return char_cls

    try:
        return _load_custom_char_class_from_file(char_cls, path)
    except Exception as e:
        logger.error(f"load custom char class failed for {char_cls.__name__}: {e}")
        clear_custom_char_cache(char_cls)
        return char_cls


def _load_custom_char_class_from_file(char_cls, path):
    """从定制代码文件中动态加载角色类。

    使用 importlib 将 .py 文件作为独立模块加载，提取与原始类同名的类。
    要求定制类必须继承 BaseChar。

    Returns:
        type: 动态加载的定制角色类。
    """
    cache_key = char_cls.__name__
    stat = path.stat()
    cached = _custom_class_cache.get(cache_key)
    if cached and cached[0] == stat.st_mtime_ns and cached[1] == stat.st_size:
        return cached[2]  # 缓存命中，直接返回

    module_name = f"ok_ww_custom_char_{char_cls.__name__}_{stat.st_mtime_ns}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load custom char module: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    custom_cls = getattr(module, char_cls.__name__, None)
    if custom_cls is None:
        raise RuntimeError(f"Custom code must define class {char_cls.__name__}")

    from src.char.BaseChar import BaseChar
    if not isinstance(custom_cls, type) or not issubclass(custom_cls, BaseChar):
        raise RuntimeError(f"{char_cls.__name__} must inherit BaseChar")

    _custom_class_cache[cache_key] = (stat.st_mtime_ns, stat.st_size, custom_cls)
    return custom_cls
