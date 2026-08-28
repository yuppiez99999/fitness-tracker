# -*- coding: utf-8 -*-
"""
fitness_modules — v7.0 模块化兼容层 (Compatibility Shim)
原单文件实现已拆分到 fitness_pkg/ 包。本文件仅做 re-export,
保证现有调用方 (体脂体重监控_完整版.py 等) 无需改动即可继续工作。

如需直接引用, 推荐改为:  from fitness_pkg import BodyDataModel, ...
"""
import matplotlib
matplotlib.use('QtAgg')  # 必须在导入 pyplot 之前设置后端 (原 fitness_modules.py 顶部设置)

from fitness_pkg import (
    COLORS, MUSCLE_EMOJI, VACUUM_TUTORIAL, FLOW_TUTORIAL,
    TRAINING_SCHEDULE, PHASE_INFO, BODY_COLUMNS, DATA_FILE,
    BodyDataModel, ExerciseLibrary, TrainingPlanParser, NutritionParser,
    ExerciseDetailDialog, DashboardPage, TrendChartPage,
    ExerciseLibraryPage, TrainingPlanPage, NutritionPage,
    AICoachPage, AI_COACH_AVAILABLE,
)

__all__ = [
    'COLORS', 'MUSCLE_EMOJI', 'VACUUM_TUTORIAL', 'FLOW_TUTORIAL',
    'TRAINING_SCHEDULE', 'PHASE_INFO', 'BODY_COLUMNS', 'DATA_FILE',
    'BodyDataModel', 'ExerciseLibrary', 'TrainingPlanParser', 'NutritionParser',
    'ExerciseDetailDialog', 'DashboardPage', 'TrendChartPage',
    'ExerciseLibraryPage', 'TrainingPlanPage', 'NutritionPage',
    'AICoachPage', 'AI_COACH_AVAILABLE',
]
