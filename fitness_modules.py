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
from typing import Optional, List, Dict, Tuple, Any

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
PLAN_MD = os.path.join(DATA_DIR, '12月底塑形冲刺计划_v2.1_宽背窄腰_执行版.md')

for d in [DATA_DIR, CHART_DIR, REPORT_DIR, GIF_DIR]:
    os.makedirs(d, exist_ok=True)

# 颜色主题(暗色)
COLORS = {
    'bg': '#FBF7F0', 'card': '#FFFFFF', 'border': '#E0D8CC',
    'text': '#2C2416', 'subtext': '#8C8278', 'primary': '#4A8FE7',
    'success': '#2DA44E', 'warning': '#BF8600', 'danger': '#CF222E',
    'purple': '#8250DF', 'cyan': '#1B9AAA', 'accent': '#D4A017',
    # v5.9.2 新增特殊主题色
    'hiit_fg': '#E85D3A',     # HIIT 渐变前景
    'hiit_bg': '#FDE8E3',     # HIIT 渐变背景
    'liss_fg': '#2DA44E',     # LISS 渐变前景
    'liss_bg': '#E6F4EA',     # LISS 渐变背景
    'rest_fg': '#8250DF',     # 完全休息前景
}

# 肌肉群 Emoji 映射 (缺GIF时的占位图标)
MUSCLE_EMOJI = {
    '胸': '💪',
    '上胸': '⬆️',
    '下胸': '⬇️',
    '背': '🏋️',
    '背部': '🏋️',
    '二头': '💪',
    '三头': '🤜',
    '腿': '🦵',
    '股四头': '🦵',
    '臀': '🍑',
    '小腿': '🦶',
    '肩': '🙆',
    '三角肌': '🙆',
    '核心': '🔥',
    '腹': '🔥',
    '腹斜': '🔥',
    '有氧': '🏃',
    '波比': '🔥',
    '壶铃': '🪨',
    '跳绳': '⤴️',
    '冲刺': '⚡',
    'HIIT': '⚡',
    'TABATA': '⚡',
    'LISS': '🚶',
    '徒手': '✊',
    '俯卧撑': '🤸',
    '下压': '⏬',
    '举腿': '🦵',
    '悬挂': '🔗',
    '弹力带': '🎀',
    '绳索': '🪢',
    '杠铃': '🏋️',
    '哑铃': '🥊',
    '默认': '🎯',
}

# 真空腹训练文字教程 (数据集无此动作, 通过弹窗提供专业指导)
VACUUM_TUTORIAL = [
    '选择姿势: 四点支撑（双手双膝着地）或跪姿或站姿, 新手推荐四点支撑, 最容易感知腹横肌。',
    '深吸一口气, 然后用力呼气, 把肺里所有空气都吐尽, 这是关键的一步 —— 必须完全排空。',
    '保持呼气末状态, 用力收腹, 想象把肚脐往脊椎方向拉, 同时收紧整个腹部区域（腹横肌收缩）。',
    '保持收缩状态 15-60 秒, 此期间用胸式呼吸（吸气时胸腔扩张但腹部不要鼓起）, 让腹部持续"内收"。',
    '放松呼气, 然后重复。每组 60 秒, 每天 3-5 组, 早晚各一次。',
    '进阶技巧: 保持真空腹时可配合站立/走路, 形成"动态真空腹", 腹横肌刺激翻倍。',
    '常见错误: ❌ 憋气（会导致血压飙升, 头晕）❌ 用腹直肌发力（应该深层收缩）❌ 腹直肌鼓起（必须内收）。',
    '⚠ 健康提示: 孕妇、高血压、心脏病患者不宜做; 训练中如感头晕立即停止, 正常呼吸休息。',
    '预期效果: 研究显示持续 8 周真空腹训练, 腰围可减少 2-3cm (视觉上更窄), 配合体脂降低效果更佳。',
    '训练时间安排: 早晨起床后空腹（代谢唤醒）+ 训练后（巩固效果）+ 睡前（替代腹部呼吸, 提升睡眠质量）。',
]

# 其他流程块通用教程 (HIIT/LISS/其他复合训练)
FLOW_TUTORIAL = {
    'hiit_loop': [
        'HIIT（高强度间歇训练）原理: 短时间全力运动 + 短休息, 提升心率至 150-170 bpm。',
        '每个动作 40 秒全力训练, 20 秒休息, 6 个动作为一组, 4 组循环。',
        '组间休息 90 秒, 让心率短暂恢复。',
        '⚠ 安全提示: 心血管疾病患者不宜做, 训练前充分热身, 训练中如感不适立即停止。',
        '预期效果: HIIT 比 LISS 燃脂效率高 30%, 运动后过量氧耗 (EPOC) 可持续 24 小时。',
    ],
    'liss_cardio': [
        'LISS（低强度稳态有氧）原理: 保持心率在脂肪供能区间 (120-135 bpm), 持续 35-45 分钟。',
        '推荐项目: 快走、慢跑机、椭圆机、骑车等, 选择能持续 30 分钟以上的低强度活动。',
        '⚠ 关键: 心率必须稳定在 120-135, 不要跑太快进入无氧区间, 否则燃脂效率反而下降。',
        '预期效果: 直接燃脂 + 提升心肺基础 + 不易疲劳, 适合每周 2-3 次作为减脂主轴。',
    ],
    'flow': [
        '这是一个训练流程组合, 由多个基础动作组成, 目的是综合刺激多个肌群或达到特定训练目标。',
        '执行要点: 按顺序完成每个动作, 组间休息根据动作复杂度调整 (30-90 秒)。',
        '训练前充分热身, 训练后拉伸放松, 避免运动损伤。',
    ],
}

# 按目标肌群关键词推断 emoji
def _emoji_for_target(target: str) -> str:
    """根据目标肌群中英文返回emoji"""
    if not target:
        return MUSCLE_EMOJI['默认']
    t = target
    # 按优先级匹配
    for key, emoji in MUSCLE_EMOJI.items():
        if key in t:
            return emoji
    return MUSCLE_EMOJI['默认']


# 体测指标完整列(扩展12项)
BODY_COLUMNS = [
    '日期', '体重(kg)', '体脂率(%)', '肌肉量(kg)', '内脏脂肪等级',
    '基础代谢率(kcal)', '体水分率(%)', '骨量(kg)', 'BMI',
    '骨骼肌率(%)', '腰围(cm)', '臀围(cm)'
]

