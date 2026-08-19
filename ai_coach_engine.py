# -*- coding: utf-8 -*-
"""
AI 教练核心引擎 v1.0 — 基于 Lzheng-fitness 知识库的本地增肌规划系统

提取 Lzheng-fitness 的 P0-L3 分层、力量周期化、训练复盘、停训接回与最低执行版本规则，
用纯 Python 实现，无需 AI 对话或网络依赖。

知识来源: Lzheng-fitness/knowledge/ (Schoenfeld/Helms/Aragon/Nuckols 蒸馏模块)
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COACH_DIR = os.path.join(BASE_DIR, '体重体脂监控', 'ai_coach')
os.makedirs(COACH_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════
# 一、P0-L3 分层评估
# ═══════════════════════════════════════════════════════════

LEVEL_DESC = {
    'P0': '启动/回归期 — 首要目标: 安全、可重复、建立基准',
    'L1': '动作稳定期 — 可逐次或隔次推进，线性渐进',
    'L2': '周管理期 — 按周管理训练量、强度和恢复',
    'L3': '阶段进步期 — 按月或阶段出现进步，需高专项性和疲劳管理',
}


@dataclass
class AthleteProfile:
    """运动员建档"""
    name: str = ''
    age: int = 0
    height_cm: float = 0.0
    weight_kg: float = 0.0
    body_fat_pct: float = 0.0
    training_years: float = 0.0
    weekly_sessions: int = 4
    session_minutes: int = 60
    equipment: List[str] = field(default_factory=lambda: ['杠铃', '哑铃', '器械'])
    goal: str = '增肌'  # 增肌/减脂/力量/综合
    limitations: List[str] = field(default_factory=list)
    # 动作熟练度: {动作名: {'level': 'P0/L1/L2/L3', 'recent_1rm': float, 'quality': 1-5}}
    movement_proficiency: Dict[str, Dict] = field(default_factory=dict)


def assess_level(profile: AthleteProfile, movement: str) -> str:
    """评估单个动作的 P0-L3 等级

    依据: 近期可比记录、动作稳定性、恢复与推进速度
    """
    prof = profile.movement_proficiency.get(movement, {})
    quality = prof.get('quality', 0)
    has_record = bool(prof.get('recent_1rm'))
    years = profile.training_years

    if not has_record or quality < 2:
        return 'P0'
    if quality < 4 or years < 1:
        return 'L1'
    if years < 3 or quality < 5:
        return 'L2'
    return 'L3'


def assess_overall_level(profile: AthleteProfile) -> str:
    """评估整体训练等级"""
    if not profile.movement_proficiency:
        return 'P0' if profile.training_years < 0.5 else 'L1'
    levels = [assess_level(profile, m) for m in profile.movement_proficiency]
    order = ['P0', 'L1', 'L2', 'L3']
    idxs = [order.index(l) for l in levels]
    avg = sum(idxs) / len(idxs)
    return order[min(int(avg), 3)]


# ═══════════════════════════════════════════════════════════
# 二、力量周期生成 (8-12 周)
# ═══════════════════════════════════════════════════════════

PHASES = ['积累', '强度', '实现', '减量']


@dataclass
class WorkoutSet:
    """训练组"""
    weight: float
    reps: int
    sets: int
    rpe_start: float = 6.0
    rpe_end: float = 7.0
    set_type: str = '正式组'  # 热身组/顶组/回退组/正式组


@dataclass
class WorkoutDay:
    """训练日"""
    week: int
    phase: str
    day_name: str
    movement: str
    sets: List[WorkoutSet] = field(default_factory=list)
    notes: str = ''
    short_version_30: str = ''
    short_version_20: str = ''
    short_version_10: str = ''


@dataclass
class StrengthCycle:
    """力量周期 (8-12 周)"""
    movement: str
    target_1rm: float
    current_1rm: float
    weeks: int
    start_date: str
    days: List[WorkoutDay] = field(default_factory=list)
    phase_distribution: Dict[str, int] = field(default_factory=dict)


def determine_cycle_length(weekly_exposures: int, goal: str = '力量') -> int:
    """确定周期长度: 8/10/12 周

    - 8 周: 目标单一、动作频率较高、只需一次积累与转化
    - 10 周: 一般力量发展，兼顾积累、强度与验证
    - 12 周: 训练频率低、需要更慢推进，或需要完整阶段
    """
    if weekly_exposures >= 3:
        return 8
    elif weekly_exposures == 2:
        return 10 if goal == '力量' else 8
    else:
        return 12


def distribute_phases(weeks: int) -> Dict[str, int]:
    """分配各阶段周数: 积累→强度→实现→减量"""
    if weeks == 8:
        return {'积累': 3, '强度': 3, '实现': 1, '减量': 1}
    elif weeks == 10:
        return {'积累': 4, '强度': 3, '实现': 2, '减量': 1}
    else:  # 12
        return {'积累': 4, '强度': 4, '实现': 2, '减量': 2}


def estimate_1rm(weight: float, reps: int, rpe: float = 7.0) -> float:
    """Epley 公式 + RPE 调整估算 1RM"""
    if reps <= 1:
        return weight
    rpe_adj = 1.0 + (rpe - 7.0) * 0.03
    return weight * (1 + reps / 30.0) * rpe_adj


def calc_target_weight(estimated_1rm: float, intensity_pct: float, reps: int) -> float:
    """根据目标强度百分比计算训练重量"""
    raw = estimated_1rm * intensity_pct
    return round(raw * 2) / 2  # 取 0.5kg 精度


PHASE_INTENSITY = {
    '积累': {'pct': 0.70, 'reps': 8, 'sets': 4, 'rpe': (6, 7)},
    '强度': {'pct': 0.80, 'reps': 5, 'sets': 4, 'rpe': (7, 8)},
    '实现': {'pct': 0.88, 'reps': 3, 'sets': 3, 'rpe': (8, 9)},
    '减量': {'pct': 0.60, 'reps': 5, 'sets': 3, 'rpe': (5, 6)},
}


def generate_strength_cycle(
    movement: str,
    current_1rm: float,
    target_1rm: float,
    weekly_exposures: int = 2,
    start_date: Optional[str] = None,
) -> StrengthCycle:
    """生成完整力量周期"""
    weeks = determine_cycle_length(weekly_exposures)
    dist = distribute_phases(weeks)
    if start_date is None:
        start_date = datetime.now().strftime('%Y-%m-%d')

    cycle = StrengthCycle(
        movement=movement,
        target_1rm=target_1rm,
        current_1rm=current_1rm,
        weeks=weeks,
        start_date=start_date,
        phase_distribution=dist,
    )

    week = 1
    for phase, n_weeks in dist.items():
        cfg = PHASE_INTENSITY[phase]
        for _ in range(n_weeks):
            progress = (week - 1) / max(weeks - 1, 1)
            cur_1rm = current_1rm + (target_1rm - current_1rm) * progress * 0.7
            pct = cfg['pct'] + progress * 0.05
            w = calc_target_weight(cur_1rm, pct, cfg['reps'])

            top_set = WorkoutSet(
                weight=w, reps=cfg['reps'], sets=1,
                rpe_start=cfg['rpe'][0], rpe_end=cfg['rpe'][1],
                set_type='顶组'
            )
            backoff_w = round(w * 0.90 * 2) / 2
            backoff = WorkoutSet(
                weight=backoff_w, reps=cfg['reps'] + 2, sets=cfg['sets'] - 1,
                rpe_start=cfg['rpe'][0], rpe_end=cfg['rpe'][1],
                set_type='回退组'
            )

            day = WorkoutDay(
                week=week, phase=phase, day_name=f'第{week}周',
                movement=movement, sets=[top_set, backoff],
                notes=f'{phase}阶段 — {PHASE_DESC[phase]}',
            )
            day.short_version_30 = f'{movement} {w}kg {cfg["sets"]}×{cfg["reps"]} (保留顶组+1组回退)'
            day.short_version_20 = f'{movement} {w}kg 2×{cfg["reps"]} (仅顶组+1组)'
            day.short_version_10 = f'{movement} {w}kg 1×{cfg["reps"]} (仅顶组)'
            cycle.days.append(day)
            week += 1

    return cycle


PHASE_DESC = {
    '积累': '建立可恢复训练量和动作质量',
    '强度': '提高较高负荷暴露，通常减少次数或部分训练量',
    '实现': '提高专项性，避免额外疲劳掩盖表现',
    '减量': '显著降低疲劳，再测试目标或建立下一周期基准',
}


# ═══════════════════════════════════════════════════════════
# 三、训练复盘 + 渐进超负荷
# ═══════════════════════════════════════════════════════════

@dataclass
class TrainingLog:
    """训练记录"""
    date: str
    movement: str
    weight: float
    reps: int
    sets: int
    rpe: float
    completed: bool = True
    notes: str = ''


@dataclass
class ReviewResult:
    """复盘结果"""
    judgment: str  # 完成/部分完成/偏轻/合适/偏重/需要观察
    key_findings: List[str]
    next_prescription: Dict[str, Any]
    progression_type: str  # 加重/加次/加组/维持/减量


def review_training(log: TrainingLog, prev_log: Optional[TrainingLog] = None) -> ReviewResult:
    """单次训练复盘 + 渐进超负荷决策

    规则:
    - 一次只优先改变重量、次数或组数中的一个主要变量
    - 双重渐进: 先把次数提高到范围上限，再增加一个最小重量单位
    - 主要正式组通常不超过 RPE 9
    - 连续两次同重量掉次数/RPE 上升约一级 → 怀疑周期结构
    """
    findings = []
    next_rx = {'movement': log.movement}

    if not log.completed:
        return ReviewResult(
            judgment='部分完成',
            key_findings=['未完成全部计划组次', '建议下次按原安排继续，不补课'],
            next_prescription={**next_rx, 'weight': log.weight, 'reps': log.reps, 'sets': log.sets, 'rpe': log.rpe},
            progression_type='维持',
        )

    if log.rpe >= 9.5:
        judgment = '偏重'
        findings.append(f'RPE {log.rpe} 过高，超过 9.5')
        findings.append('建议下次维持重量，关注动作质量')
        next_rx.update({'weight': log.weight, 'reps': log.reps, 'sets': log.sets, 'rpe': log.rpe - 0.5})
        prog = '维持'
    elif log.rpe <= 6.0:
        judgment = '偏轻'
        findings.append(f'RPE {log.rpe} 偏低，还有较多余力')
        if log.reps < 12:
            findings.append('双重渐进: 先加次数到范围上限')
            next_rx.update({'weight': log.weight, 'reps': log.reps + 1, 'sets': log.sets, 'rpe': log.rpe + 0.5})
            prog = '加次'
        else:
            findings.append('次数已达上限，加重 2.5kg')
            next_rx.update({'weight': log.weight + 2.5, 'reps': log.reps - 2, 'sets': log.sets, 'rpe': 7.0})
            prog = '加重'
    else:
        judgment = '合适'
        findings.append(f'RPE {log.rpe} 在合理区间 (7-9)')
        if prev_log and prev_log.weight == log.weight and prev_log.reps == log.reps:
            if log.rpe <= prev_log.rpe - 0.5:
                findings.append('同重量同次数 RPE 下降，可加重')
                next_rx.update({'weight': log.weight + 2.5, 'reps': log.reps, 'sets': log.sets, 'rpe': 7.5})
                prog = '加重'
            else:
                findings.append('维持当前处方，巩固适应')
                next_rx.update({'weight': log.weight, 'reps': log.reps, 'sets': log.sets, 'rpe': log.rpe})
                prog = '维持'
        else:
            if log.reps < 10:
                next_rx.update({'weight': log.weight, 'reps': log.reps + 1, 'sets': log.sets, 'rpe': log.rpe + 0.5})
                prog = '加次'
                findings.append('双重渐进: 加 1 次')
            else:
                next_rx.update({'weight': log.weight + 2.5, 'reps': log.reps - 2, 'sets': log.sets, 'rpe': 7.5})
                prog = '加重'
                findings.append('次数达上限，加重 2.5kg')

    return ReviewResult(judgment=judgment, key_findings=findings,
                        next_prescription=next_rx, progression_type=prog)


# ═══════════════════════════════════════════════════════════
# 四、停训接回 (三档方案)
# ═══════════════════════════════════════════════════════════

@dataclass
class ReturnPlan:
    """停训接回方案"""
    days_off: int
    permission: str  # 正常接回/降级接回/最低任务/暂停
    normal_version: str
    degraded_version: str
    minimal_version: str
    next_7_days: List[str]


def generate_return_plan(days_off: int, last_weight: float = 0.0,
                          movement: str = '主项') -> ReturnPlan:
    """生成停训接回三档方案

    规则:
    - 1-7 天: 正常接回 (原重量 90%)
    - 8-21 天: 降级接回 (原重量 80%)
    - 22-56 天: 最低任务 (原重量 70%)
    - >56 天: 暂停，建议重新建档
    """
    if days_off <= 0:
        return ReturnPlan(
            days_off=days_off, permission='正常接回',
            normal_version='按原计划继续',
            degraded_version='—', minimal_version='—',
            next_7_days=['按当前周期继续训练'],
        )

    if days_off <= 7:
        perm = '正常接回'
        normal_w = last_weight * 0.90
        degraded_w = last_weight * 0.85
        minimal_w = last_weight * 0.80
    elif days_off <= 21:
        perm = '降级接回'
        normal_w = last_weight * 0.85
        degraded_w = last_weight * 0.75
        minimal_w = last_weight * 0.70
    elif days_off <= 56:
        perm = '最低任务'
        normal_w = last_weight * 0.75
        degraded_w = last_weight * 0.65
        minimal_w = last_weight * 0.60
    else:
        return ReturnPlan(
            days_off=days_off, permission='暂停',
            normal_version='建议重新建档',
            degraded_version='从 P0 阶段重新开始',
            minimal_version='先完成动作学习',
            next_7_days=['重新建档', '动作重量校准', '生成新计划'],
        )

    def fmt(w):
        return f'{round(w*2)/2}kg' if w > 0 else '自重'

    plan = ReturnPlan(
        days_off=days_off, permission=perm,
        normal_version=f'{movement} {fmt(normal_w)} 3×8 @7 (正常版)',
        degraded_version=f'{movement} {fmt(degraded_w)} 3×10 @6 (降级版)',
        minimal_version=f'{movement} {fmt(minimal_w)} 2×12 @5 (最低版)',
        next_7_days=[
            f'第1天: {fmt(degraded_w)} 3×10 (找回感觉)',
            f'第3天: {fmt(normal_w)} 4×8 (恢复正常)',
            f'第5天: {fmt(normal_w)} 4×6 (接近原强度)',
            '第7天: 评估恢复，决定是否回到原周期',
        ],
    )
    return plan


# ═══════════════════════════════════════════════════════════
# 五、最低执行版本 (30/20/10 分钟)
# ═══════════════════════════════════════════════════════════

def generate_short_version(workout: WorkoutDay, minutes: int) -> str:
    """生成最低执行版本

    规则: 短版优先保留当天主线，不补课、不加倍训练、不用惩罚性有氧
    """
    if minutes >= 30:
        return workout.short_version_30 or f'{workout.movement} 主项 3组 (保留顶组+1组回退)'
    elif minutes >= 20:
        return workout.short_version_20 or f'{workout.movement} 主项 2组 (仅顶组+1组)'
    else:
        return workout.short_version_10 or f'{workout.movement} 主项 1组 (仅顶组)'


# ═══════════════════════════════════════════════════════════
# 六、数据持久化
# ═══════════════════════════════════════════════════════════

def save_profile(profile: AthleteProfile) -> str:
    path = os.path.join(COACH_DIR, 'profile.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
    return path


def load_profile() -> Optional[AthleteProfile]:
    path = os.path.join(COACH_DIR, 'profile.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return AthleteProfile(**data)


def save_cycle(cycle: StrengthCycle) -> str:
    path = os.path.join(COACH_DIR, f'cycle_{cycle.movement}_{cycle.start_date}.json')
    data = {
        'movement': cycle.movement, 'target_1rm': cycle.target_1rm,
        'current_1rm': cycle.current_1rm, 'weeks': cycle.weeks,
        'start_date': cycle.start_date, 'phase_distribution': cycle.phase_distribution,
        'days': [
            {
                'week': d.week, 'phase': d.phase, 'day_name': d.day_name,
                'movement': d.movement, 'notes': d.notes,
                'sets': [asdict(s) for s in d.sets],
                'short_30': d.short_version_30, 'short_20': d.short_version_20,
                'short_10': d.short_version_10,
            } for d in cycle.days
        ],
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def save_review(log: TrainingLog, result: ReviewResult) -> str:
    path = os.path.join(COACH_DIR, 'reviews.json')
    reviews = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
    reviews.append({
        'log': asdict(log),
        'judgment': result.judgment,
        'key_findings': result.key_findings,
        'next_prescription': result.next_prescription,
        'progression_type': result.progression_type,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
    })
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    return path


def load_reviews() -> List[Dict]:
    path = os.path.join(COACH_DIR, 'reviews.json')
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════
# 七、周期导出为 Markdown (供 fitness-tracker 训练计划页读取)
# ═══════════════════════════════════════════════════════════

def export_cycle_to_markdown(cycle: StrengthCycle) -> str:
    """导出周期为 Markdown 格式"""
    lines = [
        f'# {cycle.movement} 力量周期 — {cycle.weeks}周',
        f'> 起始日期: {cycle.start_date}',
        f'> 当前 1RM: {cycle.current_1rm}kg → 目标 1RM: {cycle.target_1rm}kg',
        f'> 阶段分布: {", ".join(f"{k}{v}周" for k, v in cycle.phase_distribution.items())}',
        '',
        '## 周期结构',
        '',
    ]
    for phase, n in cycle.phase_distribution.items():
        lines.append(f'- **{phase}** ({n}周): {PHASE_DESC.get(phase, "")}')
    lines.extend(['', '## 每周训练安排', ''])
    for d in cycle.days:
        lines.append(f'### 第{d.week}周 — {d.phase}阶段')
        lines.append(f'{d.notes}')
        lines.append('')
        lines.append('| 组类型 | 重量 | 组×次 | RPE |')
        lines.append('|:------|:-----|:------|:----|')
        for s in d.sets:
            lines.append(f'| {s.set_type} | {s.weight}kg | {s.sets}×{s.reps} | {s.rpe_start}→{s.rpe_end} |')
        lines.extend([
            '',
            '短版:',
            f'- 30分钟: {d.short_version_30}',
            f'- 20分钟: {d.short_version_20}',
            f'- 10分钟: {d.short_version_10}',
            '',
        ])
    path = os.path.join(COACH_DIR, f'周期_{cycle.movement}_{cycle.start_date}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return path