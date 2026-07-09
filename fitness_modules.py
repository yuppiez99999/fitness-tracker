# -*- coding: utf-8 -*-
"""
健身软件核心模块 v7.0 — 数据模型 + 动作库 + 训练计划 + UI页面
依赖: PySide6, matplotlib, pandas, numpy
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QFont, QColor, QIcon, QImage
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea,
    QDialog, QLineEdit, QFormLayout, QMessageBox, QFileDialog, QComboBox,
    QProgressBar, QFrame, QSplitter, QListWidget, QListWidgetItem, QTextEdit,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QSizePolicy, QSlider
)

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import MaxNLocator

# 中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


# ═══════════════════════════════════════════════════════════
# 配置与常量
# ═══════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '体重体脂监控')
CHART_DIR = os.path.join(DATA_DIR, '图表')
REPORT_DIR = os.path.join(DATA_DIR, '报告')
DATA_FILE = os.path.join(DATA_DIR, '体脂体重.txt')
EXERCISES_JSON = os.path.join(DATA_DIR, 'exercises_matched.json')
GIF_DIR = os.path.join(DATA_DIR, 'exercises_gif')
PLAN_MD = os.path.join(DATA_DIR, '8周增肌塑形计划.md')

for d in [DATA_DIR, CHART_DIR, REPORT_DIR, GIF_DIR]:
    os.makedirs(d, exist_ok=True)

# 颜色主题(暗色)
COLORS = {
    'bg': '#0d1117', 'card': '#161b22', 'border': '#30363d',
    'text': '#e6edf3', 'subtext': '#8b949e', 'primary': '#58a6ff',
    'success': '#3fb950', 'warning': '#d29922', 'danger': '#f85149',
    'purple': '#bc8cff', 'cyan': '#39d2c0',
}

# 体测指标完整列(扩展12项)
BODY_COLUMNS = [
    '日期', '体重(kg)', '体脂率(%)', '肌肉量(kg)', '内脏脂肪等级',
    '基础代谢率(kcal)', '体水分率(%)', '骨量(kg)', 'BMI',
    '骨骼肌率(%)', '腰围(cm)', '臀围(cm)'
]

# 训练计划结构(8周增肌塑形,6练1休)
TRAINING_SCHEDULE = [
    {'day': '周一', 'title': '胸 + 三头', 'focus': '上胸强化日', 'icon': '💪'},
    {'day': '周二', 'title': '背 + 二头', 'focus': '背部宽度+厚度日', 'icon': '🔙'},
    {'day': '周三', 'title': '腿 + 臀', 'focus': '下肢力量日', 'icon': '🦵'},
    {'day': '周四', 'title': '肩 + 核心', 'focus': '三角肌+下腹强化日', 'icon': '🙆'},
    {'day': '周五', 'title': '全身循环HIIT', 'focus': '低冲击燃脂', 'icon': '🔥'},
    {'day': '周六', 'title': '有氧 + 核心', 'focus': '低强度恢复', 'icon': '🏃'},
    {'day': '周日', 'title': '休息 + 恢复', 'focus': '主动恢复', 'icon': '😴'},
]


# ═══════════════════════════════════════════════════════════
# 数据模型层
# ═══════════════════════════════════════════════════════════

class BodyDataModel:
    """体测数据模型 — 管理体重体脂等12项指标"""

    def __init__(self):
        self.df = self._load()
        self.target_weight = 67.0  # 目标体重(kg)
        self.target_bodyfat = 16.5

    def _load(self) -> pd.DataFrame:
        """加载体测数据,兼容旧格式(3列)和新格式(12列)"""
        if not os.path.exists(DATA_FILE):
            return pd.DataFrame(columns=BODY_COLUMNS)
        for enc in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030']:
            try:
                df = pd.read_csv(DATA_FILE, encoding=enc)
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
                # 补齐缺失列
                for col in BODY_COLUMNS:
                    if col not in df.columns:
                        df[col] = np.nan
                df = df[BODY_COLUMNS].sort_values('日期').reset_index(drop=True)
                return df
            except Exception:
                continue
        return pd.DataFrame(columns=BODY_COLUMNS)

    def save(self):
        self.df.to_csv(DATA_FILE, index=False, encoding='utf-8')

    def add_record(self, date: str, weight: float, fat: Optional[float] = None,
                   **kwargs):
        """添加或更新记录"""
        new_row = {'日期': date, '体重(kg)': weight, '体脂率(%)': fat}
        for k, v in kwargs.items():
            if k in BODY_COLUMNS:
                new_row[k] = v
        # 合并到df
        mask = self.df['日期'] == date
        if mask.any():
            for k, v in new_row.items():
                if v is not None:
                    self.df.loc[mask, k] = v
        else:
            full_row = {col: new_row.get(col, np.nan) for col in BODY_COLUMNS}
            self.df = pd.concat([self.df, pd.DataFrame([full_row])], ignore_index=True)
        self.df = self.df.sort_values('日期').reset_index(drop=True)
        self.save()

    def delete_record(self, date: str):
        self.df = self.df[self.df['日期'] != date].reset_index(drop=True)
        self.save()

    def get_stats(self) -> Dict[str, Any]:
        """计算统计数据"""
        n = len(self.df)
        if n == 0:
            return {'count': 0}
        latest = self.df.iloc[-1]
        first = self.df.iloc[0]
        days = (pd.to_datetime(latest['日期']) - pd.to_datetime(first['日期'])).days
        init_w = first['体重(kg)']
        cur_w = latest['体重(kg)']
        has_fat = self.df['体脂率(%)'].dropna()
        cur_fat = latest['体脂率(%)'] if pd.notna(latest['体脂率(%)']) else (
            has_fat.iloc[-1] if len(has_fat) > 0 else np.nan)

        # 体脂变化：用第一个有体脂数据的记录作为起点，当前 - 初始，降低为负
        init_fat = has_fat.iloc[0] if len(has_fat) > 0 else np.nan
        fat_change = (cur_fat - init_fat) if pd.notna(init_fat) and pd.notna(cur_fat) else np.nan

        # 瘦体重
        lean = cur_w * (1 - cur_fat / 100) if pd.notna(cur_fat) else np.nan
        init_lean = init_w * (1 - (first['体脂率(%)'] if pd.notna(first['体脂率(%)']) else cur_fat) / 100) if pd.notna(init_w) else np.nan

        return {
            'count': n, 'days': days,
            'init_weight': init_w, 'cur_weight': cur_w,
            'weight_change': cur_w - init_w,
            'cur_fat': cur_fat,
            'fat_change': fat_change,
            'cur_lean': lean, 'lean_change': lean - init_lean if pd.notna(init_lean) else np.nan,
            'to_target_w': cur_w - self.target_weight,
            'to_target_f': cur_fat - self.target_bodyfat if pd.notna(cur_fat) else np.nan,
            'latest_date': latest['日期'], 'first_date': first['日期'],
        }

    def predict_target_date(self, target: float, col: str = '体重(kg)') -> Optional[str]:
        """线性预测达标日"""
        valid = self.df[self.df[col].notna()].copy()
        if len(valid) < 5:
            return None
        valid['days'] = (pd.to_datetime(valid['日期']) - pd.to_datetime(valid['日期'].iloc[0])).dt.days
        z = np.polyfit(valid['days'].values, valid[col].values, 1)
        if abs(z[0]) < 1e-6:
            return None
        pred_days = (target - z[1]) / z[0]
        if pred_days <= 0:
            return '已达'
        pred_date = pd.to_datetime(valid['日期'].iloc[0]) + timedelta(days=int(pred_days))
        return pred_date.strftime('%Y-%m-%d')


class ExerciseLibrary:
    """动作库 — 加载JSON + GIF路径管理"""

    def __init__(self):
        self.exercises: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(EXERCISES_JSON):
            with open(EXERCISES_JSON, 'r', encoding='utf-8') as f:
                self.exercises = json.load(f)

    def get_by_media_id(self, media_id: str) -> Optional[Dict]:
        for ex in self.exercises:
            if ex.get('media_id') == media_id:
                return ex
        return None

    def get_by_name(self, name_cn: str) -> Optional[Dict]:
        for ex in self.exercises:
            if ex.get('name_cn') == name_cn:
                return ex
        return None

    def search(self, keyword: str) -> List[Dict]:
        kw = keyword.lower().strip()
        if not kw:
            return self.exercises
        return [e for e in self.exercises
                if kw in e.get('name_cn', '').lower() or
                kw in e.get('name_en', '').lower() or
                kw in e.get('target', '').lower() or
                kw in e.get('category', '').lower()]

    def gif_path(self, media_id: str) -> Optional[str]:
        if not media_id:
            return None
        p = os.path.join(GIF_DIR, f'{media_id}.gif')
        return p if os.path.exists(p) else None


# ═══════════════════════════════════════════════════════════
# 训练计划解析
# ═══════════════════════════════════════════════════════════

class TrainingPlanParser:
    """从8周增肌塑形计划.md解析每日训练动作"""

    def __init__(self):
        self.raw_text = ''
        self._load()

    def _load(self):
        if os.path.exists(PLAN_MD):
            with open(PLAN_MD, 'r', encoding='utf-8') as f:
                self.raw_text = f.read()

    def get_daily_exercises(self) -> Dict[str, List[Dict]]:
        """解析markdown表格,返回每日动作列表(只解析第三章3.1-3.7的主训练+收尾表格)
        返回: {'周一': [{'name':'上斜哑铃卧推','sets':'4×8-10','target':'上胸','media_id':'ns0SIbU','tip':'...'}], ...}
        """
        result = {d['day']: [] for d in TRAINING_SCHEDULE}
        if not self.raw_text:
            return result

        lines = self.raw_text.split('\n')
        current_day = None
        section = None  # None | '热身' | '主训练' | '收尾' | '拉伸'
        # 第四章开始后立即停止(章节标志: ## 四
        in_chapter_three = False

        # 周X章节匹配模式
        day_section_map = {
            '### 3.1': '周一', '### 3.2': '周二', '### 3.3': '周三',
            '### 3.4': '周四', '### 3.5': '周五', '### 3.6': '周六',
            '### 3.7': '周日',
        }

        for line in lines:
            # 进入第三章
            if line.strip().startswith('## 三、'):
                in_chapter_three = True
                continue
            # 离开第三章(遇到第四章或更高级章节)立即终止
            if in_chapter_three and (line.strip().startswith('## 四、') or
                                      line.strip().startswith('## 五、') or
                                      line.strip().startswith('## 六、') or
                                      line.strip().startswith('## 七、') or
                                      line.strip().startswith('## 八、') or
                                      line.strip().startswith('## 九、')):
                break

            if not in_chapter_three:
                continue

            # 识别周X章节
            matched_day = False
            for prefix, day in day_section_map.items():
                if line.startswith(prefix):
                    current_day = day
                    section = None
                    matched_day = True
                    break
            if matched_day:
                continue

            if current_day is None:
                continue

            # 周日休息日不解析任何表格
            if current_day == '周日':
                continue

            # 识别当前段落(主训练/收尾/热身/拉伸)
            stripped = line.strip()
            if stripped.startswith('####'):
                if '主训练' in stripped:
                    section = '主训练'
                elif '收尾' in stripped:
                    section = '收尾'
                elif '热身' in stripped:
                    section = '热身'
                elif '拉伸' in stripped:
                    section = '拉伸'
                else:
                    section = None
                continue

            # 只解析主训练和收尾表格
            if section not in ('主训练', '收尾'):
                continue

            # 解析表格行
            if not stripped.startswith('|') or '---' in stripped:
                continue

            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) < 3:
                continue

            # 主训练表格两种格式:
            #   常规力量训练(6列): | 序号 | 动作 | 组数×次数 | 目标肌群 | 重点提示 | media_id |
            #   HIIT循环训练(5列): | 序号 | 动作 | 目标肌群 | 强度提示 | media_id |
            if section == '主训练':
                if cells[0].isdigit() and len(cells) >= 5:
                    name = cells[1]
                    if not name or name == '动作' or name.startswith('---'):
                        continue
                    if len(cells) >= 6:
                        # 6列: 标准力量训练
                        sets_reps = cells[2]
                        target = cells[3]
                        tip = cells[4]
                        media_id = cells[5]
                    else:
                        # 5列: HIIT循环(没有组数列,使用"40s+20s休息")
                        sets_reps = '40秒+20秒休息'
                        target = cells[2]
                        tip = cells[3]
                        media_id = cells[4]
                    # 过滤media_id为null或空
                    if media_id and media_id != 'media_id' and not media_id.startswith('---'):
                        if media_id.lower().startswith('null'):
                            media_id = ''  # 自重深蹲/开合跳没有GIF
                        result[current_day].append({
                            'name': name, 'sets': sets_reps, 'target': target,
                            'tip': tip, 'media_id': media_id,
                        })
            # 收尾表格: | 动作 | 组数×时间 | 目标 | media_id |
            elif section == '收尾':
                # 跳过表头行
                if cells[0] in ('动作', '部位', '项目') or cells[0].startswith('---'):
                    continue
                # 跳过空media_id列
                if len(cells) >= 4:
                    name = cells[0]
                    sets_reps = cells[1]
                    target = cells[2] if len(cells) > 2 else ''
                    media_id = cells[3] if len(cells) > 3 else ''
                    if name and media_id and media_id != 'media_id' and not media_id.startswith('---'):
                        result[current_day].append({
                            'name': name, 'sets': sets_reps, 'target': target,
                            'tip': '收尾动作', 'media_id': media_id,
                        })

        return result


# ═══════════════════════════════════════════════════════════
# UI组件 — 动作详情弹窗
# ═══════════════════════════════════════════════════════════

class ExerciseDetailDialog(QDialog):
    """动作详情弹窗 — QMovie播GIF + 步骤教学 + 肌群信息"""

    def __init__(self, exercise: Dict, exercise_lib: ExerciseLibrary, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.lib = exercise_lib
        self.movie = None
        self._build_ui()

    def _build_ui(self):
        name = self.exercise.get('name_cn', '未知动作')
        self.setWindowTitle(f'动作示范 — {name}')
        self.setMinimumSize(700, 600)
        self.setStyleSheet(f"background-color: {COLORS['bg']}; color: {COLORS['text']};")

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel(f'🏋️  {name}')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']}; padding: 10px;")
        layout.addWidget(title)

        # 英文名 + 器材
        en_name = self.exercise.get('name_en', '')
        equip = self.exercise.get('equipment', '')
        info = QLabel(f'English: {en_name}    |    器材: {equip}')
        info.setStyleSheet(f"color: {COLORS['subtext']}; padding: 0 10px;")
        layout.addWidget(info)

        # 主体: 左GIF + 右信息
        body = QHBoxLayout()

        # 左侧GIF
        gif_frame = QFrame()
        gif_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 8px;")
        gif_frame.setMinimumSize(320, 320)
        gif_layout = QVBoxLayout(gif_frame)
        self.gif_label = QLabel('加载中...')
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMinimumSize(300, 300)
        gif_layout.addWidget(self.gif_label)
        body.addWidget(gif_frame)

        # 右侧信息
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 8px;")
        info_layout = QVBoxLayout(info_frame)

        # 肌群信息
        target = self.exercise.get('target', '')
        muscle = self.exercise.get('muscle_group', '')
        secondary = self.exercise.get('secondary_muscles', [])
        sec_str = ', '.join(secondary) if isinstance(secondary, list) else str(secondary)

        for label, value, color in [
            ('🎯 目标肌群', target, COLORS['primary']),
            ('💪 主肌群', muscle, COLORS['success']),
            ('🔄 协同肌群', sec_str, COLORS['warning']),
        ]:
            row = QLabel(f'{label}: {value}')
            row.setFont(QFont('Microsoft YaHei', 10))
            row.setStyleSheet(f"color: {color}; padding: 4px;")
            row.setWordWrap(True)
            info_layout.addWidget(row)

        info_layout.addSpacing(10)

        # 步骤标题
        steps_title = QLabel('📋 动作步骤')
        steps_title.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        steps_title.setStyleSheet(f"color: {COLORS['purple']};")
        info_layout.addWidget(steps_title)

        # 步骤列表
        steps = self.exercise.get('instruction_steps_zh', [])
        if not steps:
            instructions = self.exercise.get('instructions_zh', '')
            if instructions:
                steps = [s.strip() for s in instructions.split('。') if s.strip()]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        steps_widget = QWidget()
        steps_layout = QVBoxLayout(steps_widget)
        for i, step in enumerate(steps, 1):
            step_label = QLabel(f'{i}. {step}')
            step_label.setWordWrap(True)
            step_label.setStyleSheet(f"color: {COLORS['text']}; padding: 3px;")
            steps_layout.addWidget(step_label)
        steps_layout.addStretch()
        scroll.setWidget(steps_widget)
        info_layout.addWidget(scroll)

        body.addWidget(info_frame)
        layout.addLayout(body, stretch=1)

        # GIF播放控制
        ctrl = QHBoxLayout()
        self.btn_play = QPushButton('⏸ 暂停')
        self.btn_play.clicked.connect(self._toggle_play)
        ctrl.addWidget(self.btn_play)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self._load_gif()

    def _load_gif(self):
        """加载GIF动画"""
        media_id = self.exercise.get('media_id', '')
        gif_path = self.lib.gif_path(media_id)
        if gif_path is None:
            self.gif_label.setText('🎬\n无GIF资源\n\n(该动作未匹配到\n动作示范数据)')
            self.gif_label.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 14px;")
            self.btn_play.setEnabled(False)
            return

        from PySide6.QtGui import QMovie
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(300, 300))
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def _toggle_play(self):
        if self.movie is None:
            return
        if self.movie.state() == QMovie.Running:
            self.movie.stop()
            self.btn_play.setText('▶ 播放')
        else:
            self.movie.start()
            self.btn_play.setText('⏸ 暂停')


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
        today = datetime.now().strftime('%Y-%m-%d')
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
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(REPORT_DIR, f'体测报告_{ts}.txt')
        pred_w = self.model.predict_target_date(self.model.target_weight)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f'═══ 体测报告 {datetime.now().strftime("%Y-%m-%d %H:%M")} ═══\n\n')
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

        plot_df = df.copy()
        plot_df['日期_dt'] = pd.to_datetime(plot_df['日期'])
        plot_df = plot_df.sort_values('日期_dt')

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
        # 体重
        self.ax.plot(plot_df['日期_dt'], plot_df['体重(kg)'],
                     color=COLORS['primary'], linewidth=2, marker='o', markersize=3,
                     markerfacecolor=COLORS['primary'], label='体重', zorder=3)
        # 7日EMA
        ema = plot_df['体重(kg)'].ewm(span=7, adjust=False).mean()
        self.ax.plot(plot_df['日期_dt'], ema, color=COLORS['cyan'],
                     linewidth=1.5, linestyle='--', alpha=0.8, label='7日EMA')
        # 目标线
        self.ax.axhline(y=self.model.target_weight, color=COLORS['danger'],
                        linestyle='--', linewidth=1, alpha=0.6,
                        label=f"目标{self.model.target_weight}kg")

        # 体脂(双轴)
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

        # 达标日预测标注
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
        """体成分构成(最新 vs 首次)"""
        latest = plot_df.iloc[-1]
        first = plot_df.iloc[0]
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
        # 清除旧
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

        # GIF缩略图(静态首帧)
        media_id = ex.get('media_id', '')
        gif_path = self.lib.gif_path(media_id)
        thumb = QLabel()
        thumb.setAlignment(Qt.AlignCenter)
        thumb.setFixedSize(180, 130)
        thumb.setStyleSheet(f"background-color: {COLORS['bg']}; border-radius: 4px;")
        if gif_path:
            from PIL import Image
            try:
                img = Image.open(gif_path)
                img.seek(0)
                img = img.convert('RGBA')
                img.thumbnail((180, 130))
                from PySide6.QtGui import QImage
                data = img.tobytes('raw', 'RGBA')
                qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                thumb.setPixmap(QPixmap.fromImage(qimg).scaled(180, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                thumb.setText('🎬')
        else:
            thumb.setText('🎬')
            thumb.setStyleSheet(f"background-color: {COLORS['bg']}; color: {COLORS['subtext']}; font-size: 28px; border-radius: 4px;")
        cl.addWidget(thumb)

        # 动作名
        name = QLabel(ex.get('name_cn', '未知'))
        name.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        name.setStyleSheet(f"color: {COLORS['text']};")
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignCenter)
        cl.addWidget(name)

        # 目标肌群
        target = QLabel(ex.get('target', ''))
        target.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        target.setAlignment(Qt.AlignCenter)
        cl.addWidget(target)

        # 点击事件
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
    """训练计划 — 周历视图 + 每日动作列表 + 点击跳转详情"""

    def __init__(self, plan: TrainingPlanParser, lib: ExerciseLibrary):
        super().__init__()
        self.plan = plan
        self.lib = lib
        self.daily_exercises = plan.get_daily_exercises()
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)

        # 顶部
        top = QHBoxLayout()
        title = QLabel('📅 8周增肌塑形训练计划')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        # 周次选择
        self.combo_week = QComboBox()
        self.combo_week.addItems([f'第{w}周' for w in range(1, 9)])
        self.combo_week.setStyleSheet(f"background-color: {COLORS['card']}; color: {COLORS['text']}; "
                                      f"padding: 4px; border-radius: 4px;")
        top.addWidget(self.combo_week)
        layout.addLayout(top)

        # 进度提示
        note = QLabel('💡 点击动作卡片查看GIF示范 + 详细步骤教学')
        note.setStyleSheet(f"color: {COLORS['subtext']}; padding: 4px;")
        layout.addWidget(note)

        # 7天卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(8)

        for i, sched in enumerate(TRAINING_SCHEDULE):
            day_card = self._make_day_card(sched)
            grid.addWidget(day_card, i // 3, i % 3)

        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

    def _make_day_card(self, sched: Dict) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 10px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 10, 10, 10)

        # 头部
        header = QLabel(f"{sched['icon']}  {sched['day']}  {sched['title']}")
        header.setFont(QFont('Microsoft YaHei', 11, QFont.Bold))
        header.setStyleSheet(f"color: {COLORS['primary']};")
        cl.addWidget(header)

        focus = QLabel(sched['focus'])
        focus.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        cl.addWidget(focus)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        cl.addWidget(sep)

        # 动作列表
        exercises = self.daily_exercises.get(sched['day'], [])
        if not exercises:
            hint = QLabel('🌿 主动恢复日\n慢走6000-8000步\n泡沫轴放松 + 全身拉伸')
            hint.setStyleSheet(f"color: {COLORS['success']}; padding: 8px;")
            hint.setWordWrap(True)
            cl.addWidget(hint)
        else:
            for ex in exercises:
                ex_btn = self._make_exercise_button(ex)
                cl.addWidget(ex_btn)

        cl.addStretch()
        return card

    def _make_exercise_button(self, ex: Dict) -> QPushButton:
        name = ex.get('name', '')
        sets = ex.get('sets', '')
        target = ex.get('target', '')
        media_id = ex.get('media_id', '')

        text = f'{name}  {sets}'
        if target:
            text += f'\n  🎯 {target[:20]}'

        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {COLORS['bg']}; color: {COLORS['text']};
                          border: 1px solid {COLORS['border']}; border-radius: 6px;
                          padding: 8px; text-align: left; font-size: 10px; }}
            QPushButton:hover {{ background-color: {COLORS['card']}; border: 1px solid {COLORS['primary']}; }}
        """)
        btn.setMinimumHeight(45)

        # 点击跳转详情
        ex_data = self.lib.get_by_media_id(media_id) if media_id else None
        if ex_data is None:
            ex_data = {
                'name_cn': name, 'name_en': '', 'target': target,
                'muscle_group': '', 'secondary_muscles': [],
                'equipment': '', 'instructions_zh': '', 'instruction_steps_zh': [],
                'media_id': media_id, 'matched': False,
            }
        btn.clicked.connect(lambda *args, e=ex_data: self._show_exercise(e))
        return btn

    def _show_exercise(self, ex: Dict):
        dlg = ExerciseDetailDialog(ex, self.lib, self)
        dlg.exec()
