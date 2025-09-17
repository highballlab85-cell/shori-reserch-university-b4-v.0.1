"""C2-Graph 用のデータモデル。

Pydantic v2 を用いて会議JSONをバリデーションしながら読み込み、
後続の制約チェックや矛盾検出で再利用しやすい構造を提供する。
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

ActLiteral = Literal["ASSIGN", "CONFIRM", "REVISE", "CANCEL", "OTHER"]


class CommitmentStateEnum(int, Enum):
    """コミットメント状態の簡易ステートマシン表現。"""

    UNASSIGNED = 0
    ASSIGNED_PENDING = 1
    CONFIRMED = 2
    REVISED_PENDING = 3
    CANCELLED = 4


class UtteranceEvent(BaseModel):
    turn: int = Field(..., ge=1)
    timestamp: str = Field(..., pattern=r"^\d{2}:\d{2}:\d{2}(\.\d{1,3})?$")
    speaker: str
    text: str
    act: ActLiteral
    commitment_id: Optional[str] = Field(default=None, min_length=1)
    task: Optional[str] = None
    owner: Optional[str] = None
    due: Optional[str] = None
    new_owner: Optional[str] = None
    new_due: Optional[str] = None
    reason: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Optional[dict] = None

    @field_validator("confidence")
    @classmethod
    def _validate_confidence_precision(cls, value: Optional[float]) -> Optional[float]:
        return None if value is None else round(value, 6)

    @model_validator(mode="after")
    def _validate_relationships(self) -> "UtteranceEvent":
        if self.act in {"ASSIGN", "CONFIRM", "REVISE", "CANCEL"} and not self.commitment_id:
            raise ValueError("commitment_id is required for commitment-related acts")
        if self.act == "ASSIGN" and not self.owner:
            raise ValueError("ASSIGN requires owner field")
        if self.act == "REVISE" and not (self.new_owner or self.new_due):
            raise ValueError("REVISE requires new_owner or new_due")
        return self


class MeetingRecord(BaseModel):
    meeting_id: str
    topic: Optional[str] = None
    datetime: Optional[str] = None
    participants: Optional[List[str]] = None
    utterances: List[UtteranceEvent]

    @field_validator("utterances", mode="after")
    @classmethod
    def _ensure_sorted(cls, value: Iterable[UtteranceEvent]) -> List[UtteranceEvent]:
        return sorted(list(value), key=lambda ev: ev.turn)

    def commitments(self) -> Dict[str, List[UtteranceEvent]]:
        bucket: Dict[str, List[UtteranceEvent]] = {}
        for event in self.utterances:
            if event.commitment_id:
                bucket.setdefault(event.commitment_id, []).append(event)
        return bucket

    def unique_speakers(self) -> List[str]:
        if self.participants:
            return self.participants
        seen: Dict[str, None] = {}
        for event in self.utterances:
            seen.setdefault(event.speaker, None)
        return list(seen.keys())


class ConstraintViolation(BaseModel):
    commitment_id: str
    turn: int
    violation_type: str
    description: str
    speaker: Optional[str] = None
    severity: Literal["warning", "error"] = "error"


class ConstraintSummary(BaseModel):
    meeting_id: str
    total_commitments: int
    violation_count: int
    violations: List[ConstraintViolation]
    stages: Dict[str, List[CommitmentStateEnum]]
    cp_status: Dict[str, str]


def iter_commitment_states(events: List[UtteranceEvent]) -> List[CommitmentStateEnum]:
    """簡易ステートマシンで状態遷移ログを返す。"""
    states: List[CommitmentStateEnum] = [CommitmentStateEnum.UNASSIGNED]
    current = CommitmentStateEnum.UNASSIGNED
    for event in events:
        if event.act == "ASSIGN":
            current = CommitmentStateEnum.ASSIGNED_PENDING
        elif event.act == "CONFIRM":
            current = CommitmentStateEnum.CONFIRMED
        elif event.act == "REVISE":
            current = CommitmentStateEnum.REVISED_PENDING
        elif event.act == "CANCEL":
            current = CommitmentStateEnum.CANCELLED
        states.append(current)
    return states

