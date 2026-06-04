from qfluentwidgets import FluentIcon

from ok import Logger, BaseScene

logger = Logger.get_logger(__name__)


class WWScene(BaseScene):
    """鸣潮场景管理器，缓存当前战斗/队伍/声骸强化等关键状态。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_team = None
        self._echo_enhance_btn = None
        self._in_combat = None
        self.cd_refreshed = False

    def reset(self):
        """重置所有缓存状态（脱战/换队时调用）。"""
        self._in_team = None
        self._echo_enhance_btn = None
        self._in_combat = None
        self.cd_refreshed = False

    def in_combat(self):
        """返回缓存的战斗状态，None 表示未检测。"""
        return self._in_combat

    def set_in_combat(self):
        """标记为战斗状态。"""
        self._in_combat = True
        return True

    def set_not_in_combat(self):
        """标记为非战斗状态。"""
        self._in_combat = False
        return False

    def in_team(self, fun):
        """惰性求值：仅在缓存为 None 时调用 fun() 检测队伍，后续复用缓存。"""
        if self._in_team is None:
            self._in_team = fun()
        return self._in_team

    def echo_enhance_btn(self, fun):
        """惰性求值：缓存声骸强化按钮的检测结果。"""
        if self._echo_enhance_btn is None:
            self._echo_enhance_btn = fun()
        return self._echo_enhance_btn