# 训练计划结构(v2.0宽背窄腰版, 22周塑形冲刺, 三阶段周期化, 6练1休)
# ★v2.0: 背/胸各一周2次(宽背+清晰胸肌), 固定6练1休(周日休息+真空腹日)
TRAINING_SCHEDULE = [
    {'day': '周一', 'title': '背（宽）', 'focus': '引体+高位下拉+单臂划船, 背阔宽度核心', 'icon': '🔙'},
    {'day': '周二', 'title': '胸（上胸优先）', 'focus': '上斜卧推+平板卧推, 上胸饱满+整体厚度', 'icon': '💪'},
    {'day': '周三', 'title': '腿（四头为主）', 'focus': '深蹲+前蹲+罗马尼亚硬拉, 大重量复合', 'icon': '🦵'},
    {'day': '周四', 'title': '背（厚度）+ 二头', 'focus': '俯身杠铃划船+T杆+坐姿划船, 上背厚度', 'icon': '🏋️'},
    {'day': '周五', 'title': '肩 + 腹', 'focus': '推举+侧平举+抗旋转, 中束宽度+肩腰比', 'icon': '🙆'},
    {'day': '周六', 'title': '胸+腿泵感（HIIT）', 'focus': '高次泵感+代谢冲刺, 线条雕刻', 'icon': '🔥'},
    {'day': '周日', 'title': '完全休息 + 真空腹', 'focus': '真空腹 3×30s, 窄腰核心', 'icon': '😴'},
]

# 三阶段映射 (v2.1: 22周 宽背窄腰 执行版)
PHASE_INFO = {
    1: {'name': '代谢重建',  'weeks': 'W1-W6',   'desc': '高容量背训练+动作固化, 建立代谢压力适应, 热身组强制执行'},
    2: {'name': '体成分重组','weeks': 'W7-W14',  'desc': '容量递进+1-2组/周(上限16组), 真空腹每日化(3×40s), 有氧递进HIIT 15→20+LISS 35→40min'},
    3: {'name': '线条雕刻',  'weeks': 'W15-W22', 'desc': '碳水循环(高碳日背/腿 300g→中碳日胸/肩 200g→低碳日休息 130g), 泵感日+峰值减量'},
}


# ═══════════════════════════════════════════════════════════
# 数据模型层
# ═══════════════════════════════════════════════════════════

class BodyDataModel:
    """体测数据模型 — 管理体重体脂等12项指标"""

    def __init__(self):
        self.df = self._load()
        self.target_weight = 65.0  # 目标体重(kg) [v2.0宽背窄腰: 12月底64.5-65.5]
        self.target_bodyfat = 13.0

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
    """动作库 — 加载JSON + GIF路径管理 + 预检缓存"""

    def __init__(self):
        self.exercises: List[Dict] = []
        self._gif_cache: Dict[str, Optional[str]] = {}  # media_id -> path or None
        self._gif_valid: Dict[str, bool] = {}  # media_id -> 是否有效
        self._gif_first_frame: Dict[str, bytes] = {}  # media_id -> QPixmap data
        self._load()
        self._precheck_gifs()

    def _load(self):
        if os.path.exists(EXERCISES_JSON):
            with open(EXERCISES_JSON, 'r', encoding='utf-8') as f:
                self.exercises = json.load(f)

    def _precheck_gifs(self):
        """预检所有GIF文件有效性 — 批量验证避免后续逐个检查"""
        for ex in self.exercises:
            mid = ex.get('media_id', '')
            if not mid:
                continue
            p = os.path.join(GIF_DIR, f'{mid}.gif')
            valid = False
            if os.path.exists(p) and os.path.getsize(p) > 0:
                # 仅当 QApplication 已初始化时才用 QMovie 深度校验
                from PySide6.QtWidgets import QApplication
                if QApplication.instance() is not None:
                    try:
                        from PySide6.QtGui import QMovie
                        movie = QMovie(p)
                        valid = movie.isValid() and movie.frameCount() >= 1
                        movie.setPaused(True)
                    except Exception:
                        valid = False
                else:
                    # 无 QApplication 时仅做文件存在检查
                    valid = True
            self._gif_cache[mid] = p if valid else None
            self._gif_valid[mid] = valid

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
                if kw in (e.get('name_cn') or '').lower() or
                kw in (e.get('name_en') or '').lower() or
                kw in (e.get('target') or '').lower() or
                kw in (e.get('category') or '').lower()]

    def gif_path(self, media_id: str) -> Optional[str]:
        """获取GIF路径 — 使用预检缓存快速返回"""
        if not media_id:
            return None
        if media_id in self._gif_cache:
            return self._gif_cache[media_id]
        # 回退: 直接检查文件
        p = os.path.join(GIF_DIR, f'{media_id}.gif')
        valid = os.path.exists(p) and os.path.getsize(p) > 0
        self._gif_cache[media_id] = p if valid else None
        self._gif_valid[media_id] = valid
        return p if valid else None

    def has_gif(self, media_id: str) -> bool:
        """快速判断是否有可用GIF"""
        if not media_id:
            return False
        if media_id in self._gif_valid:
            return self._gif_valid[media_id]
        return self.gif_path(media_id) is not None

    def get_first_frame(self, media_id: str) -> Optional[QPixmap]:
        """获取GIF首帧QPixmap — 用于缩略图, 缓存避免重复IO (使用QImageReader)"""
        if not media_id:
            return None
        if media_id in self._gif_first_frame:
            data = self._gif_first_frame[media_id]
            pm = QPixmap()
            pm.loadFromData(data)
            if not pm.isNull():
                return pm
            # 缓存损坏, 清除并重读
            del self._gif_first_frame[media_id]
        gif_path = self.gif_path(media_id)
        if gif_path is None:
            return None
        try:
            from PySide6.QtGui import QImageReader
            from PySide6.QtCore import QByteArray, QBuffer, QIODevice
            reader = QImageReader(gif_path)
            reader.setAutoTransform(True)
            img = reader.read()  # 读取首帧
            if img.isNull():
                return None
            pm = QPixmap.fromImage(img)
            if pm and not pm.isNull():
                # 缓存为 PNG 字节串供后续复用
                qba = QByteArray()
                buf = QBuffer(qba)
                buf.open(QIODevice.WriteOnly)
                pm.save(buf, 'PNG')
                buf.close()
                self._gif_first_frame[media_id] = bytes(qba)
            return pm
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════
# 训练计划解析
# ═══════════════════════════════════════════════════════════

