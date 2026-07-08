# -*- coding: utf-8 -*-
"""
Excel数据导入脚本 - 优化版
从体重与体脂率变化记录表.xlsx导入数据到体脂体重监控系统
"""
import sys
import os
import pandas as pd
from datetime import datetime

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def import_excel_data():
    """导入Excel数据"""
    print("=" * 80)
    print("📊 Excel数据导入工具 - 优化版".center(70))
    print("=" * 80)
    
    # 文件路径
    excel_path = os.path.join(os.path.dirname(current_dir), "体重与体脂率变化记录表.xlsx")
    data_file = os.path.join(current_dir, "体脂体重.txt")
    
    print(f"\n📂 读取文件: {excel_path}")
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_path)
        print(f"✅ 读取成功，共 {len(df)} 行数据")
        
        # 处理数据
        print(f"\n📋 开始导入...")
        
        # 创建DataFrame格式数据
        data_list = []
        for idx, row in df.iterrows():
            date_obj = row['日期']
            weight = row['体重(kg)']
            bodyfat = row['体脂率(%)']
            
            if pd.isna(date_obj) or pd.isna(weight):
                continue
            
            date_str = date_obj.strftime('%Y-%m-%d')
            weight = float(weight)
            bodyfat = float(bodyfat) if pd.notna(bodyfat) else None
            
            data_list.append({
                '日期': date_str,
                '体重(kg)': weight,
                '体脂率(%)': bodyfat
            })
            
            bf_display = f", 体脂率 {bodyfat}%" if bodyfat else ""
            print(f"  {idx+1:2d}. {date_str} - 体重 {weight:.2f}kg{bf_display}")
        
        print(f"\n📋 共 {len(data_list)} 条有效记录")
        
        # 创建DataFrame并保存为CSV
        result_df = pd.DataFrame(data_list)
        
        print(f"\n💾 保存数据到: {data_file}")
        result_df.to_csv(data_file, index=False, encoding='utf-8')
        print(f"✅ 数据保存成功！")
        
        # 显示统计
        print(f"\n" + "=" * 80)
        print("📊 导入统计".center(70))
        print("=" * 80)
        print(f"  📅 日期范围: {data_list[0]['日期']} ~ {data_list[-1]['日期']}")
        print(f"  ⚖️  体重范围: {min(r['体重(kg)'] for r in data_list):.2f} kg ~ {max(r['体重(kg)'] for r in data_list):.2f} kg")
        bodyfat_records = [r['体脂率(%)'] for r in data_list if r['体脂率(%)']]
        if bodyfat_records:
            print(f"  🔥 体脂率范围: {min(bodyfat_records):.1f}% ~ {max(bodyfat_records):.1f}%")
        print(f"  📋 总记录数: {len(data_list)} 条")
        print(f"  📉 体重变化: {data_list[-1]['体重(kg)'] - data_list[0]['体重(kg)']:+.2f} kg")
        print("=" * 80)
        
        print(f"\n💪 最新数据:")
        latest = data_list[-1]
        bf_display = f", 体脂率 {latest['体脂率(%)']}%" if latest['体脂率(%)'] else ""
        print(f"  📅 日期: {latest['日期']}")
        print(f"  ⚖️  体重: {latest['体重(kg)']:.2f} kg{bf_display}")
        
        print(f"\n✅ 导入完成！")
        print(f"\n💡 现在可以运行:")
        print(f"   • 体脂体重监控_GUI_改进版.py  (启动GUI界面)")
        print(f"   • test_训练计划.py           (测试训练计划功能)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import_excel_data()
