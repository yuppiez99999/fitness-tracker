# 健身监控 v7.0

基于市场主流健身软件（Keep / Fitbod / Hevy / Strong）特性优化的个人体脂体重监控 + 健身计划软件。

## 功能模块

- **📊 体测仪表盘** — 12 项体测指标 + 快速录入 + 历史记录
- **📈 趋势分析** — 7 日 EMA 平滑曲线 + 目标达标日预测 + 体成分饼图
- **🏋️ 动作示范库** — 38 个动作 GIF 动画 + 中文步骤教学 + 肌群信息
- **📅 训练计划** — 8 周增肌塑形计划 + 周历视图 + 点击动作看示范

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
├── 体脂体重监控_完整版.py          # 主程序入口
├── fitness_modules.py              # 核心模块
├── .venv/                          # 虚拟环境（不提交）
├── 体重体脂监控/                   # 训练计划与资源
│   ├── 8周增肌塑形计划.md
│   ├── exercises_gif/              # 动作示范 GIF
│   ├── exercises_matched.json
│   └── 体脂体重.txt                # 体测数据（示例）
└── README.md
```

## 数据说明

- 体测数据存储在 `体重体脂监控/体脂体重.txt`
- 支持 12 项指标：日期、体重、体脂率、肌肉量、内脏脂肪等级、基础代谢率、体水分率、骨量、BMI、骨骼肌率、腰围、臀围
- 目标体重默认 67.0 kg，目标体脂率默认 16.5%
- 变化值以“当前 - 初始”计算，降低会显示为负数

## 注意事项

- 本项目为个人健身工具，数据存储在本地
- 敏感个人信息文件已排除在版本控制之外
- 虚拟环境目录 `.venv` 不提交到仓库
