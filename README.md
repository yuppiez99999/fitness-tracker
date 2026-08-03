# 健身监控 v8.0

基于市场主流健身软件（Keep / Fitbod / Hevy / Strong）特性优化的个人体脂体重监控 + 健身计划软件。PySide6 重构版，提供完整的体测管理、趋势分析、动作示范、训练计划与营养指导五大模块。

## 功能模块

- **📊 体测仪表盘** — 12 项体测指标 + 快速录入 + 历史记录
- **📈 趋势分析** — 7 日 EMA 平滑曲线 + 目标达标日预测 + 体成分饼图
- **🏋️ 动作示范库** — 50 个动作 GIF 动画 + 中文步骤教学 + 肌群信息
- **📅 训练计划** — 20 周塑形冲刺（三阶段周期化）+ 12 月底冲刺 + 点击动作看示范
- **🍽 饮食与补剂** — 三阶段营养方案 + 五餐明细 + 补剂表 + 饮水指南

## 技术栈

- PySide6 + matplotlib + pandas + Pillow
- 数据源：exercises-dataset（GitHub: yuppiez99999/exercises-dataset）

## 环境要求

- Python 3.8+
- 建议使用虚拟环境运行，避免全局包冲突

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell:
.venv\Scripts\Activate.ps1

# 安装依赖
pip install PySide6 matplotlib pandas Pillow

# 运行
python 体脂体重监控_完整版.py
```

## 项目结构

```
06_个人辅助工具/
├── 体脂体重监控_完整版.py           # 主程序入口（PySide6 GUI）
├── fitness_modules.py               # 核心模块（模型/页面/解析器）
├── generate_report.py               # 报告生成工具
├── 补充缺失数据.py                   # 体测数据补全脚本
├── .venv/                           # 虚拟环境（不提交）
├── 体重体脂监控/                     # 训练计划与资源
│   ├── 8周增肌塑形计划.md
│   ├── 12月底塑形冲刺计划.md
│   ├── exercises_gif/               # 50 个动作示范 GIF
│   ├── exercises_matched.json       # 动作与 GIF 映射
│   ├── 报告/                         # 体测报告 TXT
│   └── 图表/                         # 趋势图 PNG
└── README.md
```

## 数据说明

- 体测数据支持 12 项指标：日期、体重、体脂率、肌肉量、内脏脂肪等级、基础代谢率、体水分率、骨量、BMI、骨骼肌率、腰围、臀围
- 目标体重默认 67.0 kg，目标体脂率默认 16.5%
- 变化值以"当前 - 初始"计算，降低会显示为负数

## 注意事项

- 本项目为个人健身工具，数据存储在本地
- 敏感个人信息文件已排除在版本控制之外
- 虚拟环境目录 `.venv` 不提交到仓库
