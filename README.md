# 健身监控 v9.0

基于市场主流健身软件（Keep / Fitbod / Hevy / Strong）特性优化 + **Lzheng-fitness 知识库深度集成**的个人体脂体重监控 + 健身计划软件。PySide6 重构版，提供体测管理、趋势分析、动作示范、训练计划、营养指导与 **AI 教练**六大模块。

> **v9.0 关键升级**：深度集成 [Lzheng-fitness](https://github.com/yuppiez99999/Lzheng-fitness) 知识库（Schoenfeld/Helms/Aragon/Nuckols 蒸馏模块），新增 **AI 教练**页面，实现 P0-L3 分层评估、8-12 周动态力量周期化、训练复盘 + 渐进超负荷、停训接回三档方案、最低执行版本（30/20/10 分钟）五大增肌优化能力。支持 PyInstaller 一键封装为独立 .exe，免安装 Python 直接运行。

## 功能模块

- **📊 体测仪表盘** — 12 项体测指标 + 快速录入 + 历史记录
- **📈 趋势分析** — 7 日 EMA 平滑曲线 + 目标达标日预测 + 体成分饼图
- **🏋️ 动作示范库** — 51 个动作 GIF 动画 + 中文步骤教学 + 肌群信息
- **📅 训练计划** — 22 周宽背窄腰塑形 v2.1（三阶段周期化，6 练 1 休）+ 点击动作看示范
- **🍽 饮食与补剂** — 三阶段营养方案 + 五餐明细 + 补剂表 + 饮水指南
- **� AI 教练** — 基于 Lzheng-fitness 知识库的增肌规划系统（5 个子功能）

## AI 教练模块（v9.0 新增）

集成 Lzheng-fitness 的 6 位顶级训练专家知识（Alan Aragon、Brad Schoenfeld、Brukner & Khan、Dan John、Eric Helms、Greg Nuckols），纯 Python 实现，离线运行无需 AI 对话。

| 子功能 | 说明 |
|:------|:-----|
| 📋 建档与分层 | P0-L3 四级训练阶段评估（启动/动作稳定/周管理/阶段进步） |
| 📅 力量周期 | 8-12 周动态周期生成（积累→强度→实现→减量），含顶组+回退组 |
| 📝 训练复盘 | 单次训练复盘 + 渐进超负荷决策（双重渐进：先加次再加重） |
| ↩️ 停训接回 | 三档接回方案（正常/降级/最低）+ 未来 7 天安排 |
| ⏱ 短版训练 | 30/20/10 分钟最低执行版本，保留主线，不补课不加倍 |

## 技术栈

- PySide6 + matplotlib + pandas + numpy + Pillow
- PyInstaller（封装为免安装 .exe）
- 数据源：exercises-dataset（Git 子模块，GitHub: yuppiez99999/exercises-dataset）
- 知识库：Lzheng-fitness（Git 子模块，GitHub: yuppiez99999/Lzheng-fitness）
- 舆情分析：BettaFish / MiroFish（Git 子模块，GitHub: yuppiez99999/MiroFish）

## 环境要求

- Python 3.8+
- 建议使用虚拟环境运行，避免全局包冲突

```bash
# 克隆仓库（含子模块）
git clone --recurse-submodules https://github.com/yuppiez99999/fitness-tracker.git
cd fitness-tracker

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 安装依赖
pip install PySide6 matplotlib pandas numpy Pillow

# 直接运行
python 体脂体重监控_完整版.py
```

也可双击 `启动体脂体重监控.bat` 一键启动（Windows）。

### 封装为独立 .exe

```bash
pip install pyinstaller
python -m PyInstaller 健身监控.spec --noconfirm --clean
# 产物: dist\健身监控v9.0\健身监控v9.0.exe
```

将 `dist\健身监控v9.0\` 文件夹复制到任意 Windows 电脑，双击 `健身监控v9.0.exe` 即可运行，无需安装 Python。

## 项目结构

```
06_个人辅助工具/
├── 体脂体重监控_完整版.py           # 主程序入口（PySide6 GUI，6 个 Tab）
├── fitness_modules.py               # 核心模块（模型/页面/解析器/教程/AI教练页面）
├── ai_coach_engine.py               # AI 教练引擎（P0-L3/周期/复盘/接回/短版）
├── 健身监控.spec                     # PyInstaller 打包配置
├── fitness_icon.ico                 # 应用图标
├── 启动体脂体重监控.bat             # Windows 一键启动脚本
├── Lzheng-fitness/                  # 知识库子模块（Schoenfeld/Helms 等 6 专家）
├── generate_report.py               # 报告生成工具
├── 补充缺失数据.py                   # 体测数据补全脚本
├── .venv/                           # 虚拟环境（不提交）
├── BettaFish/                       # 舆情分析子模块（Git 子模块）
├── exercises-dataset/               # 动作数据集子模块（Git 子模块）
├── dist/                            # 封装产物（仅 exe 本体随仓库分发）
│   └── 健身监控v9.0/
│       └── 健身监控v9.0.exe          # PyInstaller 封装的可执行程序
├── 体重体脂监控/                     # 训练计划与资源
│   ├── 8周增肌塑形计划.md
│   ├── 12月底塑形冲刺计划_v2.0_宽背窄腰.md
│   ├── 12月底塑形冲刺计划_v2.1_宽背窄腰_执行版.md   # 当前生效计划
│   ├── ai_coach/                    # AI 教练数据（本地个人数据，不提交）
│   ├── exercises_gif/               # 51 个动作示范 GIF
│   ├── exercises_matched.json       # 动作与 GIF 映射
│   ├── match_exercises.py           # 动作匹配脚本
│   ├── 报告/                         # 体测报告 TXT（本地个人数据，不提交）
│   └── 图表/                         # 趋势图 PNG（本地个人数据，不提交）
└── README.md
```

## 训练计划 v2.1 亮点

基于个人实测数据制定的 22 周塑形计划（示例：体脂从 16.9% 降至 12.5–13.5%），可按自身情况调整热量与训练量。

| 维度 | v2.0 | v2.1 优化 |
|:-----|:-----|:----------|
| 热量缺口 | 标称 150 kcal | 训练日 2300 / 休息日 2100 kcal |
| 背周总量 | 34 组 | 22–26 组（周一 12 + 周四 10–12） |
| 俯身划船 | 周四主项 | T 杠划船 / 胸支撑划船（护腰） |
| 阿诺德推举 | 肩日主项 | 坐姿哑铃肩推（护肩袖） |
| 空腹有氧 | Phase 2 启动 | Phase 1 完全不做，Phase 2 最多 2 次 |
| 补剂 | 堆叠 9 种 | 精简至 5 必需 + 3 建议 |
| 真空腹 | 60 秒 ×5 | 30→45→60 秒递进 |

训练日程（6 练 1 休）：背（宽）→ 胸（上胸优先）→ 腿（四头为主）→ 背（划船）→ 肩 + 臂 → 全身 HIIT + 冲刺 → 完全休息。

## AI 教练知识来源

Lzheng-fitness 知识库包含 6 个来源限定专家模块：

| 专家 | 领域 | 应用场景 |
|:-----|:-----|:---------|
| Brad Schoenfeld | 肌肥大科学 | 训练量、频率、RIR 设置 |
| Eric Helms | 训练金字塔 | 周期结构、阶段过渡 |
| Alan Aragon | 营养策略 | 热量缺口、宏量配比 |
| Greg Nuckols | 力量停滞 | 突破平台期、变量实验 |
| Dan John | 基础训练 | 目标脱节时回到基础 |
| Brukner & Khan | 临床运动 | 安全筛查、疼痛分流 |

## 数据说明

- 体测数据支持 12 项指标：日期、体重、体脂率、肌肉量、内脏脂肪等级、基础代谢率、体水分率、骨量、BMI、骨骼肌率、腰围、臀围
- AI 教练数据存储在 `体重体脂监控/ai_coach/`（建档、周期 JSON、复盘记录、周期 MD），该目录为本地个人数据，不随仓库分发
- 目标体重 / 目标体脂率可在建档时自定义
- 变化值以"当前 - 初始"计算，降低会显示为负数

## 注意事项

- 本项目为个人健身工具，数据存储在本地
- 敏感个人信息文件已排除在版本控制之外
- 虚拟环境目录 `.venv` 不提交到仓库
- 训练计划基于个人实测数据制定，参考前请结合自身体检与训练基础
- AI 教练提供一般训练规划支持，不作医疗诊断或康复建议
