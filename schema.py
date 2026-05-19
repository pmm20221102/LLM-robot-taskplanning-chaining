from typing import Literal, Optional
from pydantic import BaseModel, Field


AllowedStatus = Literal[
    "valid",
    "ambiguous",
    "target_not_found",
    "unsupported"
]

AllowedAction = Literal[
    "locate_entity",
    "navigate_to",
    "escort_to",
    "guide_to",
    "avoid_area",
    "wait",
    "ask_clarification",
    "handover_to_staff",
    "trigger_workflow",
    "perform_screening",
    "return_to_base"
]

TargetType = Literal[
    "person",
    "room",
    "object",
    "area",
    "workflow",
    "base",
    "unknown"
]

ExecutorType = Literal[
    "nav2",
    "scene_graph",
    "llm",
    "external_workflow",
    "human_staff",
    "none"
]


class Constraints(BaseModel):
    avoid: list[str] = Field(default_factory=list)
    prefer: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


class TaskStep(BaseModel):
    step: int
    action: AllowedAction
    target_type: TargetType
    target_id: Optional[str] = None
    description: str
    executor: ExecutorType
    constraints: Constraints = Field(default_factory=Constraints)


class TaskPlan(BaseModel):
    status: AllowedStatus
    task_chain: list[TaskStep]
    clarification_request: Optional[str] = None
    target_not_found: Optional[str] = None
    notes: list[str] = Field(default_factory=list)
