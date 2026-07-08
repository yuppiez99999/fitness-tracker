# -*- coding: utf-8 -*-
"""
简单Excel读取测试
"""
import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(os.path.dirname(current_dir), "体重与体脂率变化记录表.xlsx")

print("=" * 80)
print("📊 Excel文件预览".center(70))
print("=" * 80)
print(f"\n📂 文件路径: {excel_path}")

try:
    # 读取Excel文件
    df = pd.read_excel(excel_path)
    print(f"\n✅ 文件读取成功!")
    print(f"\n📋 形状: {df.shape[0]} 行 × {df.shape[1]} 列")
    print(f"\n📑 列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    print(f"\n📊 完整数据:")
    print("-" * 80)
    print(df.to_string())
    print("-" * 80)
    
    print(f"\n💡 数据类型:")
    print(df.dtypes)
    
    # 保存为CSV方便查看
    csv_path = os.path.join(current_dir, "excel_data_preview.csv")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"\n✅ 预览已保存为: {csv_path}")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
