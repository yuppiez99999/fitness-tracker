# -*- coding: utf-8 -*-
"""
fitness_pkg — 健身监控模块化包 (v7.0)
将原本单文件 fitness_modules.py 拆分为:
  constants.py   全局配置/常量/工具
  data_model.py  体测数据模型 BodyDataModel
  exercise_lib.py 动作库 ExerciseLibrary
  parsers.py     训练计划/营养方案解析器
  dialogs.py     动作详情弹窗
  ui_pages.py    5个UI页面
  ai_coach.py    AI 教练页面
"""
from .constants import (
    COLORS, MUSCLE_EMOJI, VACUUM_TUTORIAL, FLOW_TUTORIAL,
    TRAINING_SCHEDULE, PHASE_INFO, BODY_COLUMNS, DATA_FILE,
)
from .data_model import BodyDataModel
from .exercise_lib import ExerciseLibrary
from .parsers import TrainingPlanParser, NutritionParser
from .dialogs import ExerciseDetailDialog
from .ui_pages import (
    DashboardPage, TrendChartPage, ExerciseLibraryPage,
    TrainingPlanPage, NutritionPage,
)
from .ai_coach import AICoachPage, AI_COACH_AVAILABLE

__all__ = [
    'COLORS', 'MUSCLE_EMOJI', 'VACUUM_TUTORIAL', 'FLOW_TUTORIAL',
    'TRAINING_SCHEDULE', 'PHASE_INFO', 'BODY_COLUMNS', 'DATA_FILE',
    'BodyDataModel', 'ExerciseLibrary', 'TrainingPlanParser', 'NutritionParser',
    'ExerciseDetailDialog', 'DashboardPage', 'TrendChartPage',
    'ExerciseLibraryPage', 'TrainingPlanPage', 'NutritionPage',
    'AICoachPage', 'AI_COACH_AVAILABLE',
]
