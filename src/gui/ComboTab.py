"""角色合轴配置选项卡 - GUI 界面中管理合轴序列。"""
from PySide6.QtCore import QEasingCurve, QVariantAnimation
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import BodyLabel, FluentIcon, PushButton, ExpandSettingCard, SwitchButton

from ok.gui.widget.CustomTab import CustomTab
from src.combo.config import combo_config
from src.combo.sequences import AIDEQIAN_SEQUENCE


def _patch_expand_card(card: ExpandSettingCard):
    """修复 ExpandSettingCard 收起动画失效的问题。

    根因：setWidgetResizable(True) 导致展开后 scrollArea 的 verticalScrollBar().maximum() = 0，
    原始收起动画 setEndValue(maximum) 变为 0→0，完全无效。

    修复：用 QVariantAnimation 手动动画化 setFixedHeight，绕过有缺陷的滚动条机制。
    """
    card._content_h = 0  # type: ignore[attr-defined]
    card._height_ani = QVariantAnimation(card)  # type: ignore[attr-defined]
    card._height_ani.setEasingCurve(QEasingCurve.OutQuad)
    card._height_ani.setDuration(200)
    card._height_ani.valueChanged.connect(lambda v: card.setFixedHeight(int(v)))  # type: ignore[attr-defined]

    def patched_setExpand(isExpand: bool):
        if card.isExpand == isExpand:
            return

        card.isExpand = isExpand
        card.setProperty('isExpand', isExpand)
        card.setStyle(card.style())

        if isExpand:
            h = card.viewLayout.sizeHint().height()
            card._content_h = h  # type: ignore[attr-defined]
            card._height_ani.setStartValue(card.height())  # type: ignore[attr-defined]
            card._height_ani.setEndValue(card.card.height() + h)
        else:
            h = getattr(card, '_content_h', 0)
            if h <= 0:
                h = card.viewLayout.sizeHint().height()
            card._height_ani.setStartValue(card.height())  # type: ignore[attr-defined]
            card._height_ani.setEndValue(card.card.height())

        card._height_ani.start()  # type: ignore[attr-defined]
        card.card.expandButton.setExpand(isExpand)

    card.setExpand = patched_setExpand  # type: ignore[method-assign]


class ComboRotationTab(CustomTab):
    """角色合轴配置选项卡。"""

    def __init__(self):
        super().__init__()
        self._rotation_labels = {}
        self._build_ui()

    @property
    def name(self):
        return self.tr("Character Rotation")

    @property
    def icon(self):
        return FluentIcon.CALORIES

    @property
    def position(self):
        from qfluentwidgets import NavigationItemPosition
        return NavigationItemPosition.TOP

    def _build_ui(self):
        # 主卡片：开关 + 展开内容
        self._main_card = ExpandSettingCard(
            FluentIcon.CALORIES,
            self.tr("Aideqian 17s Rotation"),
            self.tr("Execute predefined rotation sequence for Aideqian 17s combo"),
            self.view,
        )

        # 开关只控制功能，不控制显示
        self._switch = SwitchButton()
        self._switch.setChecked(combo_config.enabled)
        self._switch.checkedChanged.connect(self._on_enabled_changed)
        self._main_card.addWidget(self._switch)

        # 角色序列直接放在主卡片的展开区域内
        self._add_char_section(self.tr("Aideqian 17s"), AIDEQIAN_SEQUENCE, "aideqian")

        self._main_card.viewLayout.addStretch(1)

        # 底部操作
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch(1)
        self.reset_btn = PushButton(FluentIcon.SYNC, self.tr("Reset Config"))
        self.reset_btn.clicked.connect(self._on_reset)
        btn_layout.addWidget(self.reset_btn)
        self._main_card.viewLayout.addWidget(btn_container)

        _patch_expand_card(self._main_card)
        self.add_widget(self._main_card)

    def _add_char_section(self, char_name, sequence, config_key):
        """在主卡片展开区域内添加角色序列段落。"""
        total = combo_config.get_rotation_count(config_key)
        rotation = combo_config.get_current_rotation(config_key)

        # 角色标题行（含轮次计数）
        title = BodyLabel(self.tr("{} Rotation Sequence  {}/{}").format(char_name, rotation, total))
        title.setStyleSheet("font-weight: bold;")
        self._main_card.viewLayout.addWidget(title)

        # 步骤列表
        for i, step in enumerate(sequence):
            step_desc = step.get("desc", "")
            actions = ", ".join(step.get("actions", []))
            label = BodyLabel(f"  {i}: [{actions}] {step_desc}")
            label.setStyleSheet("color: #888;")
            self._main_card.viewLayout.addWidget(label)

        self._rotation_labels[config_key] = (title, char_name)

    def _on_enabled_changed(self, checked: bool):
        """合轴开关切换时，只更新功能状态。"""
        combo_config.enabled = checked

    def _on_reset(self):
        combo_config.reset_counters()
        self._refresh_rotation_labels()
        self.logger.info("Combo rotation counters reset")

    def _refresh_rotation_labels(self):
        for key, (title_label, char_name) in self._rotation_labels.items():
            rotation = combo_config.get_current_rotation(key)
            total = combo_config.get_rotation_count(key)
            title_label.setText(self.tr("{} Rotation Sequence  {}/{}").format(char_name, rotation, total))

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_rotation_labels()