class TrainingPlanParser:
    """从12月底塑形冲刺计划.md解析训练动作, 支持20周三阶段周期化"""

    DAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    def __init__(self):
        self.raw_text = ''
        self._phase_exercises = {}  # {phase_num: {day: [exercises]}}
        self._phase_notes = {}      # {phase_num: ['note1', ...]}
        self._load()
        self._parse_all()

    def _load(self):
        if os.path.exists(PLAN_MD):
            with open(PLAN_MD, 'r', encoding='utf-8') as f:
                self.raw_text = f.read()

    @classmethod
    def get_phase(cls, week: int) -> int:
        return 1 if week <= 6 else (2 if week <= 14 else 3)

    def get_daily_exercises(self, week: int = 1) -> Dict[str, List[Dict]]:
        phase = self.get_phase(week)
        if phase in self._phase_exercises and self._phase_exercises[phase]:
            return self._phase_exercises[phase]
        # Phase 2/3 复用 Phase 1 动作(仅有调整说明, 无独立表格)
        result = self._phase_exercises.get(1, {})
        if not result:
            return {d['day']: [] for d in TRAINING_SCHEDULE}
        return result

    def get_phase_notes(self, week: int = 1) -> List[str]:
        phase = self.get_phase(week)
        return self._phase_notes.get(phase, [])

    # ──────────────── 解析引擎 ────────────────

    def _parse_all(self):
        """v2.1 格式: ## 五、Phase 1 训练明细 — ### 周X 日标题 + 3列表格(动作|组×次|要点)"""
        if not self.raw_text:
            return

        lines = self.raw_text.split('\n')
        in_section = 0      # 0=跳过, 5=Chapter5训练, 6=Chapter6概要
        current_day = None
        parsed = {}
        table_header = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # ── 章节边界 ──
            if stripped.startswith('## 五、'):
                in_section = 5; continue
            if in_section == 5 and stripped.startswith('## 六、'):
                # 保存 Phase 1
                if parsed:
                    self._phase_exercises[1] = dict(parsed)
                in_section = 6; continue
            if in_section == 6 and stripped.startswith('## 七、'):
                break
            if in_section == 0:
                continue

            # ── Chapter 6: Phase 2/3 概要收集 (v2.1: 粗体格式 **Phase N**) ──
            if in_section == 6:
                if stripped.startswith('**Phase 2') or stripped.startswith('### Phase 2'):
                    self._collect_phase_notes(2, lines, i)
                elif stripped.startswith('**Phase 3') or stripped.startswith('### Phase 3'):
                    self._collect_phase_notes(3, lines, i)
                continue

            # ── Chapter 5: 日期检测 (### 周一 · ... ) ──
            day_found = False
            for dn in self.DAY_NAMES:
                if stripped.startswith(f'### {dn}') and ('·' in stripped or '★' in stripped or '—' in stripped):
                    current_day = dn
                    table_header = []
                    day_found = True
                    break
            if day_found:
                continue
            # 非日期的 ### 行重置
            if stripped.startswith('###'):
                current_day = None
                table_header = []
                continue

            if current_day is None or current_day == '周日':
                continue

            # ── 表格行解析 (3列: 动作 | 组×次 | 要点) ──
            if not stripped.startswith('|') or '---' in stripped:
                if not stripped.startswith('|') and table_header:
                    table_header = []
                continue

            cells = [c.strip() for c in line.split('|')[1:-1]]
            if not cells:
                continue

            first_cell = cells[0]

            # 表头行: v2.1 第一列是 "动作"
            if first_cell == '动作':
                table_header = cells
                continue
            if not table_header:
                continue

            # ── 分格式解析 ──
            parsed.setdefault(current_day, [])

            if first_cell == '收尾':
                ex_name = cells[1] if len(cells) > 1 else ''
                ex_tip = cells[2] if len(cells) > 2 else ''
                if '真空腹' in ex_name:
                    if '+' in ex_name:
                        # 拆分: 非真空腹动作 + 真空腹流程块
                        non_vac = [p.strip().replace('**', '') for p in ex_name.split('+')
                                   if p.strip() and '真空腹' not in p]
                        if non_vac:
                            parsed[current_day].append({
                                'name': non_vac[0], 'sets': '',
                                'target': '收尾', 'tip': ex_tip, 'media_id': '',
                            })
                        vac_sets = ' '.join(p.strip() for p in ex_name.split('+') if '真空腹' in p)
                        parsed[current_day].append({
                            'name': vac_sets if vac_sets else '真空腹', 'sets': '',
                            'target': '窄腰', 'tip': '',
                            'media_id': '',
                            'is_workout_block': True, 'block_type': 'flow',
                            'duration': '', 'sub_info': '腹横肌收缩训练, 缩小腰围最有效的非有氧手段',
                        })
                    else:
                        parsed[current_day].append({
                            'name': ex_name, 'sets': '',
                            'target': '窄腰', 'tip': ex_tip, 'media_id': '',
                            'is_workout_block': True, 'block_type': 'flow',
                            'duration': '', 'sub_info': '腹横肌收缩训练, 缩小腰围最有效的非有氧手段',
                        })
                else:
                    parsed[current_day].append({
                        'name': ex_name, 'sets': cells[1] if len(cells) > 1 else '',
                        'target': '收尾', 'tip': ex_tip, 'media_id': '',
                    })
            elif first_cell == '热身':
                parsed[current_day].append({
                    'name': cells[1] if len(cells) > 1 else '动态热身',
                    'sets': '热身', 'target': '',
                    'tip': cells[2] if len(cells) > 2 else '', 'media_id': '',
                    'is_workout_block': True, 'block_type': 'flow',
                    'duration': '5-8分钟', 'sub_info': '关节绕环+空杆激活',
                })
            elif first_cell.startswith('循环'):
                parsed[current_day].append({
                    'name': cells[1] if len(cells) > 1 else 'HIIT循环',
                    'sets': '4循环', 'target': 'HIIT',
                    'tip': cells[2] if len(cells) > 2 else '', 'media_id': '',
                    'is_workout_block': True, 'block_type': 'hiit_loop',
                    'duration': cells[2] if len(cells) > 2 else '约15分钟',
                    'sub_info': '6动作 x 40秒训练 / 20秒休息',
                })
            elif first_cell == '拉伸':
                parsed[current_day].append({
                    'name': '全身拉伸', 'sets': cells[1] if len(cells) > 1 else '10分钟',
                    'target': '拉伸', 'tip': cells[2] if len(cells) > 2 else '', 'media_id': '',
                    'is_workout_block': True, 'block_type': 'flow',
                    'duration': cells[1] if len(cells) > 1 else '10分钟',
                    'sub_info': '静态拉伸·肌筋膜放松',
                })
            elif first_cell == '快走/椭圆机':
                parsed[current_day].append({
                    'name': '快走/椭圆机 (LISS)', 'sets': cells[1] if len(cells) > 1 else '',
                    'target': 'LISS有氧 心率120-135', 'tip': cells[2] if len(cells) > 2 else '',
                    'media_id': '',
                    'is_workout_block': True, 'block_type': 'liss_cardio',
                    'duration': cells[1] if len(cells) > 1 else '35分钟',
                    'sub_info': '心率120-135 bpm · 燃脂神经恢复',
                })
            else:
                # 普通动作行: | 动作名 | 组×次 | 要点 |
                ex_name = first_cell
                if '真空腹' in ex_name:
                    parsed[current_day].append({
                        'name': ex_name,
                        'sets': cells[1] if len(cells) > 1 else '',
                        'target': '窄腰',
                        'tip': cells[2] if len(cells) > 2 else '',
                        'media_id': '',
                        'is_workout_block': True, 'block_type': 'flow',
                        'duration': cells[1] if len(cells) > 1 else '',
                        'sub_info': '腹横肌收缩训练, 缩小腰围最有效的非有氧手段',
                    })
                else:
                    parsed[current_day].append({
                        'name': ex_name,
                        'sets': cells[1] if len(cells) > 1 else '',
                        'target': '',
                        'tip': cells[2] if len(cells) > 2 else '',
                        'media_id': '',
                    })

        # 如果没有通过 Chapter 5→6 边界保存, 兜底保存 Phase 1
        if parsed and 1 not in self._phase_exercises:
            self._phase_exercises[1] = dict(parsed)

    @staticmethod
    def _detect_phase(stripped: str) -> int:
        # v2.1: Phase 1 明细直接在 ## 五、 下, 无需 ### 子标题检测, 此方法保留兼容
        if stripped.startswith('### 3.1'):
            return 1
        if stripped.startswith('### 3.2'):
            return 2
        if stripped.startswith('### 3.3'):
            return 3
        return 0

    def _collect_phase_notes(self, phase: int, lines: List[str], start_idx: int):
        """从 Phase 2/3 概要(## 六、)标题后收集调整说明, 直到下一个 Phase 标题 或 ## 章节"""
        notes = []
        for j in range(start_idx + 1, len(lines)):
            s = lines[j].strip()
            if not s:
                continue
            # 停止条件: 下一个 Phase 粗体/标题 或 ## 章节
            if s.startswith('**Phase') or s.startswith('### Phase') or s.startswith('## '):
                break
            if s.startswith('- ') or s.startswith('**') or \
               any(s.startswith(f'{n}. **') for n in range(1, 10)):
                notes.append(s)
        if notes:
            self._phase_notes[phase] = notes


