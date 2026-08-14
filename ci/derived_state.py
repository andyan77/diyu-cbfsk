#!/usr/bin/env python3
"""派生状态字段的**唯一**实现（EQ-1）。

裁决 DIYU-CBFSK-FOUNDER-M2-PREMERGE-REVIEW-001 第八节：execution_status 的枚举不扩展，
挂起改由 m2_status 承载；代价是消费者要同时记住三条隐含优先级才能回答
「现在还能不能继续施工」。本模块把那三条优先级收成一个布尔字段。

两个消费者共用本实现，谁也不许再算一遍：
  ci/compile_role_instructions.py —— 生成投影时现算，写进 CLAUDE.md／AGENTS.md 状态块
  ci/checkers/check_project_state.py —— 现算后与投影、与 README 状态块比对

不得手工赋值：project_state 里出现 execution_permitted 键即判 DERIVED_FIELD_HAND_ASSIGNED。
一个能手填的派生字段就不是派生字段，是又一个可以说谎的状态位。
"""

from __future__ import annotations

SUSPENDED = "SUSPENDED_BY_FOUNDER"
NOT_STARTED = "EXECUTION_NOT_STARTED"

# 里程碑状态位的命名约定：<milestone>_status。执行是否被允许，取决于这些位里有没有挂起的。
MILESTONE_STATUS_SUFFIX = "_status"
MILESTONE_STATUS_EXCLUDED = ("project_status", "execution_status")

DERIVED_FIELD_NAMES = ("execution_permitted",)


def milestone_status_keys(project_state: dict) -> list[str]:
    """project_state 里哪些键是里程碑状态位——按命名约定现场取，不写死清单。

    写死清单的后果是 M3 加进来时没人记得改这里，而判据照样全绿。
    """
    return sorted(
        key
        for key in project_state
        if key.endswith(MILESTONE_STATUS_SUFFIX) and key not in MILESTONE_STATUS_EXCLUDED
    )


def execution_permitted(project_state: dict) -> bool:
    """「现在还能不能继续施工」——单一答案。

    false 的两种来源：执行尚未开始；或任一里程碑被 Founder 挂起。
    后者压过 execution_status——execution_status 答的是「哪个里程碑在飞」，
    一个在飞的里程碑同样可以是被挂起的。
    """
    if project_state.get("execution_status") == NOT_STARTED:
        return False
    return not any(project_state.get(key) == SUSPENDED for key in milestone_status_keys(project_state))


def derived_fields(project_state: dict) -> dict:
    """全部派生字段，按声明顺序。投影与判据都取这一份。"""
    return {"execution_permitted": execution_permitted(project_state)}


def hand_assigned_derived_fields(project_state: dict) -> list[str]:
    """project_state 里被手工写上的派生字段名——有一个就是一个缺陷。"""
    return [name for name in DERIVED_FIELD_NAMES if name in project_state]
