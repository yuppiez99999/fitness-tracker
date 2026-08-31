# -*- coding: utf-8 -*-
"""
UI 页面 (v7.0 模块化拆分)
DashboardPage / TrendChartPage / ExerciseLibraryPage / TrainingPlanPage / NutritionPage
"""
import datetime
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('QtAgg')  # 必须在导入 pyplot 之前设置后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog,     QScrollArea, QFrame, QComboBox, QGroupBox, QToolButton,
    QDialog, QSizePolicy,
)

from .constants import (
    COLORS, PHASE_INFO, TRAINING_SCHEDULE, VACUUM_TUTORIAL,
    FLOW_TUTORIAL, REPORT_DIR, _emoji_for_target,
)
from .data_model import BodyDataModel
from .exercise_lib import ExerciseLibrary
from .parsers import TrainingPlanParser, NutritionParser
from .dialogs import ExerciseDetailDialog


# ═══════════════════════════════════════════════════════════
# UI页面 — 仪表盘
# ═══════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    """仪表盘 — 体测概览 + 快速录入"""

    record_added = Signal()

    def __init__(self, model: BodyDataModel):
        super().__init__()
        self.model = model
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 顶部标题
        title = QLabel('📊 体测仪表盘')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        # 统计卡片网格
        cards_frame = QFrame()
        cards_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 10px;")
        cards_layout = QGridLayout(cards_frame)
        cards_layout.setSpacing(8)

        self.stat_labels = {}
        cards_config = [
            ('总记录', '—', COLORS['primary'], 0, 0),
            ('统计天数', '—', COLORS['cyan'], 0, 1),
            ('当前体重', '—', COLORS['danger'], 0, 2),
            ('当前体脂', '—', COLORS['danger'], 0, 3),
            ('体重变化', '—', COLORS['success'], 1, 0),
            ('体脂变化', '—', COLORS['success'], 1, 1),
            ('瘦体重', '—', COLORS['purple'], 1, 2),
            ('距目标', '—', COLORS['warning'], 1, 3),
        ]
        for key, val, color, row, col in cards_config:
            card = QFrame()
            card.setStyleSheet(f"background-color: {COLORS['bg']}; border-radius: 6px; padding: 8px;")
            cl = QVBoxLayout(card)
            lbl_title = QLabel(key)
            lbl_title.setFont(QFont('Microsoft YaHei', 9))
            lbl_title.setStyleSheet(f"color: {COLORS['subtext']};")
            lbl_val = QLabel(val)
            lbl_val.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
            lbl_val.setStyleSheet(f"color: {color};")
            cl.addWidget(lbl_title)
            cl.addWidget(lbl_val)
            cards_layout.addWidget(card, row, col)
            self.stat_labels[key] = lbl_val

        layout.addWidget(cards_frame)

        # 快速录入区
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 10px;")
        input_layout = QVBoxLayout(input_frame)

        lbl_input = QLabel('⚡ 快速录入')
        lbl_input.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        lbl_input.setStyleSheet(f"color: {COLORS['primary']};")
        input_layout.addWidget(lbl_input)

        row = QHBoxLayout()
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        self.input_date = QLineEdit(today)
        self.input_date.setPlaceholderText('日期 YYYY-MM-DD')
        self.input_weight = QLineEdit()
        self.input_weight.setPlaceholderText('体重(kg)')
        self.input_fat = QLineEdit()
        self.input_fat.setPlaceholderText('体脂率(%) 可选')
        self.input_muscle = QLineEdit()
        self.input_muscle.setPlaceholderText('肌肉量(kg) 可选')

        for w in [self.input_date, self.input_weight, self.input_fat, self.input_muscle]:
            w.setStyleSheet(f"background-color: {COLORS['bg']}; color: {COLORS['text']}; "
                            f"border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px;")
            row.addWidget(w)

        btn_add = QPushButton('＋ 录入')
        btn_add.setStyleSheet(f"background-color: {COLORS['success']}; color: white; "
                              f"border-radius: 4px; padding: 8px 16px; font-weight: bold;")
        btn_add.clicked.connect(self._on_add)
        row.addWidget(btn_add)

        input_layout.addLayout(row)
        layout.addWidget(input_frame)

        # 数据表格
        table_frame = QFrame()
        table_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 10px;")
        table_layout = QVBoxLayout(table_frame)
        lbl_table = QLabel('📋 历史记录')
        lbl_table.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        lbl_table.setStyleSheet(f"color: {COLORS['primary']};")
        table_layout.addWidget(lbl_table)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['日期', '体重(kg)', '体脂率(%)', '肌肉量(kg)'])
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {COLORS['bg']}; color: {COLORS['text']};
                            gridline-color: {COLORS['border']}; border: none; }}
            QHeaderView::section {{ background-color: {COLORS['card']}; color: {COLORS['primary']};
                                    padding: 6px; border: 1px solid {COLORS['border']}; }}
        """)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.table)

        # 操作按钮
        btn_row = QHBoxLayout()
        for text, color, handler in [
            ('🗑 删除', COLORS['danger'], self._on_delete),
            ('💾 导出', COLORS['cyan'], self._on_export),
            ('📊 报告', COLORS['warning'], self._on_report),
        ]:
            b = QPushButton(text)
            b.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 6px 12px;")
            b.clicked.connect(handler)
            btn_row.addWidget(b)
        btn_row.addStretch()
        table_layout.addLayout(btn_row)

        layout.addWidget(table_frame, stretch=1)
        self.refresh()

    def refresh(self):
        stats = self.model.get_stats()
        # 更新卡片
        if stats['count'] == 0:
            for k in self.stat_labels:
                self.stat_labels[k].setText('—')
            return
        self.stat_labels['总记录'].setText(f"{stats['count']}")
        self.stat_labels['统计天数'].setText(f"{stats['days']}天")
        self.stat_labels['当前体重'].setText(f"{stats['cur_weight']:.1f}kg")
        self.stat_labels['当前体脂'].setText(f"{stats['cur_fat']:.1f}%" if pd.notna(stats['cur_fat']) else '—')
        wc = stats['weight_change']
        self.stat_labels['体重变化'].setText(f"{'+' if wc >= 0 else ''}{wc:.1f}kg")
        fc = stats.get('fat_change', np.nan)
        self.stat_labels['体脂变化'].setText(f"{fc:+.1f}%" if pd.notna(fc) else '—')
        self.stat_labels['瘦体重'].setText(f"{stats['cur_lean']:.1f}kg" if pd.notna(stats['cur_lean']) else '—')
        tw = stats['to_target_w']
        self.stat_labels['距目标'].setText(f"差{tw:+.1f}kg" if tw > 0 else f"超{-tw:.1f}kg")

        # 更新表格
        df = self.model.df
        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(str(row['日期'])))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['体重(kg)']:.1f}" if pd.notna(row['体重(kg)']) else '—'))
            self.table.setItem(i, 2, QTableWidgetItem(f"{row['体脂率(%)']:.1f}" if pd.notna(row['体脂率(%)']) else '—'))
            self.table.setItem(i, 3, QTableWidgetItem(f"{row['肌肉量(kg)']:.1f}" if pd.notna(row.get('肌肉量(kg)')) else '—'))

    def _on_add(self):
        date = self.input_date.text().strip()
        w_text = self.input_weight.text().strip()
        if not date or not w_text:
            QMessageBox.warning(self, '提示', '请输入日期和体重')
            return
        try:
            weight = float(w_text)
            fat = float(self.input_fat.text()) if self.input_fat.text().strip() else None
            muscle = float(self.input_muscle.text()) if self.input_muscle.text().strip() else None
        except ValueError:
            QMessageBox.error(self, '错误', '请输入有效数字')
            return
        self.model.add_record(date, weight, fat, **{'肌肉量(kg)': muscle} if muscle else {})
        self.input_weight.clear()
        self.input_fat.clear()
        self.input_muscle.clear()
        self.refresh()
        self.record_added.emit()

    def _on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请先选中一行')
            return
        date = self.table.item(row, 0).text()
        if QMessageBox.question(self, '确认', f'删除 {date} 的记录?') == QMessageBox.Yes:
            self.model.delete_record(date)
            self.refresh()

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, '导出CSV', '体测数据.csv', 'CSV (*.csv)')
        if path:
            self.model.df.to_csv(path, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, '成功', f'已导出到 {path}')

    def _on_report(self):
        stats = self.model.get_stats()
        if stats['count'] == 0:
            QMessageBox.warning(self, '提示', '无数据')
            return
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(REPORT_DIR, f'体测报告_{ts}.txt')
        pred_w = self.model.predict_target_date(self.model.target_weight)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'═══ 体测报告 {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")} ═══\n\n')
            f.write(f'统计: {stats["count"]}条 / {stats["days"]}天\n')
            f.write(f'体重: {stats["init_weight"]:.1f} → {stats["cur_weight"]:.1f}kg ({stats["weight_change"]:+.1f})\n')
            if pd.notna(stats['cur_fat']):
                f.write(f'体脂: {stats["cur_fat"]:.1f}%\n')
            if pd.notna(stats['cur_lean']):
                f.write(f'瘦体重: {stats["cur_lean"]:.1f}kg\n')
            f.write(f'距目标: 体重差{stats["to_target_w"]:+.1f}kg\n')
            if pred_w:
                f.write(f'预计达标日: {pred_w}\n')
        QMessageBox.information(self, '报告已生成', path)


# ═══════════════════════════════════════════════════════════
# UI页面 — 趋势图
# ═══════════════════════════════════════════════════════════

class TrendChartPage(QWidget):
    """趋势图 — matplotlib嵌入,体重/体脂/肌肉量多曲线"""

    def __init__(self, model: BodyDataModel):
        super().__init__()
        self.model = model
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)

        # 顶部
        top = QHBoxLayout()
        title = QLabel('📈 趋势分析')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        # 图表类型切换
        self.combo_chart = QComboBox()
        self.combo_chart.addItems(['体重+体脂趋势', '变化对比', '周度分析', '体成分构成'])
        self.combo_chart.setStyleSheet(f"background-color: {COLORS['card']}; color: {COLORS['text']}; "
                                       f"padding: 4px; border-radius: 4px;")
        self.combo_chart.currentIndexChanged.connect(self._draw)
        top.addWidget(self.combo_chart)
        layout.addLayout(top)

        # matplotlib画布
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        self.fig, self.ax = plt.subplots(figsize=(10, 5.5))
        self.fig.patch.set_facecolor(COLORS['card'])
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("border: none;")
        layout.addWidget(self.canvas, stretch=1)

        # 保存按钮
        btn_save = QPushButton('💾 保存图表')
        btn_save.setStyleSheet(f"background-color: {COLORS['cyan']}; color: white; border-radius: 4px; padding: 6px 16px;")
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

        self._draw()

    def _draw(self):
        idx = self.combo_chart.currentIndex()
        self.ax.clear()
        df = self.model.df
        if len(df) < 2:
            self.ax.text(0.5, 0.5, '需要至少2条记录', transform=self.ax.transAxes,
                         ha='center', va='center', color=COLORS['subtext'], fontsize=14)
            self.canvas.draw()
            return

        plot_df = self.model.get_plot_df()  # 复用缓存的日期解析结果

        if idx == 0:
            self._draw_trend(plot_df)
        elif idx == 1:
            self._draw_compare(plot_df)
        elif idx == 2:
            self._draw_weekly(plot_df)
        else:
            self._draw_composition(plot_df)

        self.canvas.draw()

    def _style_ax(self, ax, title, ylabel):
        ax.set_facecolor(COLORS['card'])
        ax.tick_params(colors=COLORS['subtext'], labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['border'])
        ax.spines['left'].set_color(COLORS['border'])
        ax.set_title(title, color=COLORS['text'], fontsize=13, fontweight='bold', pad=10)
        ax.set_ylabel(ylabel, color=COLORS['subtext'], fontsize=10)
        ax.grid(True, alpha=0.15, color=COLORS['subtext'])
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        for label in ax.get_xticklabels():
            label.set_rotation(30)
            label.set_fontsize(7)

    def _draw_trend(self, plot_df):
        """体重+体脂趋势 + 7日EMA"""
        self.ax.plot(plot_df['日期_dt'], plot_df['体重(kg)'],
                     color=COLORS['primary'], linewidth=2, marker='o', markersize=3,
                     markerfacecolor=COLORS['primary'], label='体重', zorder=3)
        ema = plot_df['体重(kg)'].ewm(span=7, adjust=False).mean()
        self.ax.plot(plot_df['日期_dt'], ema, color=COLORS['cyan'],
                     linewidth=1.5, linestyle='--', alpha=0.8, label='7日EMA')
        self.ax.axhline(y=self.model.target_weight, color=COLORS['danger'],
                        linestyle='--', linewidth=1, alpha=0.6,
                        label=f"目标{self.model.target_weight}kg")

        fat_data = plot_df[plot_df['体脂率(%)'].notna()]
        if len(fat_data) > 0:
            ax2 = self.ax.twinx()
            ax2.plot(fat_data['日期_dt'], fat_data['体脂率(%)'],
                     color=COLORS['danger'], linewidth=1.5, marker='s', markersize=2,
                     alpha=0.7, label='体脂率')
            ax2.axhline(y=self.model.target_bodyfat, color=COLORS['warning'],
                        linestyle=':', linewidth=1, alpha=0.6)
            ax2.set_ylabel('体脂率(%)', color=COLORS['danger'], fontsize=9)
            ax2.tick_params(colors=COLORS['danger'], labelsize=8)
            ax2.spines['top'].set_visible(False)
            ax2.spines['left'].set_visible(False)

        self._style_ax(self.ax, '体重/体脂趋势', '体重(kg)')
        self.ax.legend(loc='upper left', fontsize=8, framealpha=0.3,
                       facecolor=COLORS['card'], edgecolor=COLORS['border'])

        pred = self.model.predict_target_date(self.model.target_weight)
        if pred and pred != '已达':
            self.ax.annotate(f'预测达标:{pred}', xy=(0.98, 0.95),
                             xycoords='axes fraction', ha='right', fontsize=9,
                             color=COLORS['warning'],
                             bbox=dict(boxstyle='round,pad=0.3', facecolor=COLORS['card'],
                                       edgecolor=COLORS['warning'], alpha=0.8))

    def _draw_compare(self, plot_df):
        """日变化量柱状图"""
        diffs = plot_df['体重(kg)'].diff().dropna()
        dates = plot_df['日期_dt'].iloc[1:][plot_df['体重(kg)'].diff().notna()]
        colors = [COLORS['success'] if v < 0 else COLORS['danger'] for v in diffs]
        self.ax.bar(dates, diffs, color=colors, alpha=0.8, width=0.8)
        self.ax.axhline(y=0, color=COLORS['subtext'], linewidth=0.5)
        self._style_ax(self.ax, '每日体重变化量', '变化(kg)')

    def _draw_weekly(self, plot_df):
        """周度均值"""
        plot_df['周'] = plot_df['日期_dt'].dt.isocalendar().week.astype(int)
        weekly = plot_df.groupby('周')['体重(kg)'].agg(['mean', 'min', 'count']).reset_index()
        x = range(len(weekly))
        self.ax.plot(x, weekly['mean'], 'o-', color=COLORS['primary'], linewidth=2, label='周均体重')
        self.ax.fill_between(x, weekly['mean'], weekly['min'], alpha=0.2, color=COLORS['primary'])
        self.ax.axhline(y=self.model.target_weight, color=COLORS['danger'],
                        linestyle='--', linewidth=1, alpha=0.6, label=f"目标{self.model.target_weight}kg")
        self.ax.set_xticks(list(x))
        self.ax.set_xticklabels([f'W{w}' for w in weekly['周']], fontsize=7)
        self._style_ax(self.ax, '周度体重变化', '体重(kg)')
        self.ax.legend(fontsize=8, framealpha=0.3, facecolor=COLORS['card'])

    def _draw_composition(self, plot_df):
        """体成分构成(最新记录)"""
        latest = plot_df.iloc[-1]
        cur_fat = latest['体脂率(%)']
        cur_w = latest['体重(kg)']
        if pd.isna(cur_fat):
            self.ax.text(0.5, 0.5, '无体脂数据', transform=self.ax.transAxes,
                         ha='center', color=COLORS['subtext'])
            return
        fat_mass = cur_w * cur_fat / 100
        lean_mass = cur_w - fat_mass
        sizes = [lean_mass, fat_mass]
        labels = [f'瘦体重\n{lean_mass:.1f}kg', f'脂肪\n{fat_mass:.1f}kg']
        colors_pie = [COLORS['primary'], COLORS['danger']]
        self.ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%',
                    startangle=90, textprops={'color': COLORS['text'], 'fontsize': 10})
        self.ax.set_title('当前体成分构成', color=COLORS['text'], fontsize=13, fontweight='bold')

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, '保存图表', '趋势图.png', 'PNG (*.png)')
        if path:
            self.fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=COLORS['card'])
            QMessageBox.information(self, '成功', f'已保存到 {path}')


# ═══════════════════════════════════════════════════════════
# UI页面 — 动作库
# ═══════════════════════════════════════════════════════════

class ExerciseLibraryPage(QWidget):
    """动作库 — 网格浏览 + 搜索 + 点击查看详情"""

    def __init__(self, lib: ExerciseLibrary):
        super().__init__()
        self.lib = lib
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)

        # 顶部
        top = QHBoxLayout()
        title = QLabel('🏋️ 动作示范库')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText('搜索动作名/肌群/器材...')
        self.search.setStyleSheet(f"background-color: {COLORS['card']}; color: {COLORS['text']}; "
                                  f"border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 6px; width: 250px;")
        self.search.textChanged.connect(self._filter)
        top.addWidget(self.search)
        layout.addLayout(top)

        # 动作网格(滚动)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        self._populate(self.lib.exercises)

    def _populate(self, exercises: List[Dict]):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 4
        for i, ex in enumerate(exercises):
            card = self._make_card(ex)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _make_card(self, ex: Dict) -> QFrame:
        card = QFrame()
        card.setFixedSize(200, 220)
        card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 8px;
                      border: 1px solid {COLORS['border']}; }}
            QFrame:hover {{ border: 2px solid {COLORS['primary']}; }}
        """)
        cl = QVBoxLayout(card)

        media_id = ex.get('media_id', '')
        thumb = QLabel()
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setFixedSize(180, 130)
        thumb.setStyleSheet(
            f"background-color: {COLORS['bg']}; border-radius: 4px; "
            f"border: 1px solid {COLORS['border']};"
        )
        pixmap = self.lib.get_first_frame(media_id)
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(178, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            thumb.setPixmap(scaled)
        else:
            thumb.setText('')
            thumb.setStyleSheet(
                f"background-color: {COLORS['bg']}; color: {COLORS['subtext']}; "
                f"font-size: 36px; border-radius: 4px; border: 1px solid {COLORS['border']};"
            )
        cl.addWidget(thumb)

        name = QLabel(ex.get('name_cn', '未知'))
        name.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        name.setStyleSheet(f"color: {COLORS['text']};")
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignCenter)
        cl.addWidget(name)

        target = QLabel(ex.get('target', ''))
        target.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        target.setAlignment(Qt.AlignCenter)
        cl.addWidget(target)

        card.mousePressEvent = lambda e, eobj=ex: self._show_detail(eobj)
        return card

    def _filter(self, text: str):
        results = self.lib.search(text)
        self._populate(results)

    def _show_detail(self, ex: Dict):
        dlg = ExerciseDetailDialog(ex, self.lib, self)
        dlg.exec()