# ═══════════════════════════════════════════════════════════
# 营养方案 — 解析12月底塑形冲刺计划第二章
# ═══════════════════════════════════════════════════════════

class NutritionParser:
    """从计划文档提取三阶段营养方案 + 补剂 + 饮水"""

    # 三阶段热量与宏量数据(v2.1宽背窄腰执行版, 热量提升+碳水循环优化)
    PHASE_MACROS = {
        1: {  # 代谢重建期 (v2.1: 2300/2100, 缺口~200-300kcal)
            'training':   {'kcal': 2300, 'protein': 170, 'carbs': 260, 'fat': 60, 'protein_pct': 30},
            'rest':       {'kcal': 2100, 'protein': 165, 'carbs': 210, 'fat': 60, 'protein_pct': 31},
        },
        2: {  # 体成分重组期 (v2.1: 2200/2000, 缺口~200-300kcal)
            'training':   {'kcal': 2200, 'protein': 170, 'carbs': 240, 'fat': 55, 'protein_pct': 31},
            'rest':       {'kcal': 2000, 'protein': 165, 'carbs': 190, 'fat': 55, 'protein_pct': 33},
        },
        3: {  # 线条雕刻期 (碳水循环: 高碳日背/腿350g, 中碳日胸/肩240g, 低碳日泵感+休息150g)
            'training':   {'kcal': 2200, 'protein': 170, 'carbs': 240, 'fat': 55, 'protein_pct': 31},  # 中碳日 fallback
            'high_carb':  {'kcal': 2500, 'protein': 170, 'carbs': 350, 'fat': 60, 'protein_pct': 27},
            'medium':     {'kcal': 2200, 'protein': 170, 'carbs': 240, 'fat': 55, 'protein_pct': 31},
            'low_carb':   {'kcal': 1900, 'protein': 165, 'carbs': 150, 'fat': 50, 'protein_pct': 35},
            'rest':       {'kcal': 1900, 'protein': 165, 'carbs': 150, 'fat': 50, 'protein_pct': 35},
        },
    }

    # 每日五餐 (v2.0 Phase 1 训练日基准 2050kcal, 蛋白目标165g)
    DAILY_MEALS = [
        {'name': '早餐 (07:00)', 'kcal': 450, 'protein': 38, 'carbs': 43, 'fat': 22,
         'items': [
             ('全蛋', '3个', '18g蛋白, 15g脂肪'),
             ('蛋白', '3个', '10g蛋白'),
             ('燕麦片(干)', '40g', '24g碳水, 5g蛋白'),
             ('蓝莓', '80g', '10g碳水'),
             ('全脂牛奶', '150ml', '8g碳水, 5g蛋白'),
         ]},
        {'name': '加餐 (10:00)', 'kcal': 280, 'protein': 28, 'carbs': 25, 'fat': 7,
         'items': [
             ('鸡胸肉', '100g', '24g蛋白'),
             ('红薯', '120g', '24g碳水, 2g蛋白'),
             ('核桃', '10g', '6g脂肪, 2g蛋白'),
         ]},
        {'name': '午餐 (12:30)', 'kcal': 520, 'protein': 40, 'carbs': 48, 'fat': 14,
         'items': [
             ('糙米饭(熟)', '120g', '40g碳水, 4g蛋白'),
             ('牛肉(瘦)', '120g', '30g蛋白, 6g脂肪'),
             ('西兰花', '200g', '8g碳水, 6g蛋白'),
             ('橄榄油', '6g', '6g脂肪'),
         ]},
        {'name': '训练前加餐 (16:30)', 'kcal': 250, 'protein': 12, 'carbs': 33, 'fat': 4,
         'items': [
             ('全麦面包', '2片', '30g碳水, 6g蛋白'),
             ('无糖豆浆', '200ml', '3g碳水, 6g蛋白'),
         ]},
        {'name': '训练后 (19:00)', 'kcal': 310, 'protein': 27, 'carbs': 29, 'fat': 1,
         'items': [
             ('酵母蛋白粉', '35g', '25g蛋白, 4g碳水'),
             ('香蕉', '1根', '25g碳水, 1g蛋白'),
             ('亮氨酸粉', '2-3g', '补偿酵母蛋白亮氨酸'),
         ]},
        {'name': '晚餐 (20:30)', 'kcal': 290, 'protein': 25, 'carbs': 8, 'fat': 9,
         'items': [
             ('三文鱼/鸡胸', '100g', '22g蛋白, 6g脂肪'),
             ('混合蔬菜', '200g', '8g碳水, 3g蛋白'),
             ('橄榄油', '3g', '3g脂肪'),
         ]},
    ]

    # 补剂方案 (v2.0宽背窄腰版, 新增乳清/CLA/电解质, 维D3提升)
    SUPPLEMENTS = [
        {'name': '酵母蛋白粉',   'dose': '35g',       'timing': '训练后30分钟内',     'purpose': '蛋白质补充',         'note': '维持'},
        {'name': '乳清蛋白粉',   'dose': '30g',       'timing': '训练前30分钟',       'purpose': '弥补酵母蛋白亮氨酸不足', 'note': '★新增,训练前补充'},
        {'name': '肌酸单水合物', 'dose': '5g/天',     'timing': '训练后随蛋白粉',     'purpose': '力量+肌肉饱满度',    'note': '维持'},
        {'name': '亮氨酸粉',     'dose': '3-4g',      'timing': '训练后(混蛋白粉)',   'purpose': 'MPS最大化',          'note': '★v2.0从2-3g提升'},
        {'name': '鱼油',         'dose': '3g',        'timing': '随餐',               'purpose': '抗炎+减脂辅助',      'note': '维持'},
        {'name': 'CLA共轭亚油酸', 'dose': '3g',       'timing': '随餐',               'purpose': '减少腹部顽固脂肪',   'note': '★新增,窄腰针对性'},
        {'name': '维生素D3',     'dose': '4000IU',    'timing': '早餐',               'purpose': '睾酮支持+免疫',      'note': '★v2.0提升到4000IU(冬季阳光少)'},
        {'name': '锌镁',         'dose': '30mg+450mg','timing': '睡前1h',             'purpose': '睡眠+恢复',          'note': '维持'},
        {'name': '电解质',       'dose': '含钾钠镁',   'timing': '高碳日训练中',       'purpose': '防抽筋+维持水合',    'note': '★新增,高碳日专用'},
    ]

    # 饮水与控盐 (v2.0窄腰版: 饮水提升, 盐摄入降低)
    HYDRATION = [
        ('总饮水量',     '4.0-4.5L/天', 'v2.0提升0.5L帮助代谢'),
        ('晨起',          '500ml温水+柠檬', '代谢唤醒'),
        ('训练中',        '800-1000ml', '每15分钟200ml'),
        ('肌酸补水',      '额外+500ml/天', '肌酸需充足水合'),
        ('盐摄入',        '<4g/天',     '★v2.0从4-5g降至<4g,控皮下水分'),
        ('周日控盐日',    '<3g/天',     '★窄腰日严格控盐'),
        ('睡前2h',        '限水',         '避免夜起'),
        ('加工食品',      '完全避免',     '★香肠腊肉酱料一律不碰'),
    ]

    # Phase 3 高碳日说明 (v2.1: 高碳日350g碳水专为大肌群背/腿日)
    HIGH_CARB_INFO = (
        '高碳日安排(碳水350g): 周四背日 + 周三腿日\n'
        '调整: 早餐燕麦→60g / 训练前+香蕉1根+燕麦20g / '
        '训练中+含30g麦芽糊精运动饮料 / 训练后+葡萄糖粉15g+额外香蕉 / 晚餐+红薯100g\n'
        '中碳日(碳水240g): 周一背日 + 周二上胸日 + 周五肩日 · 低碳日(碳水150g): 周六胸腿泵感 + 周日休息'
    )

    @classmethod
    def get_phase(cls, week: int) -> int:
        return 1 if week <= 6 else (2 if week <= 14 else 3)

    @classmethod
    def get_macros(cls, week: int, day_type: str = 'training') -> Dict:
        """day_type: 'training' | 'rest' | 'high_carb'"""
        phase = cls.get_phase(week)
        data = cls.PHASE_MACROS.get(phase, {}).get(day_type)
        if data is None:
            data = cls.PHASE_MACROS[phase]['training']
        return dict(data)

    @classmethod
    def get_meals(cls) -> List[Dict]:
        return list(cls.DAILY_MEALS)

    @classmethod
    def get_supplements(cls) -> List[Dict]:
        return list(cls.SUPPLEMENTS)

    @classmethod
    def get_hydration(cls) -> List[Tuple]:
        return list(cls.HYDRATION)

    @classmethod
    def get_daily_totals(cls, meals: List[Dict] = None) -> Dict:
        """汇总五餐合计(Phase 1 训练日基准: 169p/186c/57f/2100kcal)"""
        if meals is None:
            meals = cls.DAILY_MEALS
        return {
            'protein': sum(m['protein'] for m in meals),
            'carbs': sum(m['carbs'] for m in meals),
            'fat': sum(m['fat'] for m in meals),
            'kcal': sum(m['kcal'] for m in meals),
        }


