"""时停补偿 — 记录大招/击破等动画的冻结时间。

大招、击破等动画会暂停游戏内技能 CD 计时。
FreezeTracker 记录冻结起止时间，使 CD 计算能正确扣除冻结时长。

用法:
    FreezeTracker(self.task).wait(0.8)          # 等待 0.8s 并写入冻结
    FreezeTracker(self.task).begin().end()       # 手动控制起止
"""

import time


class FreezeTracker:
    """时停补偿跟踪器。

    记录游戏内冻结动画的起止时间，通过 task.add_freeze_duration()
    写入冻结时间线，使 time_elapsed_accounting_for_freeze 能正确扣除冻结部分。
    """

    def __init__(self, task):
        """Args:
            task: ok-script BaseTask 实例，需要 add_freeze_duration 方法。
        """
        self.task = task
        self._start = None

    def wait(self, duration: float):
        """等待 duration 秒，自动记录为冻结时间。

        Args:
            duration: 预估的动画冻结时长（秒）。
        """
        start = time.time()
        time.sleep(duration)
        self.task.add_freeze_duration(start, duration)

    def begin(self):
        """手动标记冻结起始时间（配合 end() 使用）。"""
        self._start = time.time()
        return self

    def end(self):
        """手动结束冻结记录，计算实际耗时并写入 task。"""
        if self._start is not None:
            elapsed = time.time() - self._start
            self.task.add_freeze_duration(self._start, elapsed)
            self._start = None
        return self

    def __enter__(self):
        """上下文管理器入口：begin()。"""
        return self.begin()

    def __exit__(self, *args):
        """上下文管理器出口：end()。"""
        self.end()
