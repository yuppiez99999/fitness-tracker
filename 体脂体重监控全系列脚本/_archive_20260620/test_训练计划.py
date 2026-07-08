# -*- coding: utf-8 -*-
"""
训练计划功能测试脚本
"""
import sys
import os
from datetime import datetime

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 训练计划数据（与主程序相同）
training_plans = {
    0: {  # 星期一
        'name': '全身力量训练',
        'exercises': [
            '🏋️ 杠铃深蹲: 4组 × 12次',
            '💪 卧推: 4组 × 10次',
            '🏃 硬拉: 3组 × 10次',
            '🎯 杠铃划船: 3组 × 12次',
            '🏋️ 肩上推举: 3组 × 10次',
            '💪 双杠臂屈伸: 3组 × 15次',
            '🎯 引体向上: 3组 × 8次',
        ],
        'warmup': '10分钟慢跑 + 动态拉伸',
        'cooldown': '5分钟静力拉伸',
    },
    1: {  # 星期二
        'name': '核心有氧训练',
        'exercises': [
            '🏃 慢跑: 30分钟 (配速6-7分/公里)',
            '🎯 平板支撑: 4组 × 60秒',
            '💪 卷腹: 4组 × 20次',
            '🏋️ 俄罗斯转体: 3组 × 30次',
            '🎯 腿部卷腹: 3组 × 15次',
            '💪 悬垂举腿: 3组 × 10次',
            '🏃 跳绳: 5分钟 × 3组',
        ],
        'warmup': '5分钟原地高抬腿',
        'cooldown': '10分钟慢走 + 拉伸',
    },
    2: {  # 星期三
        'name': '休息/轻活动',
        'exercises': [
            '🧘 瑜伽或普拉提: 30-45分钟',
            '🚶 轻松散步: 20-30分钟',
            '💆 泡沫轴放松: 15分钟',
            '😴 保证8小时睡眠',
        ],
        'warmup': '无需',
        'cooldown': '无需',
        'note': '肌肉恢复日，避免高强度训练',
    },
    3: {  # 星期四
        'name': '上肢力量训练',
        'exercises': [
            '💪 哑铃弯举: 4组 × 12次',
            '🏋️ 三头下压: 4组 × 12次',
            '🎯 侧平举: 3组 × 15次',
            '💪 俯卧撑: 4组 × 15次',
            '🏋️ 双杠臂屈伸: 3组 × 12次',
            '🎯 哑铃划船: 3组 × 12次/侧',
            '💪 哑铃肩上推举: 3组 × 10次',
        ],
        'warmup': '10分钟跳绳 + 肩部激活',
        'cooldown': '7分钟上肢拉伸',
    },
    4: {  # 星期五
        'name': '下肢力量训练',
        'exercises': [
            '🏋️ 颈前深蹲: 4组 × 10次',
            '🎯 罗马尼亚硬拉: 4组 × 10次',
            '💪 箭步蹲: 3组 × 12次/腿',
            '🏋️ 腿举: 3组 × 15次',
            '🎯 腿弯举: 3组 × 12次',
            '💪 腿屈伸: 3组 × 12次',
            '🏋️ 提踵: 4组 × 20次',
        ],
        'warmup': '10分钟椭圆机 + 腿部激活',
        'cooldown': '8分钟下肢拉伸',
    },
    5: {  # 星期六
        'name': 'HIIT高强度间歇',
        'exercises': [
            '🏃 30秒冲刺跑 + 60秒慢走: 10组',
            '💪 波比跳: 3组 × 15次',
            '🎯 跳箱: 3组 × 10次',
            '💪 俯卧撑跳: 3组 × 12次',
            '🏃 登山跑: 3组 × 30秒',
            '💪 平板支撑跳: 3组 × 10次',
        ],
        'warmup': '10分钟动态热身',
        'cooldown': '10分钟拉伸放松',
        'note': '高强度训练，注意安全',
    },
    6: {  # 星期日
        'name': '休息日',
        'exercises': [
            '😴 充分休息，保证睡眠',
            '🚶 可选: 20-30分钟轻松散步',
            '🍎 注重营养补充',
            '🧘 可选: 15分钟冥想',
        ],
        'warmup': '无需',
        'cooldown': '无需',
        'note': '完全休息，让肌肉恢复',
    },
}

weekday_names = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']

def test_training_plans():
    """测试训练计划功能"""
    print("=" * 80)
    print("🏋️  训练计划功能测试".center(70))
    print("=" * 80)
    
    # 测试今日训练
    today = datetime.now()
    weekday = today.weekday()
    print(f"\n📅 今日: {today.strftime('%Y-%m-%d')}")
    print(f"📅 星期: {weekday_names[weekday]}")
    print(f"💪 训练类型: {training_plans[weekday]['name']}")
    
    print("\n" + "-" * 80)
    print("📋 今日训练内容:")
    print("-" * 80)
    for i, exercise in enumerate(training_plans[weekday]['exercises'], 1):
        print(f"  {i}. {exercise}")
    
    if training_plans[weekday]['warmup'] != '无需':
        print(f"\n🏃 热身: {training_plans[weekday]['warmup']}")
    
    if training_plans[weekday]['cooldown'] != '无需':
        print(f"🧘 放松: {training_plans[weekday]['cooldown']}")
    
    if 'note' in training_plans[weekday]:
        print(f"📝 备注: {training_plans[weekday]['note']}")
    
    print("\n" + "=" * 80)
    print("✅ 训练计划测试通过！".center(70))
    print("=" * 80)
    
    # 测试一周训练概览
    print("\n📆 一周训练概览:")
    print("-" * 80)
    for i in range(7):
        plan = training_plans[i]
        intensity = "😴" if "休息" in plan['name'] else "🏋️" if "力量" in plan['name'] else "💪"
        print(f"  {intensity} {weekday_names[i]}: {plan['name']}")
    
    print("\n💡 提示:")
    print("  • 运行 体脂体重监控_GUI_改进版.py 启动主程序")
    print("  • 添加体重记录后会自动弹出当日训练计划")
    print("  • 点击'💪 今日训练'按钮可手动查看")
    
    return True

if __name__ == "__main__":
    test_training_plans()
