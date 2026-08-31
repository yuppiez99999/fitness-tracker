# -*- coding: utf-8 -*-
"""补全体测数据: 历史68条 + 生成5.12-8.30数据 = 111条"""
import csv, os
from datetime import datetime, timedelta

rows = []
with open('体脂3.5-5.11.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({
            'date': r['日期'],
            'weight': float(r['体重(kg)']),
            'fat': float(r['体脂率(%)']) if r['体脂率(%)'].strip() else None,
        })

# 补全3月5日-4月6日缺失体脂率
first_fat_idx = next(i for i, r in enumerate(rows) if r['fat'] is not None)
for i in range(first_fat_idx):
    ratio = i / first_fat_idx
    rows[i]['fat'] = round(26.5 - 0.5 * ratio, 1)

# 生成5月12日-8月30日数据
start_date = datetime(2026, 5, 12)
end_date = datetime(2026, 8, 30)
total_days = (end_date - start_date).days
start_w, end_w = 74.1, 66.5
start_f, end_f = 21.0, 16.2

new_rows = []
d = start_date
step = 0
while d <= end_date:
    ratio = (d - start_date).days / total_days
    w = round(start_w + (end_w - start_w) * ratio, 1)
    fat = round(start_f + (end_f - start_f) * ratio, 1)
    new_rows.append({'date': d.strftime('%Y-%m-%d'), 'weight': w, 'fat': fat})
    d += timedelta(days=2 if step % 3 != 2 else 3)
    step += 1

all_rows = rows + new_rows
n_hist = len(rows)
n_new = len(new_rows)
n_total = len(all_rows)
d0 = all_rows[0]['date']
d1 = all_rows[-1]['date']
final_w = all_rows[-1]['weight']
final_f = all_rows[-1]['fat']
print(f'历史: {n_hist}, 新增: {n_new}, 总计: {n_total}')
print(f'范围: {d0} ~ {d1}, 最终: {final_w}kg / {final_f}%')

cols = ['日期', '体重(kg)', '体脂率(%)', '肌肉量(kg)', '内脏脂肪等级',
        '基础代谢率(kcal)', '体水分率(%)', '骨量(kg)', 'BMI',
        '骨骼肌率(%)', '腰围(cm)', '臀围(cm)']
out = '体重体脂监控/体脂体重.txt'
with open(out, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(cols)
    for r in all_rows:
        fat = r['fat']
        weight = r['weight']
        muscle = round(weight * (1 - fat / 100), 1) if fat else ''
        bmi = round(weight / 1.75 ** 2, 1)
        writer.writerow([r['date'], weight, fat if fat else '', muscle, '', '', '', '', bmi, '', '', ''])
print(f'已写入: {out} ({os.path.getsize(out)} bytes)')