# -*- coding: utf-8 -*-
"""
体脂体重监控 + 健身计划软件 v8.0 — PySide6 重构版
基于市场主流健身软件(Keep/Fitbod/Hevy/Strong)特性优化

功能模块:
  1. 📊 体测仪表盘 — 12项体测指标 + 快速录入 + 历史记录
  2. 📈 趋势分析 — 7日EMA平滑曲线 + 目标达标日预测 + 体成分饼图
  3. 🏋️ 动作示范库 — 38个动作 GIF动画 + 中文步骤教学 + 肌群信息
  4. 📅 训练计划 — 20周塑形冲刺 + 三阶段周期化 + 点击动作看示范
  5. 🍽 饮食与补剂 — 三阶段营养方案 + 五餐明细 + 补剂表 + 饮水指南

技术栈: PySide6 + matplotlib + pandas + Pillow
数据源: exercises-dataset (GitHub: yuppiez99999/exercises-dataset)
"""

import sys
import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QPushButton, QMessageBox
)

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitness_modules import (
    BodyDataModel, ExerciseLibrary, TrainingPlanParser, NutritionParser,
    DashboardPage, TrendChartPage, ExerciseLibraryPage, TrainingPlanPage, NutritionPage,
    COLORS,
)


class MainWindow(QMainWindow):
    """主窗口 — 4页Tab布局"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('健身监控 v8.0 — 20周塑形冲刺 · 体测数据 + 动作示范 + 训练计划')
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self._apply_global_style()

        # 初始化数据模型
        self.body_model = BodyDataModel()
        self.exercise_lib = ExerciseLibrary()
        self.training_plan = TrainingPlanParser()

        # 构建UI
        self._build_ui()
        self._update_status()

    def _apply_global_style(self):
        """全局暗色主题样式"""
        self.setStyleSheet(f"""
            QMainWindow {{ background-color: {COLORS['bg']}; }}
            QTabWidget::pane {{ border: 1px solid {COLORS['border']}; border-radius: 8px;
                                background-color: {COLORS['bg']}; }}
            QTabBar::tab {{ background-color: {COLORS['card']}; color: {COLORS['subtext']};
                            padding: 10px 20px; margin: 2px; border-radius: 6px 6px 0 0;
                            font-size: 12px; font-weight: bold; }}
            QTabBar::tab:selected {{ background-color: {COLORS['primary']}; color: white; }}
            QTabBar::tab:hover:!selected {{ background-color: {COLORS['border']}; }}
            QStatusBar {{ background-color: {COLORS['card']}; color: {COLORS['subtext']}; }}
            QMenuBar {{ background-color: {COLORS['card']}; color: {COLORS['text']}; }}
            QMenuBar::item:selected {{ background-color: {COLORS['primary']}; }}
            QMenu {{ background-color: {COLORS['card']}; color: {COLORS['text']};
                     border: 1px solid {COLORS['border']}; }}
            QMenu::item:selected {{ background-color: {COLORS['primary']}; }}
        """)

    def _build_ui(self):
        # 顶部标题栏
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet(f"background-color: {COLORS['card']}; border-bottom: 1px solid {COLORS['border']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 8, 16, 8)

        title = QLabel('💪 健身监控 v8.0')
        title.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        hl.addWidget(title)

        subtitle = QLabel('体测数据 · 动作示范 · 训练计划 · 饮食补剂 一体化')
        subtitle.setStyleSheet(f"color: {COLORS['subtext']};")
        hl.addWidget(subtitle)
        hl.addStretch()

        # 数据统计速览
        self.lbl_quick_stats = QLabel('加载中...')
        self.lbl_quick_stats.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        hl.addWidget(self.lbl_quick_stats)

        self.setMenuWidget(header)

        # 中央Tab部件
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 页面1: 仪表盘
        self.page_dashboard = DashboardPage(self.body_model)
        self.page_dashboard.record_added.connect(self._on_data_changed)
        self.tabs.addTab(self.page_dashboard, '📊 仪表盘')

        # 页面2: 趋势分析
        self.page_trend = TrendChartPage(self.body_model)
        self.tabs.addTab(self.page_trend, '📈 趋势分析')

        # 页面3: 动作示范库
        self.page_exercises = ExerciseLibraryPage(self.exercise_lib)
        self.tabs.addTab(self.page_exercises, f'🏋️ 动作库 ({len(self.exercise_lib.exercises)})')

        # 页面4: 训练计划
        self.page_plan = TrainingPlanPage(self.training_plan, self.exercise_lib)
        self.tabs.addTab(self.page_plan, '📅 训练计划(20周)')

        # 页面5: 饮食与补剂
        self.page_nutrition = NutritionPage()
        self.tabs.addTab(self.page_nutrition, '🍽 饮食与补剂')

        # 状态栏
        self.statusBar().showMessage('就绪 · 5个模块已加载')

    def _update_status(self):
        """更新顶部快速统计"""
        stats = self.body_model.get_stats()
        if stats['count'] == 0:
            self.lbl_quick_stats.setText('暂无数据')
            return
        w = stats['cur_weight']
        f = stats['cur_fat']
        fat_text = f' / {f:.1f}%体脂' if f == f else ''  # NaN检查
        self.lbl_quick_stats.setText(f'当前: {w:.1f}kg{fat_text}  ·  {stats["count"]}条记录')

    def _on_data_changed(self):
        """数据变化时刷新所有页面"""
        self.page_dashboard.refresh()
        self.page_trend._draw()
        self._update_status()
        self.statusBar().showMessage('数据已更新', 3000)

    def closeEvent(self, event):
        """关闭时保存"""
        self.body_model.save()
        event.accept()


# ═══════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('健身监控 v7.0')

    # 全局字体
    font = QFont('Microsoft YaHei', 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