# ═══════════════════════════════════════════════════════════
# UI页面 — 训练计划
# ═══════════════════════════════════════════════════════════

class TrainingPlanPage(QWidget):
    """训练计划 — 22周居家平替塑形, 周历视图 + 阶段切换 + 每日动作列表"""

    def __init__(self, plan: TrainingPlanParser, lib: ExerciseLibrary):
        super().__init__()
        self.plan = plan
        self.lib = lib
        self.current_week = 1
        self.daily_exercises = plan.get_daily_exercises(self.current_week)
        # v3.0: 解析海豹徒手 + 囚徒健身两大补位体系(fail-open, 缺章节也为空结构)
        self.supplement = plan.get_supplement_systems()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)

        # 顶部
        top = QHBoxLayout()
        title = QLabel('📅 22周居家平替塑形 — 单杠+哑铃 · 三阶段周期化')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        self.combo_week = QComboBox()
        self.combo_week.setMinimumWidth(220)
        self.combo_week.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        week_labels = []
        for w in range(1, 23):
            p = TrainingPlanParser.get_phase(w)
            phase_label = PHASE_INFO[p]['name']
            week_labels.append(f'第{w}周 [{phase_label}]')
        self.combo_week.addItems(week_labels)
        self.combo_week.setStyleSheet(f"background-color: {COLORS['card']}; color: {COLORS['text']}; "
                                       f"padding: 4px; border-radius: 4px;")
        self.combo_week.currentIndexChanged.connect(self._on_week_changed)
        top.addWidget(self.combo_week)
        layout.addLayout(top)

        # 阶段信息标签
        self.phase_label = QLabel()
        self.phase_label.setStyleSheet(f"color: {COLORS['success']}; padding: 4px; font-size: 12px;")
        layout.addWidget(self.phase_label)

        # 提示
        note = QLabel('💡 点击动作卡片查看GIF示范 + 详细步骤教学')
        note.setStyleSheet(f"color: {COLORS['subtext']}; padding: 4px;")
        layout.addWidget(note)


        # 7天卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container_days = QWidget()
        self.container_days.setMinimumWidth(900)
        self.grid_days = QGridLayout(self.container_days)
        self.grid_days.setSpacing(10)
        self.grid_days.setColumnStretch(0, 1)
        self.grid_days.setColumnStretch(1, 1)
        self.grid_days.setColumnStretch(2, 1)
        scroll.setWidget(self.container_days)
        layout.addWidget(scroll, stretch=1)

        self._refresh_days()

    def _build_supplement_box(self, layout: QVBoxLayout):
        """v3.0 补位体系折叠区 — 海豹徒手 + 囚徒健身两大补位体系速览"""
        seal = self.supplement.get('seal', {})
        cc = self.supplement.get('cc', {})
        has_seal = bool(seal.get('moves') or seal.get('position'))
        has_cc = bool(cc.get('arts') or cc.get('position'))
        if not (has_seal or has_cc):
            return

        box = QGroupBox('🪢 补位体系 · 海豹徒手 (Navy SEAL) + 囚徒健身 (CC)')
        box.setStyleSheet(f"""
            QGroupBox {{ background-color: {COLORS['card']}; border: 1px solid {COLORS['border']};
                        border-radius: 8px; margin-top: 6px; color: {COLORS['primary']};
                        font-weight: bold; padding-top: 8px; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        """)
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(12, 14, 12, 12)
        box_layout.setSpacing(8)

        toggle = QToolButton(box)
        toggle.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toggle.setText('▼')
        toggle.setFixedSize(22, 22)
        toggle.setStyleSheet(
            f"QToolButton {{ background-color: {COLORS['bg']}; color: {COLORS['primary']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 4px; font-weight: bold; }}"
        )
        toggle.setCursor(Qt.PointingHandCursor)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 4, 0, 0)
        content_layout.setSpacing(10)

        def _toggle():
            visible = content.isVisible()
            content.setVisible(not visible)
            toggle.setText('▶' if visible else '▼')

        toggle.clicked.connect(_toggle)

        def _position_toggle():
            toggle.move(box.width() - 34, 10)

        box.resizeEvent = lambda e: (_position_toggle(), type(box).resizeEvent(box, e))

        if has_seal:
            box_layout.addWidget(self._make_supplement_card(
                '🪖 海豹徒手 (Navy SEAL Bodyweight)',
                seal.get('position', ''),
                seal.get('moves', []),
                seal.get('test_loop', ''),
                seal.get('embed', []),
                '六支柱循环: 推 / 起 / 引 / 蹲 / 弓步 / 平板',
            ))
        if has_cc:
            box_layout.addWidget(self._make_supplement_card(
                '🔗 囚徒健身 (Convict Conditioning)',
                cc.get('position', ''),
                [],
                '',
                cc.get('embed', []),
                None,
                arts=cc.get('arts', []),
            ))

        box_layout.addWidget(content, stretch=1)
        layout.addWidget(box)

    def _make_supplement_card(self, title: str, position: str, moves: List[Dict],
                              test_loop: str, embed: List[str], pillars: str = None,
                              arts: List[Dict] = None) -> QWidget:
        """渲染单个补位体系卡片(海豹徒手 or 囚徒健身)"""
        card = QWidget()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(6)
        card.setStyleSheet(f"background-color: {COLORS['bg']}; border-radius: 8px; "
                           f"border: 1px solid {COLORS['border']};")

        h = QLabel(title)
        h.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        h.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        cl.addWidget(h)

        if position:
            pos = QLabel(position)
            pos.setWordWrap(True)
            pos.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px; background: transparent;")
            cl.addWidget(pos)

        if pillars:
            pl = QLabel(pillars)
            pl.setWordWrap(True)
            pl.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; background: transparent;")
            cl.addWidget(pl)

        if moves:
            grid = QGridLayout()
            grid.setSpacing(4)
            grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
            grid.setColumnStretch(2, 2)
            for i, m in enumerate(moves):
                r = i // 2; c = (i % 2) * 3
                nm = QLabel(f"• {m.get('name', '')}")
                nm.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; background: transparent;")
                nm.setWordWrap(True)
                tg = QLabel(m.get('target', ''))
                tg.setStyleSheet(f"color: {COLORS['primary']}; font-size: 10px; background: transparent;")
                tg.setWordWrap(True)
                tp = QLabel(m.get('tip', '')[:40])
                tp.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px; background: transparent;")
                tp.setWordWrap(True)
                grid.addWidget(nm, r, c); grid.addWidget(tg, r, c + 1); grid.addWidget(tp, r, c + 2)
            cl.addLayout(grid)

        if arts:
            for a in arts:
                row = QLabel(f"• {a.get('art', '')} — 阶1:{a.get('s1', '')} → 阶5:{a.get('s5', '')} → 阶10:{a.get('s10', '')}"
                             f"  〔{a.get('day', '')}〕")
                row.setWordWrap(True)
                row.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px; background: transparent;")
                cl.addWidget(row)

        if test_loop:
            tl = QLabel(f"🎯 SEAL 500 验收: {test_loop}")
            tl.setWordWrap(True)
            tl.setStyleSheet(f"color: {COLORS['warning']}; font-size: 10px; background: transparent;")
            cl.addWidget(tl)

        if embed:
            for e in embed:
                eb = QLabel(f"↳ {e}")
                eb.setWordWrap(True)
                eb.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px; background: transparent;")
                cl.addWidget(eb)

        return card

    def _on_week_changed(self, idx: int):
        self.current_week = idx + 1
        self.daily_exercises = self.plan.get_daily_exercises(self.current_week)
        self._refresh_days()

    def _refresh_days(self):
        while self.grid_days.count():
            item = self.grid_days.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        phase = TrainingPlanParser.get_phase(self.current_week)
        info = PHASE_INFO[phase]
        week_notes = self.plan.get_phase_notes(self.current_week)
        phase_text = f"📍 {info['name']} ({info['weeks']}) — {info['desc']}"
        if week_notes:
            phase_text += "\n⚠ Phase调整: " + ' | '.join(week_notes[:6])
        self.phase_label.setText(phase_text)

        for i, sched in enumerate(TRAINING_SCHEDULE):
            day_card = self._make_day_card(sched)
            self.grid_days.addWidget(day_card, i // 3, i % 3)

    def _make_day_card(self, sched: Dict) -> QFrame:
        title_lower = sched['title'].lower()
        is_hiit = 'hiit' in title_lower
        is_liss = 'liss' in title_lower
        is_rest = ('休息' in sched['title']) or ('rest' in title_lower)
        if is_hiit:
            title_color = COLORS['hiit_fg']
            sub_text = '🔥 高强度间歇训练'
        elif is_liss:
            title_color = COLORS['liss_fg']
            sub_text = '🚶 低强度稳态有氧'
        elif is_rest:
            title_color = COLORS['rest_fg']
            sub_text = '💤 主动恢复日'
        else:
            title_color = COLORS['primary']
            sub_text = sched.get('focus', '')

        card = QFrame()
        card.setMinimumWidth(280)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 10px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        icon_lbl = QLabel(sched['icon'])
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        header_row.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        header = QLabel(f"{sched['day']}  {sched['title']}")
        header.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        header.setStyleSheet(f"color: {title_color}; background: transparent;")
        focus = QLabel(sub_text)
        focus.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px; background: transparent;")
        title_col.addWidget(header)
        title_col.addWidget(focus)
        title_wrap = QWidget()
        title_wrap.setStyleSheet("background: transparent;")
        title_wrap.setLayout(title_col)
        header_row.addWidget(title_wrap, 1)

        exercises = self.daily_exercises.get(sched['day'], [])
        real_exs = [e for e in exercises if not e.get('is_workout_block')]
        total = len(real_exs)
        with_gif = sum(1 for e in real_exs if self._resolve_ex_data(e).get('media_id'))
        if is_rest or total == 0:
            stat_chip = QLabel('休息日')
            chip_color = COLORS['rest_fg']
        elif with_gif == total:
            stat_chip = QLabel(f'✓ {total} GIF')
            chip_color = COLORS['success']
        elif with_gif > 0:
            stat_chip = QLabel(f'{with_gif}/{total}')
            chip_color = COLORS['accent']
        else:
            stat_chip = QLabel(f'0/{total}')
            chip_color = COLORS['warning']
        stat_chip.setStyleSheet(
            f"color: {chip_color}; background-color: {COLORS['bg']}; "
            f"border: 1px solid {chip_color}; border-radius: 9px; "
            f"padding: 3px 9px; font-size: 10px; font-weight: bold;"
        )
        header_row.addWidget(stat_chip)
        cl.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        cl.addWidget(sep)

        if is_rest or not exercises:
            hint = QLabel('😴 完全休息日\n晨空腹称重 + 真空腹5×60s\n30min拉伸 + 1h低强度散步\n控盐日(钠<3g) · 蔬菜为主\n睡眠8h+ · 蛋白160g')
            hint.setStyleSheet(f"color: {COLORS['success']}; padding: 8px;")
            hint.setWordWrap(True)
            cl.addWidget(hint)
        else:
            for ex in exercises:
                if ex.get('is_workout_block'):
                    ex_wid = self._make_workout_block(ex)
                else:
                    ex_wid = self._make_exercise_button(ex)
                cl.addWidget(ex_wid)

        cl.addStretch()
        return card

    def _resolve_ex_data(self, ex: Dict) -> Dict:
        """统一的ex→ex_data解析入口, 供统计/缩略图共用"""
        media_id = ex.get('media_id', '') or ''
        if media_id:
            ed = self.lib.get_by_media_id(media_id)
            if ed:
                return ed
        ed = self.lib.get_by_name(ex.get('name', '')) if ex.get('name') else None
        if ed:
            return ed
        ed = self._fuzzy_match_exercise(ex.get('name', ''))
        if ed:
            return ed
        return {
            'name_cn': ex.get('name', ''), 'name_en': '', 'target': ex.get('target', ''),
            'muscle_group': '', 'secondary_muscles': [],
            'equipment': '', 'instructions_zh': '', 'instruction_steps_zh': [],
            'media_id': '', 'matched': False,
        }

    def _make_workout_block(self, ex: Dict) -> QFrame:
        """v5.9.2: HIIT循环 / LISS流程 / 复合动作 紧凑流程块"""
        block_type = ex.get('block_type', 'flow')
        duration = ex.get('duration', '')
        sub = ex.get('sub_info', '')
        block = QFrame()
        block.setMinimumHeight(46)
        block.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg']};
                border: 1px dashed {COLORS['primary']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                background-color: {COLORS['card']};
                border: 1px dashed {COLORS['accent']};
            }}
        """)

        if block_type == 'hiit_loop':
            ic = '🔥'; main_color = COLORS['hiit_fg']; lbl_sub_text = sub or '40秒训练 / 20秒休息'
        elif block_type == 'liss_cardio':
            ic = '🚶'; main_color = COLORS['liss_fg']; lbl_sub_text = sub or '心率120-135 · 低强稳态'
        else:
            ic = '📋'; main_color = COLORS['cyan']; lbl_sub_text = sub or ''

        ic_lbl = QLabel(ic); ic_lbl.setStyleSheet("font-size: 16px; background: transparent;")
        lbl_main = QLabel(ex.get('name', '训练流程'))
        lbl_main.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        lbl_main.setStyleSheet(f"color: {main_color}; background: transparent;")
        lbl_sub = QLabel(lbl_sub_text)
        lbl_sub.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px; background: transparent;")

        hl = QHBoxLayout(block)
        hl.setContentsMargins(10, 6, 10, 6)
        hl.setSpacing(8)
        hl.addWidget(ic_lbl)

        col = QVBoxLayout(); col.setSpacing(0)
        col.addWidget(lbl_main); col.addWidget(lbl_sub)
        col_w = QWidget(); col_w.setStyleSheet("background: transparent;"); col_w.setLayout(col)
        hl.addWidget(col_w, 1)

        if duration:
            dur_lbl = QLabel(duration)
            dur_lbl.setStyleSheet(
                f"color: {COLORS['accent']}; font-size: 10px; font-weight: bold; "
                f"background-color: {COLORS['card']}; border-radius: 8px; padding: 3px 9px;"
            )
            hl.addWidget(dur_lbl)

        block.setCursor(Qt.PointingHandCursor)
        handler = lambda e, data=ex: self._show_flow_detail(data)
        block.mousePressEvent = handler
        for child in block.findChildren(QWidget):
            child.setCursor(Qt.PointingHandCursor)
            child.mousePressEvent = handler
        return block

    def _show_flow_detail(self, ex: Dict):
        """v2.0: 流程块详情弹窗 — 真空腹/HIIT/LISS 等文字教程"""
        dlg = QDialog(self)
        name = ex.get('name', '训练流程')
        dlg.setWindowTitle(f'📋 {name} — 详细教程')
        dlg.setMinimumSize(620, 540)
        dlg.resize(680, 600)
        dlg.setStyleSheet(f"background-color: {COLORS['bg']}; color: {COLORS['text']};")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        title = QLabel(f'📋 {name}')
        title.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        lay.addWidget(title)

        sub_info = ex.get('sub_info', '')
        if sub_info:
            sub = QLabel(sub_info)
            sub.setStyleSheet(f"color: {COLORS['accent']}; font-size: 11px;")
            sub.setWordWrap(True)
            lay.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        lay.addWidget(sep)

        tutorial = VACUUM_TUTORIAL if '真空腹' in name else FLOW_TUTORIAL.get(ex.get('block_type', 'flow'), FLOW_TUTORIAL['flow'])
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(0, 4, 0, 4)
        bl.setSpacing(8)
        for i, step in enumerate(tutorial, 1):
            row = QLabel(f'{i}. {step}')
            row.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; padding: 4px 0;")
            row.setWordWrap(True)
            bl.addWidget(row)
        bl.addStretch()
        scroll.setWidget(body)
        lay.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton('关闭')
        btn_close.setStyleSheet(
            f"QPushButton {{ background-color: {COLORS['primary']}; color: white; "
            f"border-radius: 4px; padding: 6px 20px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: #1890FF; }}"
        )
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

        dlg.exec()

    def _make_exercise_button(self, ex: Dict) -> QFrame:
        name = ex.get('name', '')
        sets = ex.get('sets', '')
        target = ex.get('target', '')
        tip = ex.get('tip', '')
        media_id = ex.get('media_id', '')

        ex_data = self.lib.get_by_media_id(media_id) if media_id else None
        if ex_data is None:
            ex_data = self.lib.get_by_name(name) or self._fuzzy_match_exercise(name)
        if ex_data is None:
            ex_data = {
                'name_cn': name, 'name_en': '', 'target': target,
                'muscle_group': '', 'secondary_muscles': [],
                'equipment': '', 'instructions_zh': '', 'instruction_steps_zh': [],
                'media_id': '', 'matched': False,
            }

        container = QFrame()
        container.setMinimumHeight(54)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        container.setCursor(Qt.PointingHandCursor)
        has_gif = self.lib.has_gif(ex_data.get('media_id', ''))
        matched = ex_data.get('matched', True)

        border_color = COLORS['border']
        if not matched:
            border_color = COLORS['warning']
        elif has_gif:
            border_color = COLORS['success'] + '88'

        container.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['bg']}; border-radius: 8px;
                      border: 1px solid {border_color}; }}
            QFrame:hover {{ background-color: {COLORS['card']};
                           border: 1px solid {COLORS['primary']}; }}
        """)

        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(8, 4, 8, 4)
        hbox.setSpacing(8)

        thumb = QLabel()
        thumb.setFixedSize(52, 40)
        thumb.setAlignment(Qt.AlignCenter)
        if has_gif:
            pm = self.lib.get_first_frame(ex_data['media_id'])
            if pm and not pm.isNull():
                thumb.setPixmap(pm.scaled(50, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                thumb.setStyleSheet(
                    f"background-color: #000; border-radius: 4px; "
                    f"border: 1px solid {COLORS['success']}66;"
                )
            else:
                thumb.setText('GIF')
                thumb.setStyleSheet(
                    f"background-color: {COLORS['bg']}; color: {COLORS['primary']}; "
                    f"font-size: 8px; font-weight: bold; border-radius: 4px; "
                    f"border: 1px solid {COLORS['border']};"
                )
        else:
            emoji = _emoji_for_target(target or name)
            thumb.setText(emoji)
            bg_tint = COLORS['card']
            thumb.setStyleSheet(
                f"background-color: {bg_tint}; color: {COLORS['primary']}; "
                f"font-size: 18px; border-radius: 4px; "
                f"border: 1px dashed {COLORS['warning']}88;"
            )
        hbox.addWidget(thumb)

        text_widget = QWidget()
        text_widget.setStyleSheet("background: transparent; border: none;")
        tv = QVBoxLayout(text_widget)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        n = QLabel(name)
        n.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        n.setStyleSheet(f"color: {COLORS['text']}; background: transparent; border: none;")
        title_row.addWidget(n)
        if sets:
            s = QLabel(str(sets))
            s.setStyleSheet(f"color: {COLORS['accent']}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
            title_row.addWidget(s)
        title_row.addStretch()
        tv.addLayout(title_row)

        sub_text = ''
        if target and target not in ('收尾',) and 'LISS' not in str(target):
            sub_text = f'目标: {str(target)[:24]}'
        elif tip and len(tip) < 25:
            sub_text = f'{tip}'
        if sub_text:
            sub = QLabel(sub_text)
            sub.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px; background: transparent; border: none;")
            tv.addWidget(sub)

        hbox.addWidget(text_widget, stretch=1)

        status_lbl = QLabel()
        status_lbl.setFixedWidth(34)
        status_lbl.setAlignment(Qt.AlignCenter)
        if has_gif:
            status_lbl.setText('GIF')
            status_lbl.setStyleSheet(
                f"color: {COLORS['success']}; font-size: 8px; font-weight: bold; "
                f"background-color: {COLORS['success']}22; "
                f"border: 1px solid {COLORS['success']}66; "
                f"border-radius: 4px; padding: 2px 4px;"
            )
        else:
            status_lbl.setText('!')
            status_lbl.setStyleSheet(
                f"color: {COLORS['warning']}; font-size: 9px; font-weight: bold; "
                f"background-color: {COLORS['warning']}18; "
                f"border: 1px solid {COLORS['warning']}66; "
                f"border-radius: 4px; padding: 1px 4px;"
            )
        hbox.addWidget(status_lbl)

        container.mousePressEvent = lambda e, data=ex_data: self._show_exercise(data)
        for child in container.findChildren(QWidget):
            child.mousePressEvent = lambda e, data=ex_data: self._show_exercise(data)

        return container

    def _fuzzy_match_exercise(self, name: str) -> Optional[Dict]:
        """按名称模糊匹配: 剥离括号/数字/特殊格式/超级组标记, 取第一个有效匹配"""
        if not name:
            return None
        core = re.sub(r'[（(][^）)]*[）)]', '', name)
        core = core.replace('**', '').replace('超级组', '').replace('循环', '')
        core = core.replace('+', ' ')
        core = re.sub(r'\d+\s*[°]?\s*(分钟|分|秒|组|次|圈|轮|x|X|秒)?\s*$', '', core)
        core = re.sub(r'\s+', ' ', core).strip()
        core = re.sub(r'[\d×x\s]+$', '', core).strip()

        words = core.split()
        for n_words in [3, 2, 1]:
            if len(words) >= n_words:
                kw = ' '.join(words[:n_words])
                results = self.lib.search(kw)
                for r in results:
                    if self.lib.has_gif(r.get('media_id', '')):
                        return r

        if core:
            results = self.lib.search(core)
            for r in results:
                if self.lib.has_gif(r.get('media_id', '')):
                    return r

        if '+' in name:
            for part in re.split(r'\s*\+\s*', name):
                part = part.strip().replace('**', '').replace('超级组', '')
                ed = self.lib.get_by_name(part) or self._fuzzy_match_exercise(part)
                if ed and self.lib.has_gif(ed.get('media_id', '')):
                    return ed

        return None

    def _show_exercise(self, ex: Dict):
        dlg = ExerciseDetailDialog(ex, self.lib, self)
        dlg.exec()


# ═══════════════════════════════════════════════════════════
# UI组件 — 饮食与补剂页面
# ═══════════════════════════════════════════════════════════

class NutritionPage(QWidget):
    """饮食与补剂 — 三阶段营养方案 + 五餐明细 + 补剂表 + 饮水指南"""

    def __init__(self):
        super().__init__()
        self.current_week = 1
        self.current_day_type = 'training'
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        outer = QVBoxLayout(self)

        top = QHBoxLayout()
        title = QLabel('🍽 饮食与补剂方案')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        self.combo_week = QComboBox()
        self.combo_week.setMinimumWidth(220)
        self.combo_week.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        week_labels = []
        for w in range(1, 23):
            p = NutritionParser.get_phase(w)
            phase_label = PHASE_INFO[p]['name']
            week_labels.append(f'第{w}周 [{phase_label}]')
        self.combo_week.addItems(week_labels)
        self.combo_week.setStyleSheet(f"background-color: {COLORS['card']}; color: {COLORS['text']}; "
                                       f"padding: 4px; border-radius: 4px;")
        self.combo_week.currentIndexChanged.connect(self._on_week_changed)
        top.addWidget(self.combo_week)

        self.btn_training = self._make_type_btn('🏋 训练日', 'training', True)
        self.btn_rest = self._make_type_btn('😴 休息日', 'rest', False)
        self.btn_medium = self._make_type_btn('🟡 中碳日', 'medium', False)
        self.btn_highcarb = self._make_type_btn('⚡ 高碳日', 'high_carb', False)
        top.addWidget(self.btn_training)
        top.addWidget(self.btn_rest)
        top.addWidget(self.btn_medium)
        top.addWidget(self.btn_highcarb)
        outer.addLayout(top)

        self.phase_label = QLabel()
        self.phase_label.setStyleSheet(f"color: {COLORS['success']}; padding: 2px 4px; font-size: 12px;")
        outer.addWidget(self.phase_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        content.setMinimumWidth(900)
        content_layout = QVBoxLayout(content)

        self.macro_card = QFrame()
        self.macro_card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 10px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        self.macro_layout = QHBoxLayout(self.macro_card)
        self.macro_layout.setContentsMargins(20, 16, 20, 16)
        self.macro_layout.setSpacing(12)

        self.macro_labels = {}
        for key, icon, name, unit in [
            ('kcal', '🔥', '总热量', 'kcal'),
            ('protein', '🥩', '蛋白质', 'g'),
            ('carbs', '🍚', '碳水化合物', 'g'),
            ('fat', '🧈', '脂肪', 'g'),
        ]:
            panel = self._make_macro_panel(icon, name, unit)
            self.macro_layout.addWidget(panel)
            self.macro_labels[key] = panel
        content_layout.addWidget(self.macro_card)

        self.protein_pct_label = QLabel()
        self.protein_pct_label.setStyleSheet(f"color: {COLORS['subtext']}; padding: 4px 0; font-size: 11px;")
        content_layout.addWidget(self.protein_pct_label)

        meals_title = QLabel('📋 每日五餐明细')
        meals_title.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        meals_title.setStyleSheet(f"color: {COLORS['primary']}; padding-top: 12px;")
        content_layout.addWidget(meals_title)

        self.meals_grid = QGridLayout()
        self.meals_grid.setSpacing(10)
        for col in range(3):
            self.meals_grid.setColumnStretch(col, 1)
        content_layout.addLayout(self.meals_grid)

        self.total_summary = QLabel()
        self.total_summary.setStyleSheet(f"color: {COLORS['success']}; padding: 6px 0; font-size: 12px;")
        content_layout.addWidget(self.total_summary)

        supp_title = QLabel('💊 补剂方案')
        supp_title.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        supp_title.setStyleSheet(f"color: {COLORS['primary']}; padding-top: 12px;")
        content_layout.addWidget(supp_title)

        self.supplement_table = QWidget()
        supp_layout = QVBoxLayout(self.supplement_table)
        supp_layout.setSpacing(4)
        content_layout.addWidget(self.supplement_table)

        water_title = QLabel('💧 饮水与控盐')
        water_title.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        water_title.setStyleSheet(f"color: {COLORS['primary']}; padding-top: 12px;")
        content_layout.addWidget(water_title)

        self.water_table = QWidget()
        water_layout = QVBoxLayout(self.water_table)
        water_layout.setSpacing(4)
        content_layout.addWidget(self.water_table)

        content_layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

        self._refresh_all()

    def _make_type_btn(self, text: str, day_type: str, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setCheckable(True)
        btn.setChecked(active)
        btn.setProperty('day_type', day_type)
        base_bg = COLORS['primary'] if active else COLORS['card']
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {base_bg}; color: {'#fff' if active else COLORS['text']};
                          border: 1px solid {COLORS['border']}; border-radius: 4px;
                          padding: 4px 12px; font-size: 11px; font-weight: bold; }}
            QPushButton:checked {{ background-color: {COLORS['primary']}; color: #fff; }}
            QPushButton:hover {{ border: 1px solid {COLORS['primary']}; }}
        """)
        btn.clicked.connect(lambda checked=False, t=day_type: self._on_day_type_changed(t))
        return btn

    def _make_macro_panel(self, icon: str, name: str, unit: str) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['bg']}; border-radius: 8px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(14, 10, 14, 10)
        vl.setSpacing(2)

        head = QLabel(f'{icon} {name}')
        head.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px;")
        vl.addWidget(head)

        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        val = QLabel('--')
        val.setObjectName('macro_value')
        val.setFont(QFont('Consolas', 22, QFont.Bold))
        val.setStyleSheet(f"color: {COLORS['text']};")
        val_row.addWidget(val)
        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(f"color: {COLORS['subtext']}; padding-top: 6px; font-size: 10px;")
        val_row.addWidget(unit_lbl)
        val_row.addStretch()
        vl.addLayout(val_row)

        cmp = QLabel()
        cmp.setObjectName('macro_cmp')
        cmp.setStyleSheet(f"color: {COLORS['success']}; font-size: 9px;")
        vl.addWidget(cmp)
        return panel

    def _make_meal_card(self, meal: Dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 8px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        cv = QVBoxLayout(card)
        cv.setContentsMargins(12, 10, 12, 10)
        cv.setSpacing(4)

        hrow = QHBoxLayout()
        hrow.setSpacing(6)
        n = QLabel(meal['name'])
        n.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        n.setStyleSheet(f"color: {COLORS['primary']};")
        hrow.addWidget(n)
        hrow.addStretch()
        kcal_str = f"{meal['kcal']} kcal  P{meal['protein']}g C{meal['carbs']}g F{meal['fat']}g"
        cal = QLabel(kcal_str)
        cal.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        hrow.addWidget(cal)
        cv.addLayout(hrow)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        cv.addWidget(sep)

        for item_name, amount, detail in meal['items']:
            item_line = QHBoxLayout()
            item_line.setSpacing(6)
            iname = QLabel(item_name)
            iname.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
            item_line.addWidget(iname)
            iamt = QLabel(amount)
            iamt.setStyleSheet(f"color: {COLORS['accent']}; font-size: 10px; font-weight: bold;")
            item_line.addWidget(iamt)
            item_line.addStretch()
            idet = QLabel(detail)
            idet.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
            item_line.addWidget(idet)
            cv.addLayout(item_line)

        return card

    def _make_supplement_row(self, supp: Dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 6px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        rh = QHBoxLayout(row)
        rh.setContentsMargins(12, 6, 12, 6)
        rh.setSpacing(12)

        name = QLabel(supp['name'])
        name.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        name.setStyleSheet(f"color: {COLORS['text']};")
        name.setMinimumWidth(100)
        rh.addWidget(name)

        dose = QLabel(supp['dose'])
        dose.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 11px;")
        dose.setMinimumWidth(70)
        rh.addWidget(dose)

        timing = QLabel(supp['timing'])
        timing.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px;")
        timing.setMinimumWidth(130)
        rh.addWidget(timing)

        purpose = QLabel(supp['purpose'])
        purpose.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px;")
        purpose.setMinimumWidth(120)
        rh.addWidget(purpose)

        note = QLabel(supp['note'])
        note.setStyleSheet(f"color: {COLORS['success']}; font-size: 10px;")
        rh.addWidget(note)
        rh.addStretch()
        return row

    def _make_water_row(self, item: Tuple) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 6px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        rh = QHBoxLayout(row)
        rh.setContentsMargins(12, 6, 12, 6)
        rh.setSpacing(12)

        name = QLabel(item[0])
        name.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        name.setStyleSheet(f"color: {COLORS['text']};")
        name.setMinimumWidth(100)
        rh.addWidget(name)

        std = QLabel(item[1])
        std.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 11px;")
        std.setMinimumWidth(120)
        rh.addWidget(std)

        note = QLabel(item[2])
        note.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px;")
        rh.addWidget(note)
        rh.addStretch()
        return row

    def _on_week_changed(self, idx: int):
        self.current_week = idx + 1
        phase = NutritionParser.get_phase(self.current_week)
        self.btn_highcarb.setVisible(phase >= 3)
        self.btn_medium.setVisible(phase >= 3)
        if self.current_day_type in ('high_carb', 'medium') and phase < 3:
            self.current_day_type = 'training'
            self.btn_training.setChecked(True)
        self._refresh_all()

    def _on_day_type_changed(self, day_type: str):
        self.current_day_type = day_type
        for btn in [self.btn_training, self.btn_rest, self.btn_medium, self.btn_highcarb]:
            btn.setChecked(btn.property('day_type') == day_type)
        self._refresh_all()

    def _refresh_all(self):
        phase = NutritionParser.get_phase(self.current_week)
        info = PHASE_INFO[phase]
        macros = NutritionParser.get_macros(self.current_week, self.current_day_type)
        meals = NutritionParser.get_meals()
        supplements = NutritionParser.get_supplements()
        hydration = NutritionParser.get_hydration()
        daily = NutritionParser.get_daily_totals(meals)

        day_type_name = {'training': '训练日', 'rest': '休息日', 'medium': '中碳日', 'high_carb': '高碳日'}[self.current_day_type]
        self.phase_label.setText(
            f"📍 {info['name']} ({info['weeks']}) — {info['desc']} | 当前: {day_type_name} 营养方案"
        )

        macro_keys = [('kcal', 0), ('protein', 1), ('carbs', 2), ('fat', 3)]
        for key, _ in macro_keys:
            panel = self.macro_labels[key]
            val_label = panel.findChild(QLabel, 'macro_value')
            if val_label:
                val_label.setText(str(macros[key]))

        self._update_macro_panel('kcal', macros['kcal'], daily.get('kcal', 0), 'kcal')
        self._update_macro_panel('protein', macros['protein'], daily.get('protein', 0), 'g')
        self._update_macro_panel('carbs', macros['carbs'], daily.get('carbs', 0), 'g')
        self._update_macro_panel('fat', macros['fat'], daily.get('fat', 0), 'g')

        self.protein_pct_label.setText(
            f"蛋白质占比: {macros['protein_pct']}% (目标) | 五餐合计: "
            f"P{daily['protein']}g C{daily['carbs']}g F{daily['fat']}g = {daily['kcal']}kcal"
        )

        while self.meals_grid.count():
            item = self.meals_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, meal in enumerate(meals):
            card = self._make_meal_card(meal)
            self.meals_grid.addWidget(card, i // 3, i % 3)

        totals = NutritionParser.get_daily_totals(meals)
        target_p = macros['protein']
        diff_p = totals['protein'] - target_p
        sign = '+' if diff_p > 0 else ''
        self.total_summary.setText(
            f"🍽 五餐合计: 蛋白质 {totals['protein']}g (目标 {target_p}g, {sign}{diff_p}g) | "
            f"碳水 {totals['carbs']}g (目标 {macros['carbs']}g) | "
            f"脂肪 {totals['fat']}g (目标 {macros['fat']}g) | "
            f"热量 {totals['kcal']}kcal (目标 {macros['kcal']}kcal)"
        )

        while self.supplement_table.layout().count():
            item = self.supplement_table.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in supplements:
            self.supplement_table.layout().addWidget(self._make_supplement_row(s))

        while self.water_table.layout().count():
            item = self.water_table.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for w in hydration:
            self.water_table.layout().addWidget(self._make_water_row(w))

    def _update_macro_panel(self, key: str, target: float, actual: float, unit: str):
        panel = self.macro_labels[key]
        val_label = panel.findChild(QLabel, 'macro_value')
        cmp_label = panel.findChild(QLabel, 'macro_cmp')
        if val_label:
            val_label.setText(str(target))
        if cmp_label:
            if unit == 'kcal':
                diff_str = f"五餐合计: {actual}kcal (求值{target}kcal)"
            else:
                diff_str = f"五餐合计: {actual}g (目标{target}g)"
            cmp_label.setText(diff_str)