# ═══════════════════════════════════════════════════════════
# UI组件 — 动作详情弹窗
# ═══════════════════════════════════════════════════════════

class ExerciseDetailDialog(QDialog):
    """动作详情弹窗 — QMovie播GIF + 循环控制 + 速度选择 + 自适应缩放"""

    def __init__(self, exercise: Dict, exercise_lib: ExerciseLibrary, parent=None):
        super().__init__(parent)
        self.exercise = exercise
        self.lib = exercise_lib
        self.movie = None
        self._speed = 100  # 百分比, 100=原速
        self._build_ui()

    def _build_ui(self):
        name = self.exercise.get('name_cn', '未知动作')
        self.setWindowTitle(f'动作示范 — {name}')
        self.setMinimumSize(780, 620)
        self.setStyleSheet(f"background-color: {COLORS['bg']}; color: {COLORS['text']};")

        layout = QVBoxLayout(self)

        # 标题
        title = QLabel(f'  {name}')
        title.setFont(QFont('Microsoft YaHei', 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']}; padding: 8px 10px;")
        layout.addWidget(title)

        # 英文名 + 器材
        en_name = self.exercise.get('name_en', '')
        equip = self.exercise.get('equipment', '')
        target = self.exercise.get('target', '')
        info_parts = [f'English: {en_name}'] if en_name else []
        if equip:
            info_parts.append(f'器材: {equip}')
        if target:
            info_parts.append(f'目标: {target}')
        info = QLabel('    |    '.join(info_parts))
        info.setStyleSheet(f"color: {COLORS['subtext']}; padding: 0 10px; font-size: 11px;")
        layout.addWidget(info)

        # 主体: 左GIF + 右信息
        body = QHBoxLayout()
        body.setSpacing(12)

        # 左侧GIF区域
        gif_frame = QFrame()
        gif_frame.setStyleSheet(
            f"background-color: {COLORS['card']}; border-radius: 10px; "
            f"border: 1px solid {COLORS['border']};"
        )
        gif_frame.setMinimumSize(340, 340)
        gif_layout = QVBoxLayout(gif_frame)
        gif_layout.setContentsMargins(8, 8, 8, 8)

        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMinimumSize(320, 280)
        self.gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.gif_label.setStyleSheet(
            f"background-color: transparent; color: {COLORS['subtext']}; font-size: 13px;"
        )
        gif_layout.addWidget(self.gif_label)

        # 帧信息标签
        self.frame_info = QLabel('')
        self.frame_info.setAlignment(Qt.AlignCenter)
        self.frame_info.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        gif_layout.addWidget(self.frame_info)

        body.addWidget(gif_frame, stretch=4)

        # 右侧信息面板
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {COLORS['card']}; border-radius: 10px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(6)

        # 肌群信息
        muscle = self.exercise.get('muscle_group', '')
        secondary = self.exercise.get('secondary_muscles', [])
        sec_str = ', '.join(secondary) if isinstance(secondary, list) else str(secondary)

        musc_title = QLabel('肌群信息')
        musc_title.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        musc_title.setStyleSheet(f"color: {COLORS['primary']};")
        info_layout.addWidget(musc_title)

        for label, value, color in [
            ('主肌群', muscle, COLORS['success']),
            ('协同肌群', sec_str, COLORS['warning']),
        ]:
            if value:
                row = QLabel(f'{label}: {value}')
                row.setFont(QFont('Microsoft YaHei', 10))
                row.setStyleSheet(f"color: {color}; padding: 2px 4px;")
                row.setWordWrap(True)
                info_layout.addWidget(row)

        # 分隔
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"color: {COLORS['border']}; margin: 4px 0;")
        info_layout.addWidget(sep1)

        # 步骤标题
        steps_title = QLabel('动作步骤')
        steps_title.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        steps_title.setStyleSheet(f"color: {COLORS['purple']};")
        info_layout.addWidget(steps_title)

        # 步骤列表
        steps = self.exercise.get('instruction_steps_zh', [])
        if not steps:
            instructions = self.exercise.get('instructions_zh', '')
            if instructions:
                steps = [s.strip() for s in instructions.replace('\n', '。').split('。') if s.strip()]

        step_scroll = QScrollArea()
        step_scroll.setWidgetResizable(True)
        step_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: transparent; }}"
        )
        step_widget = QWidget()
        step_layout = QVBoxLayout(step_widget)
        step_layout.setSpacing(4)
        step_layout.setContentsMargins(0, 0, 0, 0)
        for i, step in enumerate(steps, 1):
            sl = QLabel(f'{i}. {step}')
            sl.setWordWrap(True)
            sl.setStyleSheet(f"color: {COLORS['text']}; padding: 2px 4px; font-size: 10px;")
            step_layout.addWidget(sl)
        step_layout.addStretch()
        step_scroll.setWidget(step_widget)
        info_layout.addWidget(step_scroll, stretch=1)

        body.addWidget(info_frame, stretch=3)
        layout.addLayout(body, stretch=1)

        # 底部控制栏
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)

        # 播放/暂停
        self.btn_play = QPushButton('暂停')
        self.btn_play.setFixedHeight(28)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_play.setStyleSheet(self._ctrl_btn_style(COLORS['primary']))
        ctrl.addWidget(self.btn_play)

        # 重新播放
        btn_restart = QPushButton('重播')
        btn_restart.setFixedHeight(28)
        btn_restart.clicked.connect(self._restart)
        btn_restart.setStyleSheet(self._ctrl_btn_style(COLORS['success']))
        ctrl.addWidget(btn_restart)

        ctrl.addSpacing(16)

        # 速度控制标签
        speed_label = QLabel('速度:')
        speed_label.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 10px;")
        ctrl.addWidget(speed_label)

        for pct, lbl in [(50, '0.5x'), (75, '0.75x'), (100, '1x'), (150, '1.5x'), (200, '2x')]:
            btn = QPushButton(lbl)
            btn.setFixedHeight(26)
            btn.setFixedWidth(42)
            active = (pct == 100)
            btn.setCheckable(True)
            btn.setChecked(active)
            btn.clicked.connect(lambda checked, s=pct: self._set_speed(s))
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {'#2ea043' if active else COLORS['card']}; "
                f"color: {'#fff' if active else COLORS['text']}; border: 1px solid {COLORS['border']}; "
                f"border-radius: 3px; padding: 2px 4px; font-size: 9px; }}"
                f"QPushButton:checked {{ background-color: #2ea043; color: #fff; }}"
                f"QPushButton:hover {{ border: 1px solid {COLORS['primary']}; }}"
            )
            btn.setProperty('speed_btn', True)
            ctrl.addWidget(btn)

        ctrl.addStretch()

        # 帧计数
        self.lbl_frame_count = QLabel('')
        self.lbl_frame_count.setStyleSheet(f"color: {COLORS['subtext']}; font-size: 9px;")
        ctrl.addWidget(self.lbl_frame_count)

        layout.addLayout(ctrl)

        self._load_gif()

    @staticmethod
    def _ctrl_btn_style(color: str) -> str:
        return (
            f"QPushButton {{ background-color: {COLORS['card']}; color: {COLORS['text']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 4px; "
            f"padding: 4px 12px; font-size: 11px; }}"
            f"QPushButton:hover {{ border: 1px solid {color}; }}"
        )

    def _load_gif(self):
        """加载GIF动画 — 带错误恢复和帧缓存"""
        media_id = self.exercise.get('media_id', '')
        gif_path = self.lib.gif_path(media_id)
        if gif_path is None:
            self.gif_label.setText(
                '无动作示范GIF\n\n(该动作未匹配到示范数据)'
            )
            self.gif_label.setStyleSheet(
                f"background-color: {COLORS['card']}; color: {COLORS['subtext']}; "
                f"font-size: 13px; border-radius: 8px; padding: 20px;"
            )
            self.btn_play.setEnabled(False)
            self.lbl_frame_count.setText('')
            return

        from PySide6.QtGui import QMovie
        try:
            self.movie = QMovie(gif_path)
            if not self.movie.isValid():
                raise ValueError('无效GIF文件')

            # 缓存所有帧以提高播放流畅度
            self.movie.setCacheMode(QMovie.CacheAll)
            # 自适应缩放到label大小
            gif_size = self.movie.currentImage().size()
            display_size = min(340, max(280, gif_size.width()))
            self.movie.setScaledSize(QSize(display_size, display_size))

            self.movie.frameChanged.connect(self._on_frame_changed)
            self.movie.finished.connect(self._on_loop_complete)
            self.movie.stateChanged.connect(self._on_state_changed)

            self.gif_label.setMovie(self.movie)
            self.movie.start()

            total = self.movie.frameCount()
            self.lbl_frame_count.setText(f'共 {total} 帧')
            self.frame_info.setText(
                f'分辨率: {gif_size.width()}x{gif_size.height()}'
            )

        except Exception as e:
            self.gif_label.setText(
                f'GIF加载失败\n\n(文件可能已损坏)\n\n{str(e)[:80]}'
            )
            self.gif_label.setStyleSheet(
                f"background-color: {COLORS['card']}; color: {COLORS['danger']}; "
                f"font-size: 11px; border-radius: 8px; padding: 20px;"
            )
            self.btn_play.setEnabled(False)
            self.lbl_frame_count.setText('')
            if self.movie:
                self.movie = None

    def _on_frame_changed(self, frame: int):
        if self.movie:
            total = self.movie.frameCount()
            if total > 0:
                self.frame_info.setText(f'帧: {frame + 1}/{total}')

    def _on_loop_complete(self):
        """循环结束自动重播"""
        if self.movie:
            self.movie.start()

    def _on_state_changed(self, state):
        from PySide6.QtGui import QMovie
        if state == QMovie.Running:
            self.btn_play.setText('暂停')
        elif state == QMovie.NotRunning:
            self.btn_play.setText('播放')

    def _toggle_play(self):
        if self.movie is None:
            return
        from PySide6.QtGui import QMovie
        if self.movie.state() == QMovie.Running:
            self.movie.setPaused(True)
            self.btn_play.setText('播放')
        else:
            self.movie.setPaused(False)
            self.btn_play.setText('暂停')

    def _restart(self):
        if self.movie is None:
            return
        self.movie.stop()
        self.movie.start()

    def _set_speed(self, pct: int):
        """设置播放速度"""
        if self.movie is None:
            return
        self._speed = pct
        self.movie.setSpeed(pct)
        # 更新所有速度按钮状态
        for child in self.findChildren(QPushButton):
            if child.property('speed_btn'):
                child.setChecked(child.text() in [
                    '0.5x', '0.75x', '1x', '1.5x', '2x'
                ] and False)  # reset
        self.frame_info.setText(
            f'速度: {pct / 100:.2f}x' if pct != 100 else (
                f'{self.movie.currentFrameNumber() + 1}/{self.movie.frameCount()}'
            )
        )

    def closeEvent(self, event):
        """关闭窗口时清理QMovie资源"""
        if self.movie:
            self.movie.stop()
            self.gif_label.clear()
            self.movie.deleteLater()
            self.movie = None
        super().closeEvent(event)


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

        # GIF缩略图 — 使用 QMovie 首帧提取 (无需 PIL)
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
            scaled = pixmap.scaled(
                178, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            thumb.setPixmap(scaled)
        else:
            thumb.setText('')
            thumb.setStyleSheet(
                f"background-color: {COLORS['bg']}; color: {COLORS['subtext']}; "
                f"font-size: 36px; border-radius: 4px; border: 1px solid {COLORS['border']};"
            )
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
    """训练计划 — 20周塑形冲刺, 周历视图 + 阶段切换 + 每日动作列表"""

    def __init__(self, plan: TrainingPlanParser, lib: ExerciseLibrary):
        super().__init__()
        self.plan = plan
        self.lib = lib
        self.current_week = 1
        self.daily_exercises = plan.get_daily_exercises(self.current_week)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        layout = QVBoxLayout(self)

        # 顶部
        top = QHBoxLayout()
        title = QLabel('📅 22周塑形冲刺 — 宽背窄腰 · 三阶段周期化')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        # 周次选择 (22周)
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
        self.container_days.setMinimumWidth(900)  # 3列x280+间距, 防止卡片被压扁
        self.grid_days = QGridLayout(self.container_days)
        self.grid_days.setSpacing(10)
        # 三列等宽stretch, 避免列被压扁
        self.grid_days.setColumnStretch(0, 1)
        self.grid_days.setColumnStretch(1, 1)
        self.grid_days.setColumnStretch(2, 1)
        scroll.setWidget(self.container_days)
        layout.addWidget(scroll, stretch=1)

        self._refresh_days()

    def _on_week_changed(self, idx: int):
        self.current_week = idx + 1
        self.daily_exercises = self.plan.get_daily_exercises(self.current_week)
        self._refresh_days()

    def _refresh_days(self):
        # 清除旧卡片
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
        # v5.9.2: 识别 HIIT / LISS / REST 特殊日, 头部渐变 + GIF统计徽章
        title_lower = sched['title'].lower()
        is_hiit = 'hiit' in title_lower
        is_liss = 'liss' in title_lower
        is_rest = ('休息' in sched['title']) or ('rest' in title_lower)
        if is_hiit:
            head_bg = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['hiit_bg']}, stop:1 {COLORS['card']})"
            title_color = COLORS['hiit_fg']
            sub_text = '🔥 高强度间歇训练'
        elif is_liss:
            head_bg = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['liss_bg']}, stop:1 {COLORS['card']})"
            title_color = COLORS['liss_fg']
            sub_text = '🚶 低强度稳态有氧'
        elif is_rest:
            head_bg = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['card']}, stop:1 {COLORS['card']})"
            title_color = COLORS['rest_fg']
            sub_text = '💤 主动恢复日'
        else:
            head_bg = COLORS['card']
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

        # ===== v5.9.2 头部 (图标 + 标题 + 副标题 + 统计徽章) =====
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

        # 统计徽章: X/Y GIF
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

        # 头部底色通过父容器包裹的方式表达 — 这里用顶部frame作为视觉条
        # (实际效果靠标题色+渐变控制, 此处保留分隔)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        cl.addWidget(sep)

        if is_rest or not exercises:
            hint = QLabel('😴 完全休息日\n睡眠>8h | 泡脚 | 按摩\n当日蛋白目标155-160g')
            hint.setStyleSheet(f"color: {COLORS['success']}; padding: 8px;")
            hint.setWordWrap(True)
            cl.addWidget(hint)
        else:
            for ex in exercises:
                # v5.9.2: HIIT循环/LISS流程 渲染为流程块而非按钮
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
        """v5.9.2: HIIT循环 / LISS流程 / 复合动作 紧凑流程块(窄腰/真空腹可点击查看教程)"""
        block_type = ex.get('block_type', 'flow')  # 'hiit_loop' | 'liss_cardio' | 'flow'
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

        # v2.0: 流程块支持点击查看教程 (真空腹等专项训练的文字教程)
        block.setCursor(Qt.PointingHandCursor)
        # 透传点击事件给所有子控件
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

        # 标题
        title = QLabel(f'📋 {name}')
        title.setFont(QFont('Microsoft YaHei', 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        lay.addWidget(title)

        # 副标题
        sub_info = ex.get('sub_info', '')
        if sub_info:
            sub = QLabel(sub_info)
            sub.setStyleSheet(f"color: {COLORS['accent']}; font-size: 11px;")
            sub.setWordWrap(True)
            lay.addWidget(sub)

        # 分隔
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        lay.addWidget(sep)

        # 教程内容
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

        # 关闭按钮
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

        # 查找动作库: media_id 优先, 其次按名称模糊匹配
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

        # 使用QFrame作为可点击容器, 嵌入缩略图+文字+状态标识
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
            border_color = COLORS['success'] + '88'   # 半透明成功色

        container.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['bg']}; border-radius: 8px;
                      border: 1px solid {border_color}; }}
            QFrame:hover {{ background-color: {COLORS['card']};
                           border: 1px solid {COLORS['primary']}; }}
        """)

        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(8, 4, 8, 4)
        hbox.setSpacing(8)

        # 左: GIF缩略图 (52x40) - v5.9.2 缺图时显示肌肉群 emoji
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
            # v5.9.2: 显示肌肉群emoji占位 — 富点击反馈感
            emoji = _emoji_for_target(target or name)
            thumb.setText(emoji)
            bg_tint = COLORS['card']
            thumb.setStyleSheet(
                f"background-color: {bg_tint}; color: {COLORS['primary']}; "
                f"font-size: 18px; border-radius: 4px; "
                f"border: 1px dashed {COLORS['warning']}88;"
            )
        hbox.addWidget(thumb)

        # 中: 动作名称 + 组数 + 目标
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

        # 肌群/提示行
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

        # 右: 状态标识 (v5.9.2: 改为更鲜明的徽章)
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

        # 点击事件
        container.mousePressEvent = lambda e, data=ex_data: self._show_exercise(data)
        # 子控件也传递点击
        for child in container.findChildren(QWidget):
            child.mousePressEvent = lambda e, data=ex_data: self._show_exercise(data)

        return container

    def _fuzzy_match_exercise(self, name: str) -> Optional[Dict]:
        """按名称模糊匹配: 剥离括号/数字/特殊格式/超级组标记, 取第一个有效匹配"""
        if not name:
            return None
        import re
        # 步骤1: 完全删除括号及其内部内容
        core = re.sub(r'[（(][^）)]*[）)]', '', name)
        # 步骤2: 去除 ** 加粗标记 (来自markdown)和"超级组"/"循环"标记
        core = core.replace('**', '').replace('超级组', '').replace('循环', '')
        # 步骤3: 把 + 替换为空格
        core = core.replace('+', ' ')
        # 步骤4: 去除数字尾巴 ("2分钟"/"3秒"/"3×12"等)
        core = re.sub(r'\d+\s*[°]?\s*(分钟|分|秒|组|次|圈|轮|x|X|秒)?\s*$', '', core)
        # 步骤5: 压缩多余空格
        core = re.sub(r'\s+', ' ', core).strip()
        # 步骤6: 去掉残留的数字和乘号
        core = re.sub(r'[\d×x\s]+$', '', core).strip()

        # 优先级1: 用前 2-3 个关键词搜索
        words = core.split()
        for n_words in [3, 2, 1]:
            if len(words) >= n_words:
                kw = ' '.join(words[:n_words])
                results = self.lib.search(kw)
                for r in results:
                    if self.lib.has_gif(r.get('media_id', '')):
                        return r

        # 优先级2: 用完整核心名搜
        if core:
            results = self.lib.search(core)
            for r in results:
                if self.lib.has_gif(r.get('media_id', '')):
                    return r

        # 优先级3: 拆分 + 后的多个动作名, 分别尝试匹配
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
        self.current_day_type = 'training'  # 'training' | 'rest' | 'high_carb'
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg']};")
        outer = QVBoxLayout(self)

        # ── 顶部栏 ──
        top = QHBoxLayout()
        title = QLabel('🍽 饮食与补剂方案')
        title.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()

        # 周次 (22周)
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

        # 日类型切换 (v2.0 新增中碳日)
        self.btn_training = self._make_type_btn('🏋 训练日', 'training', True)
        self.btn_rest = self._make_type_btn('😴 休息日', 'rest', False)
        self.btn_medium = self._make_type_btn('🟡 中碳日', 'medium', False)
        self.btn_highcarb = self._make_type_btn('⚡ 高碳日', 'high_carb', False)
        top.addWidget(self.btn_training)
        top.addWidget(self.btn_rest)
        top.addWidget(self.btn_medium)
        top.addWidget(self.btn_highcarb)
        outer.addLayout(top)

        # ── 阶段信息 ──
        self.phase_label = QLabel()
        self.phase_label.setStyleSheet(f"color: {COLORS['success']}; padding: 2px 4px; font-size: 12px;")
        outer.addWidget(self.phase_label)

        # ── 滚动可容纳两个区域: 宏量 + 餐食 + 补剂饮水 ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        content = QWidget()
        content.setMinimumWidth(900)
        content_layout = QVBoxLayout(content)

        # ── 宏量营养概览卡片 ──
        self.macro_card = QFrame()
        self.macro_card.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['card']}; border-radius: 10px;
                      border: 1px solid {COLORS['border']}; }}
        """)
        self.macro_layout = QHBoxLayout(self.macro_card)
        self.macro_layout.setContentsMargins(20, 16, 20, 16)
        self.macro_layout.setSpacing(12)

        # 4个宏量数字卡片占位
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

        # ── 蛋白质占比标签 ──
        self.protein_pct_label = QLabel()
        self.protein_pct_label.setStyleSheet(f"color: {COLORS['subtext']}; padding: 4px 0; font-size: 11px;")
        content_layout.addWidget(self.protein_pct_label)

        # ── 五餐明细 (2行×3列) ──
        meals_title = QLabel('📋 每日五餐明细')
        meals_title.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        meals_title.setStyleSheet(f"color: {COLORS['primary']}; padding-top: 12px;")
        content_layout.addWidget(meals_title)

        self.meals_grid = QGridLayout()
        self.meals_grid.setSpacing(10)
        for col in range(3):
            self.meals_grid.setColumnStretch(col, 1)
        content_layout.addLayout(self.meals_grid)

        # 五餐合计小结
        self.total_summary = QLabel()
        self.total_summary.setStyleSheet(f"color: {COLORS['success']}; padding: 6px 0; font-size: 12px;")
        content_layout.addWidget(self.total_summary)

        # ── 补剂方案 ──
        supp_title = QLabel('💊 补剂方案')
        supp_title.setFont(QFont('Microsoft YaHei', 13, QFont.Bold))
        supp_title.setStyleSheet(f"color: {COLORS['primary']}; padding-top: 12px;")
        content_layout.addWidget(supp_title)

        self.supplement_table = QWidget()
        supp_layout = QVBoxLayout(self.supplement_table)
        supp_layout.setSpacing(4)
        content_layout.addWidget(self.supplement_table)

        # ── 饮水控盐 ──
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

        # 初始刷新
        self._refresh_all()

    # ── 控件工厂 ──

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

        # 值 + 单位在同一行
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

        # 对比目标
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

        # 标题行: 餐名 + 热量
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

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        cv.addWidget(sep)

        # 食材列表
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

    # ── 事件 ──

    def _on_week_changed(self, idx: int):
        self.current_week = idx + 1
        # Phase 3 才显示中碳日/高碳日按钮
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

        # 阶段标签
        day_type_name = {'training': '训练日', 'rest': '休息日', 'medium': '中碳日', 'high_carb': '高碳日'}[self.current_day_type]
        self.phase_label.setText(
            f"📍 {info['name']} ({info['weeks']}) — {info['desc']} | 当前: {day_type_name} 营养方案"
        )

        # 宏量数字卡片
        macro_keys = [('kcal', 0), ('protein', 1), ('carbs', 2), ('fat', 3)]
        for key, _ in macro_keys:
            target = macros[key]
            actual = daily.get(key, 0) if key in daily else 0
            panel = self.macro_labels[key]
            val_label = panel.findChild(QLabel, 'macro_value')
            cmp_label = panel.findChild(QLabel, 'macro_cmp')
            if val_label:
                val_label.setText(str(target))

        self._update_macro_panel('kcal', macros['kcal'], daily.get('kcal', 0), 'kcal')
        self._update_macro_panel('protein', macros['protein'], daily.get('protein', 0), 'g')
        self._update_macro_panel('carbs', macros['carbs'], daily.get('carbs', 0), 'g')
        self._update_macro_panel('fat', macros['fat'], daily.get('fat', 0), 'g')

        self.protein_pct_label.setText(
            f"蛋白质占比: {macros['protein_pct']}% (目标) | 五餐合计: "
            f"P{daily['protein']}g C{daily['carbs']}g F{daily['fat']}g = {daily['kcal']}kcal"
        )

        # 五餐卡片
        while self.meals_grid.count():
            item = self.meals_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, meal in enumerate(meals):
            card = self._make_meal_card(meal)
            self.meals_grid.addWidget(card, i // 3, i % 3)

        # 五餐合计
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

        # 补剂表格
        while self.supplement_table.layout().count():
            item = self.supplement_table.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in supplements:
            self.supplement_table.layout().addWidget(self._make_supplement_row(s))

        # 饮水控盐
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
            diff = actual - target
            if unit == 'kcal':
                diff_str = f"五餐合计: {actual}kcal (求值{target}kcal)"
            else:
                diff_str = f"五餐合计: {actual}g (目标{target}g)"
            cmp_label.setText(diff_str)
