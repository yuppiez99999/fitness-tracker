"""
AI 教练页面 (v7.0 模块化拆分)
基于 Lzheng-fitness 知识库的增肌规划: 分层评估/周期生成/训练复盘/停训接回/短版训练。
"""

import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .constants import COLORS, button_style, outline_button_style, textedit_style
from .shell import apply_page_layout, apply_surface, make_page_heading

# AI 教练引擎 — 软依赖, 缺失时降级 (原 fitness_modules.py L2816-2826)
try:
    from ai_coach_engine import (
        LEVEL_DESC,
        AthleteProfile,
        TrainingLog,
        assess_overall_level,
        export_cycle_to_markdown,
        generate_return_plan,
        generate_short_version,
        generate_strength_cycle,
        load_profile,
        load_reviews,
        review_training,
        save_cycle,
        save_profile,
        save_review,
    )

    AI_COACH_AVAILABLE = True
except Exception:
    AI_COACH_AVAILABLE = False


class AICoachPage(QWidget):
    """AI 教练页面 — 5 个子功能: 分层评估/周期生成/训练复盘/停训接回/短版训练"""

    def __init__(self):
        super().__init__()
        self.profile = load_profile() or AthleteProfile()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        apply_page_layout(layout)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        if not AI_COACH_AVAILABLE:
            lbl = QLabel("AI 教练引擎未加载 (ai_coach_engine.py)")
            lbl.setStyleSheet(f"color: {COLORS['danger']}; font-size: 14px;")
            layout.addWidget(lbl)
            return

        layout.addWidget(make_page_heading("AI 教练", "P0–L3 分层 · 力量周期 · 复盘 · 停训接回 · 短版训练"))

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_profile_tab(), "建档与分层")
        self.tabs.addTab(self._build_cycle_tab(), "力量周期")
        self.tabs.addTab(self._build_review_tab(), "训练复盘")
        self.tabs.addTab(self._build_return_tab(), "停训接回")
        self.tabs.addTab(self._build_short_tab(), "短版训练")

    def _build_profile_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        w = QWidget()
        w.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(12)

        form_card = QFrame()
        apply_surface(form_card)
        form = QGridLayout(form_card)
        form.setContentsMargins(18, 16, 18, 16)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)

        self.in_name = QLineEdit(self.profile.name)
        self.in_age = QSpinBox()
        self.in_age.setRange(10, 80)
        self.in_age.setValue(self.profile.age or 30)
        self.in_height = QDoubleSpinBox()
        self.in_height.setRange(100, 250)
        self.in_height.setValue(self.profile.height_cm or 175)
        self.in_weight = QDoubleSpinBox()
        self.in_weight.setRange(30, 200)
        self.in_weight.setValue(self.profile.weight_kg or 67)
        self.in_bf = QDoubleSpinBox()
        self.in_bf.setRange(3, 60)
        self.in_bf.setValue(self.profile.body_fat_pct or 17)
        self.in_years = QDoubleSpinBox()
        self.in_years.setRange(0, 30)
        self.in_years.setSingleStep(0.5)
        self.in_years.setValue(self.profile.training_years or 0)
        self.in_sessions = QSpinBox()
        self.in_sessions.setRange(1, 7)
        self.in_sessions.setValue(self.profile.weekly_sessions or 4)
        self.in_minutes = QSpinBox()
        self.in_minutes.setRange(10, 180)
        self.in_minutes.setValue(self.profile.session_minutes or 60)
        self.in_goal = QComboBox()
        self.in_goal.addItems(["增肌", "减脂", "力量", "综合"])
        self.in_goal.setCurrentText(self.profile.goal or "增肌")

        pairs = [
            ("姓名", self.in_name),
            ("年龄", self.in_age),
            ("身高(cm)", self.in_height),
            ("体重(kg)", self.in_weight),
            ("体脂率(%)", self.in_bf),
            ("训练年限(年)", self.in_years),
            ("每周训练次数", self.in_sessions),
            ("单次时长(分钟)", self.in_minutes),
            ("主要目标", self.in_goal),
        ]
        for i, (label, widget) in enumerate(pairs):
            r, c = divmod(i, 2)
            lab = QLabel(label)
            lab.setStyleSheet(f"color: {COLORS['subtext']}; background: transparent;")
            form.addWidget(lab, r, c * 2)
            form.addWidget(widget, r, c * 2 + 1)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)
        outer.addWidget(form_card)

        btn_save = QPushButton("保存建档并评估分层")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet(button_style(COLORS["primary"], padding="9px 28px", font_size=12))
        btn_save.setMinimumWidth(240)
        btn_save.clicked.connect(self._save_profile)
        outer.addWidget(btn_save, 0, Qt.AlignLeft)

        self.lbl_level_result = QTextEdit()
        self.lbl_level_result.setReadOnly(True)
        self.lbl_level_result.setMinimumHeight(240)
        self.lbl_level_result.setStyleSheet(textedit_style())
        outer.addWidget(self.lbl_level_result, 1)

        scroll.setWidget(w)
        return scroll

    def _save_profile(self):
        self.profile.name = self.in_name.text()
        self.profile.age = self.in_age.value()
        self.profile.height_cm = self.in_height.value()
        self.profile.weight_kg = self.in_weight.value()
        self.profile.body_fat_pct = self.in_bf.value()
        self.profile.training_years = self.in_years.value()
        self.profile.weekly_sessions = self.in_sessions.value()
        self.profile.session_minutes = self.in_minutes.value()
        self.profile.goal = self.in_goal.currentText()
        save_profile(self.profile)

        level = assess_overall_level(self.profile)
        html = f"<h3>整体训练等级: {level}</h3><p>{LEVEL_DESC[level]}</p>"
        html += "<h4>建议:</h4><ul>"
        if level == "P0":
            html += "<li>首要目标: 安全、可重复、建立基准</li><li>使用固定器械或支撑动作</li><li>每次训练记录重量和感觉</li>"
        elif level == "L1":
            html += "<li>可逐次或隔次推进</li><li>使用线性或双重渐进</li><li>一次只改变一个主要变量</li>"
        elif level == "L2":
            html += "<li>按周管理训练量、强度和恢复</li><li>可使用多周周期</li><li>关注疲劳管理</li>"
        else:
            html += "<li>按阶段规划进步</li><li>需要更高专项性</li><li>使用完整积累→强度→实现→减量周期</li>"
        html += "</ul>"
        self.lbl_level_result.setHtml(html)

    # ─── 子页2: 力量周期生成 ───
    def _build_cycle_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("动作:"))
        self.in_cycle_move = QComboBox()
        self.in_cycle_move.addItems(["卧推", "深蹲", "硬拉", "推举", "引体向上", "划船"])
        ctrl.addWidget(self.in_cycle_move)

        ctrl.addWidget(QLabel("当前1RM(kg):"))
        self.in_cur_1rm = QDoubleSpinBox()
        self.in_cur_1rm.setRange(10, 500)
        self.in_cur_1rm.setValue(80)
        ctrl.addWidget(self.in_cur_1rm)

        ctrl.addWidget(QLabel("目标1RM(kg):"))
        self.in_tgt_1rm = QDoubleSpinBox()
        self.in_tgt_1rm.setRange(10, 500)
        self.in_tgt_1rm.setValue(90)
        ctrl.addWidget(self.in_tgt_1rm)

        ctrl.addWidget(QLabel("每周暴露:"))
        self.in_exposures = QSpinBox()
        self.in_exposures.setRange(1, 4)
        self.in_exposures.setValue(2)
        ctrl.addWidget(self.in_exposures)
        layout.addLayout(ctrl)

        btn = QPushButton("生成力量周期")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(button_style(COLORS["success"], padding="9px 30px", font_size=12))
        btn.setMinimumHeight(38)
        btn.setMaximumWidth(360)
        btn.clicked.connect(self._gen_cycle)
        layout.addWidget(btn, 0, Qt.AlignHCenter)

        self.cycle_result = QTextEdit()
        self.cycle_result.setReadOnly(True)
        layout.addWidget(self.cycle_result)
        return w

    def _gen_cycle(self):
        move = self.in_cycle_move.currentText()
        cur = self.in_cur_1rm.value()
        tgt = self.in_tgt_1rm.value()
        exp = self.in_exposures.value()

        cycle = generate_strength_cycle(move, cur, tgt, exp)
        save_cycle(cycle)
        md_path = export_cycle_to_markdown(cycle)

        html = f"<h3>{move} 力量周期 — {cycle.weeks}周</h3>"
        html += f"<p>当前1RM: {cur}kg → 目标1RM: {tgt}kg</p>"
        html += "<h4>阶段分布</h4><ul>"
        for phase, n in cycle.phase_distribution.items():
            html += f"<li><b>{phase}</b>: {n}周</li>"
        html += '</ul><h4>每周安排</h4><table border="1" cellpadding="4" style="border-collapse:collapse;">'
        html += "<tr><th>周</th><th>阶段</th><th>顶组</th><th>回退组</th></tr>"
        for d in cycle.days:
            top = d.sets[0] if d.sets else None
            back = d.sets[1] if len(d.sets) > 1 else None
            top_s = f"{top.weight}kg {top.sets}×{top.reps}" if top else "—"
            back_s = f"{back.weight}kg {back.sets}×{back.reps}" if back else "—"
            html += f"<tr><td>{d.week}</td><td>{d.phase}</td><td>{top_s}</td><td>{back_s}</td></tr>"
        html += f'</table><p style="color:{COLORS["success"]};">✓ 已保存至: {md_path}</p>'
        self.cycle_result.setHtml(html)

    # ─── 子页3: 训练复盘 ───
    def _build_review_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("动作:"))
        self.in_rev_move = QLineEdit("卧推")
        ctrl.addWidget(self.in_rev_move)
        ctrl.addWidget(QLabel("重量(kg):"))
        self.in_rev_w = QDoubleSpinBox()
        self.in_rev_w.setRange(0, 500)
        self.in_rev_w.setValue(60)
        ctrl.addWidget(self.in_rev_w)
        ctrl.addWidget(QLabel("次数:"))
        self.in_rev_reps = QSpinBox()
        self.in_rev_reps.setRange(1, 30)
        self.in_rev_reps.setValue(8)
        ctrl.addWidget(self.in_rev_reps)
        ctrl.addWidget(QLabel("组数:"))
        self.in_rev_sets = QSpinBox()
        self.in_rev_sets.setRange(1, 10)
        self.in_rev_sets.setValue(4)
        ctrl.addWidget(self.in_rev_sets)
        ctrl.addWidget(QLabel("RPE:"))
        self.in_rev_rpe = QDoubleSpinBox()
        self.in_rev_rpe.setRange(1, 10)
        self.in_rev_rpe.setSingleStep(0.5)
        self.in_rev_rpe.setValue(7.5)
        ctrl.addWidget(self.in_rev_rpe)
        layout.addLayout(ctrl)

        btn = QPushButton("复盘并生成下一次处方")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(button_style(COLORS["primary"], padding="9px 30px", font_size=12))
        btn.setMinimumHeight(38)
        btn.setMaximumWidth(360)
        btn.clicked.connect(self._do_review)
        layout.addWidget(btn, 0, Qt.AlignHCenter)

        self.review_result = QTextEdit()
        self.review_result.setReadOnly(True)
        layout.addWidget(self.review_result)

        hist_btn = QPushButton("查看历史复盘")
        hist_btn.setCursor(Qt.PointingHandCursor)
        hist_btn.setStyleSheet(outline_button_style(accent=COLORS["primary"], padding="8px 22px", font_size=11))
        hist_btn.setMaximumWidth(240)
        hist_btn.clicked.connect(self._show_history)
        layout.addWidget(hist_btn, 0, Qt.AlignHCenter)
        return w

    def _do_review(self):
        log = TrainingLog(
            date=datetime.datetime.now().strftime("%Y-%m-%d"),
            movement=self.in_rev_move.text(),
            weight=self.in_rev_w.value(),
            reps=self.in_rev_reps.value(),
            sets=self.in_rev_sets.value(),
            rpe=self.in_rev_rpe.value(),
        )
        result = review_training(log)
        save_review(log, result)

        color = {
            "合适": COLORS["success"],
            "偏轻": COLORS["warning"],
            "偏重": COLORS["danger"],
            "部分完成": COLORS["warning"],
        }.get(result.judgment, COLORS["text"])
        html = f'<h3 style="color:{color};">判断: {result.judgment}</h3>'
        html += "<h4>关键发现</h4><ul>"
        for f in result.key_findings:
            html += f"<li>{f}</li>"
        html += "</ul>"
        rx = result.next_prescription
        html += f"<h4>下一次处方</h4><p><b>{rx.get('movement', '')}</b>: {rx.get('weight', '')}kg × {rx.get('sets', '')}组{rx.get('reps', '')}次 @ RPE {rx.get('rpe', '')}</p>"
        html += f"<p>渐进类型: <b>{result.progression_type}</b></p>"
        self.review_result.setHtml(html)

    def _show_history(self):
        reviews = load_reviews()
        if not reviews:
            self.review_result.setHtml("<p>暂无历史复盘记录</p>")
            return
        html = '<h3>历史复盘</h3><table border="1" cellpadding="4" style="border-collapse:collapse;">'
        html += "<tr><th>时间</th><th>动作</th><th>重量</th><th>组×次</th><th>RPE</th><th>判断</th><th>渐进</th></tr>"
        for r in reviews[-20:]:
            log = r["log"]
            html += f"<tr><td>{r['timestamp']}</td><td>{log['movement']}</td><td>{log['weight']}kg</td>"
            html += f"<td>{log['sets']}×{log['reps']}</td><td>{log['rpe']}</td>"
            html += f"<td>{r['judgment']}</td><td>{r['progression_type']}</td></tr>"
        html += "</table>"
        self.review_result.setHtml(html)

    # ─── 子页4: 停训接回 ───
    def _build_return_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("停训天数:"))
        self.in_days_off = QSpinBox()
        self.in_days_off.setRange(1, 365)
        self.in_days_off.setValue(7)
        ctrl.addWidget(self.in_days_off)
        ctrl.addWidget(QLabel("最近训练重量(kg):"))
        self.in_last_w = QDoubleSpinBox()
        self.in_last_w.setRange(0, 500)
        self.in_last_w.setValue(60)
        ctrl.addWidget(self.in_last_w)
        ctrl.addWidget(QLabel("动作:"))
        self.in_ret_move = QLineEdit("卧推")
        ctrl.addWidget(self.in_ret_move)
        layout.addLayout(ctrl)

        btn = QPushButton("生成接回方案")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(button_style(COLORS["warning"], padding="9px 30px", font_size=12))
        btn.setMinimumHeight(38)
        btn.setMaximumWidth(360)
        btn.clicked.connect(self._gen_return)
        layout.addWidget(btn, 0, Qt.AlignHCenter)

        self.return_result = QTextEdit()
        self.return_result.setReadOnly(True)
        layout.addWidget(self.return_result)
        return w

    def _gen_return(self):
        plan = generate_return_plan(
            self.in_days_off.value(),
            self.in_last_w.value(),
            self.in_ret_move.text(),
        )
        perm_color = {
            "正常接回": COLORS["success"],
            "降级接回": COLORS["warning"],
            "最低任务": COLORS["accent"],
            "暂停": COLORS["danger"],
        }.get(plan.permission, COLORS["text"])
        html = f'<h3 style="color:{perm_color};">恢复权限: {plan.permission}</h3>'
        html += f"<p>停训天数: {plan.days_off}天</p>"
        html += "<h4>三档方案</h4><ul>"
        html += f"<li><b>正常版</b>: {plan.normal_version}</li>"
        html += f"<li><b>降级版</b>: {plan.degraded_version}</li>"
        html += f"<li><b>最低版</b>: {plan.minimal_version}</li>"
        html += "</ul><h4>未来7天</h4><ol>"
        for d in plan.next_7_days:
            html += f"<li>{d}</li>"
        html += "</ol>"
        self.return_result.setHtml(html)

    # ─── 子页5: 最低执行版本 ───
    def _build_short_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        intro = QLabel("时间不足时自动生成短版训练：保留主线动作，不补课、不加倍训练、不用惩罚性有氧。")
        intro.setWordWrap(True)
        intro.setStyleSheet(
            f"color: {COLORS['text']}; background-color: {COLORS['primary_soft']}; "
            f"border: 1px solid {COLORS['primary_border']}; border-radius: 8px; padding: 10px 12px;"
        )
        layout.addWidget(intro)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        ctrl.addWidget(QLabel("可用时间(分钟):"))
        self.in_short_minutes = QSpinBox()
        self.in_short_minutes.setRange(5, 60)
        self.in_short_minutes.setValue(20)
        self.in_short_minutes.setMinimumHeight(32)
        ctrl.addWidget(self.in_short_minutes)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        time_btns = QHBoxLayout()
        time_btns.setSpacing(10)
        for m in [30, 20, 10]:
            btn = QPushButton(f"{m}分钟版")
            btn.setStyleSheet(outline_button_style(accent=COLORS["primary"], padding="8px 28px", font_size=12))
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _, x=m: self._gen_short(x))
            time_btns.addWidget(btn)
        time_btns.addStretch()
        layout.addLayout(time_btns)

        self.short_result = QTextEdit()
        self.short_result.setReadOnly(True)
        layout.addWidget(self.short_result)
        return w

    def _gen_short(self, minutes: int):
        if not hasattr(self, "cycle_result"):
            self.short_result.setHtml('<p>请先在"力量周期"页生成周期</p>')
            return
        move = self.in_cycle_move.currentText() if hasattr(self, "in_cycle_move") else "主项"
        cur = self.in_cur_1rm.value() if hasattr(self, "in_cur_1rm") else 60
        cycle = generate_strength_cycle(move, cur, cur * 1.1, 2)
        if not cycle.days:
            self.short_result.setHtml("<p>无可用训练日</p>")
            return
        day = cycle.days[0]
        short = generate_short_version(day, minutes)
        html = f"<h3>{minutes}分钟短版训练</h3>"
        html += f"<p>动作: {move}</p>"
        html += f"<p><b>{short}</b></p>"
        html += "<h4>原则</h4><ul>"
        html += "<li>优先保留当天主线动作</li>"
        html += "<li>不补课、不加倍训练</li>"
        html += "<li>不用惩罚性有氧</li>"
        html += "<li>漏一次按原顺序继续，漏两次用短版接回</li>"
        html += "</ul>"
        self.short_result.setHtml(html)
