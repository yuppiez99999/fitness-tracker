# -*- coding: utf-8 -*-
"""
体脂体重监控程序 v6.0 — 数据导入 + 趋势图表 + 报告生成
支持: TXT/CSV/Excel 多源导入, 自动编码检测, 专业减脂趋势图
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import MaxNLocator
from datetime import datetime, timedelta
import os, sys

# ─── 中文字体配置 ───
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Microsoft JhengHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ─── 路径配置 ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '体重体脂监控')
CHART_DIR = os.path.join(DATA_DIR, '图表')
REPORT_DIR = os.path.join(DATA_DIR, '报告')
DATA_FILE = os.path.join(DATA_DIR, '体脂体重.txt')

for d in [DATA_DIR, CHART_DIR, REPORT_DIR]:
    os.makedirs(d, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# 主应用
# ═══════════════════════════════════════════════════════════

class BodyWeightMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("体脂体重监控 v6.0")
        self.root.geometry("1400x850")
        self.root.minsize(1100, 700)
        self.root.configure(bg='#f0f2f5')

        # 目标
        self.target_weight = 67.0
        self.target_bodyfat = 17.0

        # 加载数据
        self.df = self.load_data()

        # 图标路径
        self._setup_style()
        self._build_ui()
        self.refresh_all()

        # 窗口关闭
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ─── 样式 ───
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'),
                        background='#f0f2f5', foreground='#1a1a2e')
        style.configure('Card.TFrame', background='white', relief='solid', borderwidth=1)
        style.configure('Stat.TLabel', font=('Microsoft YaHei', 11),
                        background='white', foreground='#333')
        style.configure('StatValue.TLabel', font=('Microsoft YaHei', 18, 'bold'),
                        background='white', foreground='#1890ff')
        style.configure('Danger.TLabel', font=('Microsoft YaHei', 18, 'bold'),
                        background='white', foreground='#e74c3c')
        style.configure('Green.TLabel', font=('Microsoft YaHei', 18, 'bold'),
                        background='white', foreground='#27ae60')
        style.configure('Btn.TButton', font=('Microsoft YaHei', 10), padding=(12, 6))

    # ─── 数据加载 ───
    def load_data(self):
        """自动检测编码加载数据"""
        if not os.path.exists(DATA_FILE):
            return pd.DataFrame(columns=['日期', '体重(kg)', '体脂率(%)'])

        for enc in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030']:
            try:
                df = pd.read_csv(DATA_FILE, encoding=enc)
                df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
                df = df.sort_values('日期').reset_index(drop=True)
                return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        return pd.DataFrame(columns=['日期', '体重(kg)', '体脂率(%)'])

    def save_data(self):
        """保存数据"""
        try:
            self.df.to_csv(DATA_FILE, index=False, encoding='utf-8')
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    # ─── UI 构建 ───
    def _build_ui(self):
        # 顶部标题栏
        title_bar = tk.Frame(self.root, bg='#1a1a2e', height=56)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="体脂体重监控系统 v6.0", font=('Microsoft YaHei', 15, 'bold'),
                 fg='white', bg='#1a1a2e').pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(title_bar, text="3月5日 - 6月26日 · 减脂记录",
                 font=('Microsoft YaHei', 10), fg='#a0a0b0', bg='#1a1a2e').pack(side=tk.LEFT, pady=14)

        # 主布局
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#e0e0e0',
                                      sashwidth=3, sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ── 左侧面板 ──
        left = tk.Frame(main_paned, bg='#f0f2f5', width=520)
        main_paned.add(left)

        # 统计卡片
        self._build_stats_panel(left)

        # 数据表格
        self._build_table(left)

        # ── 右侧面板 (图表) ──
        right = tk.Frame(main_paned, bg='#f0f2f5')
        main_paned.add(right)
        self._build_chart_panel(right)

        # ── 底部按钮栏 ──
        btn_bar = tk.Frame(self.root, bg='#f0f2f5', height=50)
        btn_bar.pack(fill=tk.X, padx=8, pady=(0, 8))
        btn_bar.pack_propagate(False)

        buttons = [
            ("导入TXT/CSV", self.import_text, '#1890ff'),
            ("导入Excel", self.import_excel, '#52c41a'),
            ("添加记录", self.add_record, '#fa8c16'),
            ("编辑记录", self.edit_record, '#722ed1'),
            ("删除记录", self.delete_record, '#e74c3c'),
            ("刷新", self.refresh_all, '#595959'),
            ("生成报告", self.generate_report, '#f5222d'),
            ("保存图表", self.save_chart_png, '#13c2c2'),
        ]

        for i, (text, cmd, color) in enumerate(buttons):
            b = tk.Button(btn_bar, text=text, command=cmd,
                          bg=color, fg='white', font=('Microsoft YaHei', 10),
                          relief=tk.FLAT, padx=14, pady=6, cursor='hand2',
                          activebackground=color, activeforeground='white')
            b.bind('<Enter>', lambda e, btn=b, c=color: btn.configure(bg=self._lighten(c)))
            b.bind('<Leave>', lambda e, btn=b, c=color: btn.configure(bg=c))
            b.pack(side=tk.LEFT, padx=4, pady=8)

    def _lighten(self, hex_color):
        """颜色变浅"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 20); g = min(255, g + 20); b = min(255, b + 20)
        return f'#{r:02x}{g:02x}{b:02x}'

    def _build_stats_panel(self, parent):
        """统计卡片面板"""
        stats_frame = tk.Frame(parent, bg='#f0f2f5')
        stats_frame.pack(fill=tk.X, padx=6, pady=(6, 4))

        # 6格卡片
        self.stat_labels = {}
        cards = [
            ("总记录", "0 天", '#1890ff'),
            ("当前体重", "0.0 kg", '#e74c3c'),
            ("距目标67kg", "—", '#fa8c16'),
            ("当前体脂", "0.0%", '#e74c3c'),
            ("距目标17%", "—", '#fa8c16'),
            ("已减体重", "0.0 kg", '#27ae60'),
            ("已降体脂", "0.0%", '#27ae60'),
            ("体重达标日", "—", '#722ed1'),
            ("体脂达标日", "—", '#722ed1'),
        ]

        for i, (title, value, color) in enumerate(cards):
            row = i // 3
            col = i % 3
            card = tk.Frame(stats_frame, bg='white', relief=tk.FLAT,
                            highlightbackground='#e8e8e8', highlightthickness=1)
            card.grid(row=row, column=col, padx=3, pady=4, sticky='nsew')
            stats_frame.grid_columnconfigure(col, weight=1)

            tk.Label(card, text=title, font=('Microsoft YaHei', 9),
                     bg='white', fg='#888').pack(pady=(8, 2))
            lbl = tk.Label(card, text=value, font=('Microsoft YaHei', 16, 'bold'),
                           bg='white', fg=color)
            lbl.pack(pady=(0, 8))
            self.stat_labels[title] = lbl

        # 进度条
        progress_frame = tk.Frame(parent, bg='#f0f2f5')
        progress_frame.pack(fill=tk.X, padx=6, pady=(0, 4))

        # 体重进度
        tk.Label(progress_frame, text="减重进度",
                 font=('Microsoft YaHei', 9), bg='#f0f2f5', fg='#666').pack(anchor=tk.W)
        self.weight_canvas = tk.Canvas(progress_frame, height=22, bg='#f0f2f5',
                                        highlightthickness=0, bd=0)
        self.weight_canvas.pack(fill=tk.X, pady=(2, 6))

        # 体脂进度
        tk.Label(progress_frame, text="减脂进度",
                 font=('Microsoft YaHei', 9), bg='#f0f2f5', fg='#666').pack(anchor=tk.W)
        self.fat_canvas = tk.Canvas(progress_frame, height=22, bg='#f0f2f5',
                                     highlightthickness=0, bd=0)
        self.fat_canvas.pack(fill=tk.X, pady=(2, 2))

    def _build_table(self, parent):
        """数据表格 + 底部常驻输入栏"""
        table_frame = tk.Frame(parent, bg='#f0f2f5')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        # Treeview
        columns = ('日期', '体重(kg)', '体脂率(%)')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                                  height=18, selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col, anchor=tk.CENTER)
            self.tree.column(col, width=130, anchor=tk.CENTER, minwidth=80)

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击编辑
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_record())

        # 常驻输入栏
        input_bar = tk.Frame(table_frame, bg='#f0f2f5')
        input_bar.pack(fill=tk.X, pady=(6, 2))

        today = datetime.now().strftime('%Y-%m-%d')
        self.entry_vars = {
            '日期': tk.StringVar(value=today),
            '体重(kg)': tk.StringVar(value=''),
            '体脂率(%)': tk.StringVar(value=''),
        }
        for label, var in self.entry_vars.items():
            frm = tk.Frame(input_bar, bg='#f0f2f5')
            frm.pack(side=tk.LEFT, padx=6)
            tk.Label(frm, text=label, font=('Microsoft YaHei', 9),
                     bg='#f0f2f5', fg='#666').pack(anchor=tk.W)
            tk.Entry(frm, textvariable=var, font=('Microsoft YaHei', 10),
                     width=12).pack(anchor=tk.W)

        tk.Button(input_bar, text='＋ 快速录入',
                  command=self.add_record_from_bar,
                  bg='#52c41a', fg='white', font=('Microsoft YaHei', 10, 'bold'),
                  relief=tk.FLAT, padx=12, pady=4, cursor='hand2').pack(side=tk.RIGHT, padx=6)

    def _build_chart_panel(self, parent):
        """图表面板 — Tab切换"""
        self.chart_notebook = ttk.Notebook(parent)
        self.chart_notebook.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Tab 1: 趋势图
        self.trend_frame = tk.Frame(self.chart_notebook, bg='white')
        self.chart_notebook.add(self.trend_frame, text='  减脂趋势图  ')

        # Tab 2: 变化对比图
        self.compare_frame = tk.Frame(self.chart_notebook, bg='white')
        self.chart_notebook.add(self.compare_frame, text='  变化对比图  ')

        # Tab 3: 周度统计
        self.weekly_frame = tk.Frame(self.chart_notebook, bg='white')
        self.chart_notebook.add(self.weekly_frame, text='  周度分析  ')

        self.chart_notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

    def _on_tab_changed(self, event):
        """Tab切换时更新图表"""
        idx = self.chart_notebook.index('current')
        if idx == 0:
            self._draw_trend_chart()
        elif idx == 1:
            self._draw_compare_chart()
        elif idx == 2:
            self._draw_weekly_chart()

    # ─── 进度条绘制 ───
    def _draw_progress(self, canvas, pct, color):
        canvas.delete('all')
        w = canvas.winfo_width()
        if w < 10:
            w = 400
        bar_h = 18
        pad = 2
        # 背景
        canvas.create_rectangle(pad, pad, w - pad, bar_h + pad,
                                 fill='#e8e8e8', outline='#ddd', width=1)
        # 进度
        fill_w = max(pad + 4, (w - 2 * pad) * min(pct, 1.0))
        canvas.create_rectangle(pad, pad, fill_w, bar_h + pad,
                                 fill=color, outline='', width=0)
        # 文字
        canvas.create_text(w / 2, bar_h / 2 + pad,
                           text=f'{pct*100:.1f}%', font=('Microsoft YaHei', 8, 'bold'),
                           fill='#333')

    # ─── 数据刷新 ───
    def refresh_all(self):
        """刷新全部界面"""
        self._refresh_table()
        self._refresh_stats()
        self._draw_trend_chart()

    def _refresh_table(self):
        """刷新数据表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for _, row in self.df.iterrows():
            fat = f"{row['体脂率(%)']:.1f}" if pd.notna(row['体脂率(%)']) else '—'
            self.tree.insert('', tk.END,
                             values=(row['日期'], f"{row['体重(kg)']:.1f}", fat))

    def _refresh_stats(self):
        """刷新统计面板"""
        n = len(self.df)
        self.stat_labels['总记录'].configure(text=f"{n} 天")

        if n == 0:
            for key in ['当前体重', '当前体脂', '已减体重', '已降体脂', '体重达标日', '体脂达标日', '距目标67kg', '距目标17%']:
                self.stat_labels[key].configure(text='—')
            self._draw_progress(self.weight_canvas, 0, '#1890ff')
            self._draw_progress(self.fat_canvas, 0, '#e74c3c')
            return

        latest = self.df.iloc[-1]
        first = self.df.iloc[0]
        init_w = first['体重(kg)']
        cur_w = latest['体重(kg)']

        self.stat_labels['当前体重'].configure(text=f"{cur_w:.1f} kg")
        self.stat_labels['已减体重'].configure(text=f"{init_w - cur_w:.1f} kg")

        # 距目标体重差
        to_go_w = cur_w - self.target_weight
        if to_go_w <= 0:
            self.stat_labels['距目标67kg'].configure(text="✅ 已达成", fg='#27ae60')
        else:
            self.stat_labels['距目标67kg'].configure(text=f"差 {to_go_w:.1f} kg", fg='#fa8c16')

        # 体重达标日查找
        weight_target_hit = self.df[self.df['体重(kg)'] <= self.target_weight]
        if len(weight_target_hit) > 0:
            self.stat_labels['体重达标日'].configure(
                text=weight_target_hit['日期'].iloc[0], fg='#27ae60')
        else:
            # 线性拟合预测
            if len(self.df) >= 5:
                w_data = self.df.copy()
                w_data['days'] = (pd.to_datetime(w_data['日期']) -
                                   pd.to_datetime(w_data['日期'].iloc[0])).dt.days
                z = np.polyfit(w_data['days'].values, w_data['体重(kg)'].values, 1)
                if z[0] < 0:
                    pred_days = int((self.target_weight - z[1]) / z[0])
                    if pred_days > 0:
                        pred_date = (pd.to_datetime(w_data['日期'].iloc[0]) +
                                      timedelta(days=pred_days))
                        self.stat_labels['体重达标日'].configure(
                            text=pred_date.strftime('%m-%d'), fg='#fa8c16')
                    else:
                        self.stat_labels['体重达标日'].configure(text='即将达成', fg='#fa8c16')
                else:
                    self.stat_labels['体重达标日'].configure(text='趋势异常', fg='#e74c3c')
            else:
                self.stat_labels['体重达标日'].configure(text='数据不足', fg='#999')

        # 体重进度
        total_w_loss = init_w - self.target_weight
        if total_w_loss > 0:
            w_pct = (init_w - cur_w) / total_w_loss
        else:
            w_pct = 1.0 if cur_w <= self.target_weight else 0
        w_pct = max(0, min(1, w_pct))
        self._draw_progress(self.weight_canvas, w_pct, '#1890ff')

        # 体脂
        has_fat = self.df['体脂率(%)'].dropna()
        if len(has_fat) > 0:
            cur_fat = latest['体脂率(%)'] if pd.notna(latest['体脂率(%)']) else has_fat.iloc[-1]
            init_fat = has_fat.iloc[0]
            self.stat_labels['当前体脂'].configure(text=f"{cur_fat:.1f}%")
            fat_loss = init_fat - cur_fat
            self.stat_labels['已降体脂'].configure(text=f"{fat_loss:.1f}%")

            # 距目标体脂差
            to_go_f = cur_fat - self.target_bodyfat
            if to_go_f <= 0:
                self.stat_labels['距目标17%'].configure(text="✅ 已达成", fg='#27ae60')
            else:
                self.stat_labels['距目标17%'].configure(text=f"差 {to_go_f:.1f}%", fg='#fa8c16')

            # 找体脂首次达标日
            fat_total = init_fat - self.target_bodyfat
            if fat_total > 0:
                f_pct = (init_fat - cur_fat) / fat_total
            else:
                f_pct = 1.0 if cur_fat <= self.target_bodyfat else 0
            f_pct = max(0, min(1, f_pct))
            self._draw_progress(self.fat_canvas, f_pct, '#e74c3c')

            # 体脂达标日查找
            target_hit = self.df[(self.df['体脂率(%)'].notna()) &
                                  (self.df['体脂率(%)'] <= self.target_bodyfat)]
            if len(target_hit) > 0:
                self.stat_labels['体脂达标日'].configure(
                    text=target_hit['日期'].iloc[0], fg='#27ae60')
            else:
                # 线性拟合预测
                fat_data = self.df[self.df['体脂率(%)'].notna()].copy()
                if len(fat_data) >= 5:
                    fat_data['days'] = (pd.to_datetime(fat_data['日期']) -
                                         pd.to_datetime(fat_data['日期'].iloc[0])).dt.days
                    z = np.polyfit(fat_data['days'].values, fat_data['体脂率(%)'].values, 1)
                    if z[0] < 0:  # 下降趋势
                        pred_days = (self.target_bodyfat - z[1]) / z[0]
                        pred_date = (pd.to_datetime(fat_data['日期'].iloc[0]) +
                                      timedelta(days=int(pred_days)))
                        self.stat_labels['体脂达标日'].configure(
                            text=pred_date.strftime('%m-%d'), fg='#fa8c16')
                    else:
                        self.stat_labels['体脂达标日'].configure(text='趋势异常', fg='#e74c3c')
                else:
                    self.stat_labels['体脂达标日'].configure(text='数据不足', fg='#999')
        else:
            self.stat_labels['当前体脂'].configure(text='—')
            self.stat_labels['已降体脂'].configure(text='—')
            self.stat_labels['距目标17%'].configure(text='无数据', fg='#999')
            self.stat_labels['体脂达标日'].configure(text='无体脂数据')

    # ─── 图表绘制 ───
    def _draw_trend_chart(self):
        """Tab1: 趋势图"""
        for w in self.trend_frame.winfo_children():
            w.destroy()

        if len(self.df) < 2:
            tk.Label(self.trend_frame, text="需要至少2条记录",
                     font=('Microsoft YaHei', 14), bg='white',
                     fg='#999').pack(expand=True)
            return

        plot_df = self.df.copy()
        plot_df['日期_dt'] = pd.to_datetime(plot_df['日期'])
        plot_df = plot_df.sort_values('日期_dt')

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5))
        fig.subplots_adjust(hspace=0.35, top=0.93, bottom=0.1, left=0.1, right=0.95)

        is_dark = False
        fig.patch.set_facecolor('white')
        for ax in [ax1, ax2]:
            ax.set_facecolor('white')
            ax.tick_params(colors='#333', labelsize=7)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        # ── 体重图 ──
        ax1.plot(plot_df['日期_dt'], plot_df['体重(kg)'],
                 color='#1890ff', linewidth=2, marker='o', markersize=3,
                 markerfacecolor='#1890ff', markeredgecolor='white',
                 markeredgewidth=0.5, label='每日体重', zorder=3)

        # 7日均线
        ma = plot_df['体重(kg)'].rolling(7, min_periods=1).mean()
        ax1.plot(plot_df['日期_dt'], ma, color='#91caff', linewidth=1.5,
                 linestyle='--', alpha=0.8, label='7日均线')

        # 目标线
        ax1.axhline(y=self.target_weight, color='#e74c3c', linestyle='--',
                     linewidth=1.2, alpha=0.8, label=f'目标 {self.target_weight:.0f}kg')

        # 填充
        ax1.fill_between(plot_df['日期_dt'], plot_df['体重(kg)'],
                          alpha=0.08, color='#1890ff')

        ax1.set_ylim(bottom=65)
        ax1.set_ylabel('体重 (kg)', fontsize=10, color='#333')
        ax1.set_title('体重变化趋势', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)
        ax1.legend(loc='upper right', fontsize=7, framealpha=0.8)
        ax1.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

        # ── 体脂图 ──
        fat_data = plot_df[plot_df['体脂率(%)'].notna()]
        if len(fat_data) > 0:
            ax2.plot(fat_data['日期_dt'], fat_data['体脂率(%)'],
                     color='#e74c3c', linewidth=2, marker='o', markersize=3,
                     markerfacecolor='#e74c3c', markeredgecolor='white',
                     markeredgewidth=0.5, label='每日体脂率', zorder=3)

            fm = fat_data['体脂率(%)'].rolling(5, min_periods=1).mean()
            ax2.plot(fat_data['日期_dt'], fm, color='#ffa39e', linewidth=1.5,
                     linestyle='--', alpha=0.8, label='5日均线')

            ax2.axhline(y=self.target_bodyfat, color='#27ae60', linestyle='--',
                         linewidth=1.2, alpha=0.8, label=f'目标 {self.target_bodyfat:.0f}%')

            ax2.fill_between(fat_data['日期_dt'], fat_data['体脂率(%)'],
                              alpha=0.08, color='#e74c3c')
        else:
            ax2.text(0.5, 0.5, '暂无体脂率数据', transform=ax2.transAxes,
                     ha='center', va='center', fontsize=14, color='#999')

        ax2.set_ylim(bottom=15)
        ax2.set_ylabel('体脂率 (%)', fontsize=10, color='#333')
        ax2.set_title('体脂率变化趋势', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)
        ax2.legend(loc='upper right', fontsize=7, framealpha=0.8)
        ax2.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)

        # 格式化x轴
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
            for label in ax.get_xticklabels():
                label.set_rotation(30)
                label.set_fontsize(7)

        self._embed_chart(fig, self.trend_frame)

    def _draw_compare_chart(self):
        """Tab2: 变化对比图"""
        for w in self.compare_frame.winfo_children():
            w.destroy()

        if len(self.df) < 2:
            tk.Label(self.compare_frame, text="需要至少2条记录",
                     font=('Microsoft YaHei', 14), bg='white',
                     fg='#999').pack(expand=True)
            return

        plot_df = self.df.copy()
        plot_df['日期_dt'] = pd.to_datetime(plot_df['日期'])
        plot_df = plot_df.sort_values('日期_dt')

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5))
        fig.subplots_adjust(hspace=0.35, top=0.93, bottom=0.1, left=0.1, right=0.95)
        fig.patch.set_facecolor('white')

        # ── 日均减重 ──
        daily_loss = []
        dates = []
        for i in range(1, len(plot_df)):
            day_diff = (plot_df['日期_dt'].iloc[i] - plot_df['日期_dt'].iloc[i-1]).days
            if day_diff > 0:
                daily_loss.append((plot_df['体重(kg)'].iloc[i-1] - plot_df['体重(kg)'].iloc[i]) / day_diff)
                dates.append(plot_df['日期_dt'].iloc[i])

        colors_bar = ['#52c41a' if v >= 0 else '#e74c3c' for v in daily_loss]
        ax1.bar(dates, daily_loss, color=colors_bar, alpha=0.8, width=0.8)
        ax1.axhline(y=0, color='#333', linewidth=0.5)
        ax1.set_ylabel('日均体重变化 (kg/天)', fontsize=10)
        ax1.set_title('每日体重变化量', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)
        ax1.grid(True, alpha=0.2, axis='y')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # ── 累计减重对比 ──
        cum_loss = plot_df['体重(kg)'].iloc[0] - plot_df['体重(kg)']
        ax2.fill_between(plot_df['日期_dt'], cum_loss, alpha=0.3, color='#1890ff')
        ax2.plot(plot_df['日期_dt'], cum_loss, color='#1890ff', linewidth=2)
        # 标记最高点
        max_idx = cum_loss.idxmax()
        ax2.annotate(f"累计 {cum_loss[max_idx]:.1f}kg",
                     (plot_df['日期_dt'].iloc[max_idx], cum_loss[max_idx]),
                     textcoords="offset points", xytext=(0, 10),
                     fontsize=9, ha='center', color='#1890ff',
                     arrowprops=dict(arrowstyle='->', color='#1890ff', lw=1))

        ax2.set_ylabel('累计减重 (kg)', fontsize=10)
        ax2.set_title('累计减重趋势', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)
        ax2.grid(True, alpha=0.2)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # 格式化
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
            for label in ax.get_xticklabels():
                label.set_rotation(30)
                label.set_fontsize(7)
            ax.tick_params(colors='#333', labelsize=7)
            ax.set_facecolor('white')

        self._embed_chart(fig, self.compare_frame)

    def _draw_weekly_chart(self):
        """Tab3: 周度分析"""
        for w in self.weekly_frame.winfo_children():
            w.destroy()

        if len(self.df) < 2:
            tk.Label(self.weekly_frame, text="需要至少2条记录",
                     font=('Microsoft YaHei', 14), bg='white',
                     fg='#999').pack(expand=True)
            return

        plot_df = self.df.copy()
        plot_df['日期_dt'] = pd.to_datetime(plot_df['日期'])
        plot_df = plot_df.sort_values('日期_dt')
        plot_df['周'] = plot_df['日期_dt'].dt.isocalendar().week.astype(int)

        weekly = plot_df.groupby('周').agg(
            周均体重=('体重(kg)', 'mean'),
            最低体重=('体重(kg)', 'min'),
            体脂均值=('体脂率(%)', lambda x: x.dropna().mean() if x.notna().any() else np.nan),
            记录数=('体重(kg)', 'count')
        ).reset_index()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5))
        fig.subplots_adjust(hspace=0.35, top=0.93, bottom=0.1, left=0.1, right=0.95)
        fig.patch.set_facecolor('white')

        # 周均体重
        x = range(len(weekly))
        ax1.plot(x, weekly['周均体重'], 'b-o', linewidth=2, markersize=6, color='#1890ff')
        ax1.fill_between(x, weekly['周均体重'], weekly['最低体重'],
                          alpha=0.2, color='#1890ff',
                          label='最低-均值范围')
        ax1.axhline(y=self.target_weight, color='#e74c3c', linestyle='--',
                     linewidth=1.2, alpha=0.8, label=f'目标 {self.target_weight:.0f}kg')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'W{w}' for w in weekly['周']], fontsize=7)
        ax1.set_ylim(bottom=65)
        ax1.set_ylabel('体重 (kg)', fontsize=10)
        ax1.set_title('周度体重变化', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)
        ax1.legend(fontsize=7)
        ax1.grid(True, alpha=0.2)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.tick_params(colors='#333', labelsize=7)
        ax1.set_facecolor('white')

        # 体脂下降
        fat_weekly = weekly.dropna(subset=['体脂均值'])
        if len(fat_weekly) > 0:
            bars = ax2.bar(x, weekly['记录数'], color='#91caff', alpha=0.8,
                           label='记录天数')
            ax2.set_ylabel('记录天数', fontsize=10, color='#1890ff')
            ax2.set_title('周度记录密度', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)

            # 双轴：体脂
            ax2b = ax2.twinx()
            ax2b.plot([i for i in range(len(fat_weekly))],
                       fat_weekly['体脂均值'],
                       'r-o', linewidth=2, markersize=5, color='#e74c3c',
                       label='周均体脂')
            ax2b.set_ylim(bottom=15)
            ax2b.set_ylabel('体脂率 (%)', fontsize=10, color='#e74c3c')
            ax2b.tick_params(colors='#e74c3c', labelsize=7)
            ax2b.spines['top'].set_visible(False)
        else:
            ax2.bar(x, weekly['记录数'], color='#91caff', alpha=0.8)
            ax2.set_title('周度记录密度', fontsize=13, fontweight='bold', color='#1a1a2e', pad=8)

        ax2.set_xticks(x)
        ax2.set_xticklabels([f'W{w}' for w in weekly['周']], fontsize=7)
        ax2.grid(True, alpha=0.2, axis='y')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.tick_params(colors='#333', labelsize=7)
        ax2.set_facecolor('white')

        self._embed_chart(fig, self.weekly_frame)

    def _embed_chart(self, fig, frame):
        """将matplotlib图表嵌入tkinter Frame"""
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 保存引用
        self.current_canvas = canvas
        self.current_fig = fig

    # ─── 导入数据 ───
    def import_text(self):
        """导入TXT/CSV文件"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("文本文件", "*.txt *.csv"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        try:
            # 自动编码检测
            for enc in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'gb18030']:
                try:
                    df_new = pd.read_csv(file_path, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                messagebox.showerror("错误", "无法识别文件编码")
                return

            df_new = self._normalize_columns(df_new, file_path)
            if df_new is None:
                return

            # 合并
            self.df = pd.concat([self.df, df_new], ignore_index=True)
            self.df['日期'] = pd.to_datetime(self.df['日期']).dt.strftime('%Y-%m-%d')
            self.df = self.df.drop_duplicates(subset=['日期'], keep='last')
            self.df = self.df.sort_values('日期').reset_index(drop=True)

            self.save_data()
            self.refresh_all()
            messagebox.showinfo("导入成功", f"已导入，当前共 {len(self.df)} 条记录")

        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def import_excel(self):
        """导入Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        try:
            df_new = pd.read_excel(file_path)
            df_new = self._normalize_columns(df_new, file_path)
            if df_new is None:
                return

            self.df = pd.concat([self.df, df_new], ignore_index=True)
            self.df['日期'] = pd.to_datetime(self.df['日期']).dt.strftime('%Y-%m-%d')
            self.df = self.df.drop_duplicates(subset=['日期'], keep='last')
            self.df = self.df.sort_values('日期').reset_index(drop=True)

            self.save_data()
            self.refresh_all()
            messagebox.showinfo("导入成功", f"已导入，当前共 {len(self.df)} 条记录")

        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def _normalize_columns(self, df, file_path):
        """标准化列名映射"""
        col_map = {}
        for col in df.columns:
            col_s = str(col).strip()
            if col_s in ['日期', 'date', 'Date', '时间']:
                col_map[col] = '日期'
            elif any(k in col_s for k in ['体重', 'weight', 'Weight']):
                col_map[col] = '体重(kg)'
            elif any(k in col_s for k in ['体脂', 'bodyfat', 'body_fat', 'BodyFat', 'fat']):
                col_map[col] = '体脂率(%)'

        df = df.rename(columns=col_map)

        if '日期' not in df.columns or '体重(kg)' not in df.columns:
            # 尝试位置映射
            if len(df.columns) >= 2:
                cols = list(df.columns)
                rename = {cols[0]: '日期', cols[1]: '体重(kg)'}
                if len(cols) >= 3:
                    rename[cols[2]] = '体脂率(%)'
                df = df.rename(columns=rename)
            else:
                messagebox.showerror("格式错误", f"文件需包含日期和体重列\n当前列: {df.columns.tolist()}")
                return None

        # 确保体脂率列存在
        if '体脂率(%)' not in df.columns:
            df['体脂率(%)'] = np.nan

        # 保留核心列
        df = df[['日期', '体重(kg)', '体脂率(%)']].copy()
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce').dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['日期'])
        df['体重(kg)'] = pd.to_numeric(df['体重(kg)'], errors='coerce')
        df['体脂率(%)'] = pd.to_numeric(df['体脂率(%)'], errors='coerce')
        df = df.dropna(subset=['体重(kg)'])

        if len(df) == 0:
            messagebox.showerror("错误", "未解析到有效数据")
            return None

        return df

    # ─── 记录操作 ───
    def add_record(self):
        """添加新记录（弹窗）"""
        today = datetime.now().strftime('%Y-%m-%d')

        # 创建输入对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加记录")
        dialog.geometry("320x220")
        dialog.resizable(False, False)
        dialog.configure(bg='#f0f2f5')
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 320) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="添加体重体脂记录", font=('Microsoft YaHei', 13, 'bold'),
                 bg='#f0f2f5', fg='#1a1a2e').pack(pady=(12, 8))

        fields = {}
        for label, default in [('日期', today), ('体重(kg)', ''), ('体脂率(%)', '')]:
            frm = tk.Frame(dialog, bg='#f0f2f5')
            frm.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(frm, text=label, font=('Microsoft YaHei', 10),
                     bg='#f0f2f5', width=10, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value=default)
            tk.Entry(frm, textvariable=var, font=('Microsoft YaHei', 10),
                     width=15).pack(side=tk.LEFT, padx=4)
            fields[label] = var

        def do_add():
            self._commit_record(
                date=fields['日期'].get().strip(),
                weight_str=fields['体重(kg)'].get().strip(),
                fat_str=fields['体脂率(%)'].get().strip(),
                on_success=lambda: dialog.destroy()
            )

        tk.Button(dialog, text="确认添加", command=do_add,
                  bg='#1890ff', fg='white', font=('Microsoft YaHei', 11),
                  relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(pady=15)

    def add_record_from_bar(self):
        """从底部常驻输入栏快速录入"""
        self._commit_record(
            date=self.entry_vars['日期'].get().strip(),
            weight_str=self.entry_vars['体重(kg)'].get().strip(),
            fat_str=self.entry_vars['体脂率(%)'].get().strip(),
            on_success=lambda: (
                self.entry_vars['体重(kg)'].set(''),
                self.entry_vars['体脂率(%)'].set('')
            )
        )

    def _commit_record(self, date: str, weight_str: str, fat_str: str, on_success=None):
        """统一录入逻辑"""
        if not date:
            messagebox.showwarning("提示", "请输入日期")
            return
        try:
            weight = float(weight_str)
        except ValueError:
            messagebox.showerror("错误", "请输入有效体重")
            return

        fat = float(fat_str) if fat_str else np.nan

        new_row = pd.DataFrame([{'日期': date, '体重(kg)': weight, '体脂率(%)': fat}])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.df['日期'] = pd.to_datetime(self.df['日期']).dt.strftime('%Y-%m-%d')
        self.df = self.df.drop_duplicates(subset=['日期'], keep='last')
        self.df = self.df.sort_values('日期').reset_index(drop=True)
        self.save_data()
        self.refresh_all()
        messagebox.showinfo("成功", f"已添加 {date} 的记录")
        if on_success:
            on_success()

    def edit_record(self):
        """编辑选中记录"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在表格中选中一条记录")
            return

        values = self.tree.item(sel[0])['values']
        old_date = str(values[0])

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑记录")
        dialog.geometry("320x220")
        dialog.resizable(False, False)
        dialog.configure(bg='#f0f2f5')
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 320) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="编辑记录", font=('Microsoft YaHei', 13, 'bold'),
                 bg='#f0f2f5', fg='#1a1a2e').pack(pady=(12, 8))

        fields = {}
        for label, default in [('日期', values[0]), ('体重(kg)', values[1]),
                                ('体脂率(%)', values[2] if values[2] != '—' else '')]:
            frm = tk.Frame(dialog, bg='#f0f2f5')
            frm.pack(fill=tk.X, padx=30, pady=3)
            tk.Label(frm, text=label, font=('Microsoft YaHei', 10),
                     bg='#f0f2f5', width=10, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            tk.Entry(frm, textvariable=var, font=('Microsoft YaHei', 10),
                     width=15).pack(side=tk.LEFT, padx=4)
            fields[label] = var

        def do_edit():
            new_date = fields['日期'].get().strip()
            try:
                weight = float(fields['体重(kg)'].get().strip())
                fat_str = fields['体脂率(%)'].get().strip()
                fat = float(fat_str) if fat_str else np.nan

                # 更新或删除旧记录
                mask = self.df['日期'] == old_date
                self.df.loc[mask, '日期'] = new_date
                self.df.loc[mask, '体重(kg)'] = weight
                self.df.loc[mask, '体脂率(%)'] = fat

                self.df['日期'] = pd.to_datetime(self.df['日期']).dt.strftime('%Y-%m-%d')
                self.df = self.df.drop_duplicates(subset=['日期'], keep='last')
                self.df = self.df.sort_values('日期').reset_index(drop=True)
                self.save_data()
                self.refresh_all()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("错误", "请输入有效数字")

        tk.Button(dialog, text="确认修改", command=do_edit,
                  bg='#722ed1', fg='white', font=('Microsoft YaHei', 11),
                  relief=tk.FLAT, padx=20, pady=5, cursor='hand2').pack(pady=15)

    def delete_record(self):
        """删除选中记录"""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在表格中选中一条记录")
            return

        values = self.tree.item(sel[0])['values']
        date = str(values[0])

        if messagebox.askyesno("确认删除", f"确定删除 {date} 的记录吗？\n体重: {values[1]} kg  体脂: {values[2]}"):
            self.df = self.df[self.df['日期'] != date].reset_index(drop=True)
            self.save_data()
            self.refresh_all()

    # ─── 报告与图表导出 ───
    def generate_report(self):
        """生成减脂报告"""
        if len(self.df) == 0:
            messagebox.showwarning("提示", "没有数据")
            return

        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(REPORT_DIR, f'减脂报告_{timestamp}.txt')

        df = self.df.copy()
        df['日期_dt'] = pd.to_datetime(df['日期'])

        first = df.iloc[0]
        latest = df.iloc[-1]
        days = (latest['日期_dt'] - first['日期_dt']).days

        weight_loss = first['体重(kg)'] - latest['体重(kg)']
        avg_daily = weight_loss / max(days, 1)

        has_fat = df['体脂率(%)'].dropna()
        fat_info = ""
        if len(has_fat) > 0:
            init_fat = has_fat.iloc[0]
            cur_fat = latest['体脂率(%)'] if pd.notna(latest['体脂率(%)']) else has_fat.iloc[-1]
            fat_loss = init_fat - cur_fat
            fat_info = f"""体脂率: {init_fat}% → {cur_fat:.1f}%  (下降 {fat_loss:.1f}%)"""

        # 周均分析
        df['周'] = df['日期_dt'].dt.isocalendar().week
        weekly_avg = df.groupby('周')['体重(kg)'].mean()
        last_week_avg = weekly_avg.iloc[-1] if len(weekly_avg) > 0 else 0

        report = f"""╔══════════════════════════════════════════════════════╗
║          🏋️ 减脂进度报告                          ║
╠══════════════════════════════════════════════════════╣
║  生成时间: {now.strftime('%Y-%m-%d %H:%M')}
╠══════════════════════════════════════════════════════╣

📊 数据概览
  • 统计天数: {days} 天  ({first['日期']} — {latest['日期']})
  • 记录条数: {len(df)} 条
  • 体脂数据: {len(has_fat)} 条

⚖️ 体重变化
  • 初始体重: {first['体重(kg)']:.1f} kg
  • 当前体重: {latest['体重(kg)']:.1f} kg
  • 累计减重: {weight_loss:.1f} kg
  • 日均减重: {avg_daily*1000:.0f} 克/天
  • 本周均值: {last_week_avg:.1f} kg
  • 距目标差: {latest['体重(kg)'] - self.target_weight:.1f} kg

{fat_info}

📈 进度评估
  • 体重目标: {self.target_weight:.0f} kg — """

        if latest['体重(kg)'] <= self.target_weight:
            report += "✅ 已达成！"
        else:
            remaining = latest['体重(kg)'] - self.target_weight
            if avg_daily > 0:
                est_days = int(remaining / avg_daily)
                est_date = now + timedelta(days=est_days)
                report += f"预计 {est_days} 天后 ({est_date.strftime('%m-%d')}) 达标"
            else:
                report += "体重不再下降，需调整计划"

        if len(has_fat) > 0:
            report += f"\n  • 体脂目标: {self.target_bodyfat:.0f}% — "
            if pd.notna(latest['体脂率(%)']) and latest['体脂率(%)'] <= self.target_bodyfat:
                report += "✅ 已达成！"
            else:
                fat_data = df[df['体脂率(%)'].notna()].copy()
                if len(fat_data) >= 3:
                    fat_data['days'] = (fat_data['日期_dt'] - fat_data['日期_dt'].iloc[0]).dt.days
                    z = np.polyfit(fat_data['days'].values, fat_data['体脂率(%)'].values, 1)
                    if z[0] < 0 and pd.notna(latest['体脂率(%)']):
                        remain = latest['体脂率(%)'] - self.target_bodyfat
                        est = int(remain / abs(z[0]))
                        est_date = now + timedelta(days=est)
                        report += f"预计 {est} 天后 ({est_date.strftime('%m-%d')}) 达标"
                    else:
                        report += "趋势异常，需关注"

        weekly_list = ""
        for w, avg_w in weekly_avg.items():
            weekly_list += f"    第{w}周: {avg_w:.1f} kg\n"

        report += f"""

📅 周均体重
{weekly_list}
╚══════════════════════════════════════════════════════╝
"""
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # 同时保存图表
        chart_path = os.path.join(CHART_DIR, f'减脂趋势图_{timestamp}.png')
        if hasattr(self, 'current_fig'):
            self.current_fig.savefig(chart_path, dpi=150, bbox_inches='tight',
                                      facecolor='white', edgecolor='none')

        messagebox.showinfo("报告已生成",
                            f"报告: {report_path}\n图表: {chart_path if hasattr(self, 'current_fig') else 'N/A'}")

    def save_chart_png(self):
        """导出当前图表为PNG"""
        if not hasattr(self, 'current_fig') or self.current_fig is None:
            messagebox.showwarning("提示", "暂无图表可保存")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        tab_idx = self.chart_notebook.index('current')
        prefix = ['趋势图', '变化对比图', '周度分析'][tab_idx]
        chart_path = os.path.join(CHART_DIR, f'{prefix}_{timestamp}.png')

        self.current_fig.savefig(chart_path, dpi=150, bbox_inches='tight',
                                  facecolor='white', edgecolor='none')
        messagebox.showinfo("保存成功", f"图表已保存至:\n{chart_path}")

    def _on_close(self):
        """关闭窗口"""
        self.save_data()
        self.root.destroy()


# ═══════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    BodyWeightMonitor()
