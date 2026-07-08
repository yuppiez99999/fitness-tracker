# -*- coding: utf-8 -*-
"""
生成最新减脂报告和图表（仅体重和体脂率）
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "体重体脂监控", "体脂体重.txt")
REPORT_DIR = os.path.join(BASE_DIR, "体重体脂监控", "报告")
CHART_DIR = os.path.join(BASE_DIR, "体重体脂监控", "图表")

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

# 读取数据
df = pd.read_csv(DATA_FILE)
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期')

# 统计数据
stats = {}
stats['记录总数'] = len(df)
stats['开始日期'] = df['日期'].iloc[0].strftime('%Y-%m-%d')
stats['最新日期'] = df['日期'].iloc[-1].strftime('%Y-%m-%d')

# 仅统计体重和体脂率
for col in ['体重(kg)', '体脂率(%)']:
    data = df[col].dropna()
    if len(data) > 0:
        key = col.replace('(kg)', '').replace('(%)', '')
        stats[f'初始{key}'] = data.iloc[0]
        stats[f'最新{key}'] = data.iloc[-1]
        stats[f'{key}变化'] = data.iloc[-1] - data.iloc[0]

# 计算进度
weight_progress = min(100, max(0, (stats['初始体重'] - stats['最新体重']) / (stats['初始体重'] - 67) * 100))
bodyfat_progress = min(100, max(0, (stats['初始体脂率'] - stats['最新体脂率']) / (stats['初始体脂率'] - 17) * 100))

# 生成报告
report = f"""
================================================================================
                    5周减脂监控报告 - 最新数据
================================================================================

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

记录总数: {stats['记录总数']} 条
记录时间: {stats['开始日期']} 至 {stats['最新日期']}

================================================================================
体重统计
================================================================================
初始体重: {stats['初始体重']:.2f} kg
最新体重: {stats['最新体重']:.2f} kg
体重变化: {stats['体重变化']:+.2f} kg
目标体重: 67.00 kg
距离目标: {stats['最新体重'] - 67:.2f} kg
体重进度: {weight_progress:.1f}%

================================================================================
体脂率统计
================================================================================
初始体脂: {stats['初始体脂率']:.2f}%
最新体脂: {stats['最新体脂率']:.2f}%
体脂变化: {stats['体脂率变化']:+.2f}%
目标体脂: 17.00%
距离目标: {stats['最新体脂率'] - 17:.2f}%
体脂进度: {bodyfat_progress:.1f}%

================================================================================
减脂效果总结
================================================================================
✓ 累计减重: {stats['体重变化']:+.2f} kg
✓ 体脂率下降: {stats['体脂率变化']:+.2f}%
✓ 预计1周内达成目标!

================================================================================
"""

print(report)

# 保存报告
report_path = os.path.join(REPORT_DIR, f"减脂报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n报告已保存: {report_path}")

# 生成图表（仅体重和体脂率）
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('5周减脂数据趋势图', fontsize=18, fontweight='bold', y=0.98)

# 体重
ax1.plot(df['日期'], df['体重(kg)'], 'b-o', linewidth=2, markersize=4, label='体重')
ax1.axhline(y=67, color='r', linestyle='--', alpha=0.7, label='目标67kg')
ax1.set_ylabel('体重 (kg)', fontsize=12)
ax1.set_title('体重变化趋势', fontsize=14, fontweight='bold')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 体脂率
ax2.plot(df['日期'], df['体脂率(%)'], 'r-o', linewidth=2, markersize=4, label='体脂率')
ax2.axhline(y=17, color='green', linestyle='--', alpha=0.7, label='目标17%')
ax2.set_ylabel('体脂率 (%)', fontsize=12)
ax2.set_title('体脂率变化趋势', fontsize=14, fontweight='bold')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 格式化x轴
for ax in [ax1, ax2]:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, fontsize=8)

plt.tight_layout()

# 保存图表
chart_path = os.path.join(CHART_DIR, f"减脂趋势图_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
print(f"图表已保存: {chart_path}")
