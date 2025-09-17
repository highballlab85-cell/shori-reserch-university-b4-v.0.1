from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Dict, Iterable, List, Literal, Optional

ActLiteral = Literal["ASSIGN", "CONFIRM", "REVISE", "CANCEL", "OTHER"]


class QuestionStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class CommitmentStateEnum(int, Enum):
    """コミットメント状態の簡易ステートマシン表現。"""

    UNASSIGNED = 0
    ASSIGNED_PENDING = 1
    CONFIRMED = 2
    REVISED_PENDING = 3
    CANCELLED = 4


TIMESTAMP_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?$")


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return value.model_dump()
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    return value


class ModelMixin:
    def model_dump(self) -> Dict[str, object]:
        return {f.name: _serialize(getattr(self, f.name)) for f in fields(self)}

    def model_dump_json(self, indent: Optional[int] = None) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False, indent=indent)

    @classmethod
    def model_validate(cls, data):
        if isinstance(data, cls):
            return data
        if not isinstance(data, dict):
            raise TypeError(f"{cls.__name__} expects dict for validation")
        return cls.from_dict(data)


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


@dataclass
class OpenQuestion(ModelMixin):
    question_id: str
    text: str
    status: QuestionStatus = QuestionStatus.OPEN
    raised_by: Optional[str] = None
    raised_turn: Optional[int] = None
    resolved_by: Optional[str] = None
    resolved_turn: Optional[int] = None
    commitment_refs: Optional[List[str]] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "OpenQuestion":
        question_id = str(data["question_id"]).strip()
        if not question_id.startswith("Q"):
            raise ValueError("question_id must start with 'Q'")
        text = str(data["text"])
        status = QuestionStatus(data.get("status", QuestionStatus.OPEN))
        raised_by = data.get("raised_by")
        raised_turn = data.get("raised_turn")
        if raised_turn is not None and int(raised_turn) < 1:
            raise ValueError("raised_turn must be >=1")
        resolved_by = data.get("resolved_by")
        resolved_turn = data.get("resolved_turn")
        if status == QuestionStatus.RESOLVED:
            if not (resolved_by and resolved_turn):
                raise ValueError("resolved questions require resolved_by and resolved_turn")
            if int(resolved_turn) < 1:
                raise ValueError("resolved_turn must be >=1")
        commitment_refs_data = data.get("commitment_refs")
        commitment_refs: Optional[List[str]] = None
        if commitment_refs_data is not None:
            if not isinstance(commitment_refs_data, list):
                raise ValueError("commitment_refs must be a list")
            cleaned = []
            for ref in commitment_refs_data:
                if not ref:
                    raise ValueError("commitment_refs must not contain empty strings")
                cleaned.append(str(ref))
            commitment_refs = _dedupe_preserve_order(cleaned)
        notes = data.get("notes")
        return cls(
            question_id=question_id,
            text=text,
            status=status,
            raised_by=raised_by,
            raised_turn=int(raised_turn) if raised_turn is not None else None,
            resolved_by=resolved_by,
            resolved_turn=int(resolved_turn) if resolved_turn is not None else None,
            commitment_refs=commitment_refs,
            notes=notes,
        )


@dataclass
class UtteranceEvent(ModelMixin):
    turn: int
    timestamp: str
    speaker: str
    text: str
    act: ActLiteral
    commitment_id: Optional[str] = None
    task: Optional[str] = None
    owner: Optional[str] = None
    due: Optional[str] = None
    new_owner: Optional[str] = None
    new_due: Optional[str] = None
    reason: Optional[str] = None
    question_refs: Optional[List[str]] = None
    confidence: Optional[float] = None
    metadata: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "UtteranceEvent":
        turn = int(data["turn"])
        if turn < 1:
            raise ValueError("turn must be >=1")
        timestamp = str(data["timestamp"])
        if not TIMESTAMP_PATTERN.match(timestamp):
            raise ValueError("timestamp must match HH:MM:SS or HH:MM:SS.mmm format")
        speaker = str(data["speaker"])
        text = str(data["text"])
        act = str(data["act"]).upper()
        if act not in {"ASSIGN", "CONFIRM", "REVISE", "CANCEL", "OTHER"}:
            raise ValueError(f"unsupported act: {act}")
        commitment_id = data.get("commitment_id")
        if act in {"ASSIGN", "CONFIRM", "REVISE", "CANCEL"}:
            if not commitment_id:
                raise ValueError("commitment_id is required for commitment-related acts")
            commitment_id = str(commitment_id)
        elif commitment_id:
            commitment_id = str(commitment_id)
        else:
            commitment_id = None
        owner = data.get("owner")
        if act == "ASSIGN" and not owner:
            raise ValueError("ASSIGN requires owner field")
        owner = str(owner) if owner is not None else None
        due = data.get("due")
        due = str(due) if due is not None else None
        new_owner = data.get("new_owner")
        new_due = data.get("new_due")
        if act == "REVISE" and not (new_owner or new_due):
            raise ValueError("REVISE requires new_owner or new_due")
        new_owner = str(new_owner) if new_owner is not None else None
        new_due = str(new_due) if new_due is not None else None
        reason = data.get("reason")
        reason = str(reason) if reason is not None else None
        question_refs = data.get("question_refs")
        if question_refs is not None:
            if not isinstance(question_refs, list):
                raise ValueError("question_refs must be a list")
            cleaned: List[str] = []
            for ref in question_refs:
                if not ref:
                    raise ValueError("question_refs must not contain empty strings")
                ref_str = str(ref)
                if not ref_str.startswith("Q"):
                    raise ValueError("question_refs entries must start with 'Q'")
                cleaned.append(ref_str)
            question_refs = _dedupe_preserve_order(cleaned)
        confidence = data.get("confidence")
        if confidence is not None:
            confidence = float(confidence)
            if not (0.0 <= confidence <= 1.0):
                raise ValueError("confidence must be between 0 and 1")
            confidence = round(confidence, 6)
        metadata = data.get("metadata")
        return cls(
            turn=turn,
            timestamp=timestamp,
            speaker=speaker,
            text=text,
            act=act,  # type: ignore[arg-type]
            commitment_id=commitment_id,
            task=str(data.get("task")) if data.get("task") is not None else None,
            owner=owner,
            due=due,
            new_owner=new_owner,
            new_due=new_due,
            reason=reason,
            question_refs=question_refs,
            confidence=confidence,
            metadata=metadata if isinstance(metadata, dict) else None,
        )


@dataclass
class MeetingRecord(ModelMixin):
    meeting_id: str
    topic: Optional[str] = None
    datetime: Optional[str] = None
    participants: Optional[List[str]] = None
    open_questions: Optional[List[OpenQuestion]] = None
    utterances: List[UtteranceEvent] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "MeetingRecord":
        meeting_id = str(data["meeting_id"])
        topic = data.get("topic")
        datetime_value = data.get("datetime")
        participants = data.get("participants")
        if participants is not None:
            if not isinstance(participants, list):
                raise ValueError("participants must be a list")
            participants = [str(p) for p in participants]
        open_questions_data = data.get("open_questions")
        open_questions: Optional[List[OpenQuestion]] = None
        if open_questions_data is not None:
            if not isinstance(open_questions_data, list):
                raise ValueError("open_questions must be a list")
            parsed: List[OpenQuestion] = []
            seen_ids = set()
            for item in open_questions_data:
                question = OpenQuestion.model_validate(item)
                if question.question_id in seen_ids:
                    raise ValueError(f"duplicated question_id detected: {question.question_id}")
                seen_ids.add(question.question_id)
                parsed.append(question)
            open_questions = parsed
        utterances_data = data.get("utterances")
        if not isinstance(utterances_data, list) or not utterances_data:
            raise ValueError("utterances must be a non-empty list")
        utterances = [UtteranceEvent.model_validate(item) for item in utterances_data]
        utterances.sort(key=lambda ev: ev.turn)
        question_ids = {q.question_id for q in open_questions or []}
        for event in utterances:
            if event.question_refs:
                unknown = [ref for ref in event.question_refs if ref not in question_ids]
                if unknown:
                    raise ValueError(
                        f"Utterance turn {event.turn} references unknown questions: {unknown}"
                    )
        return cls(
            meeting_id=meeting_id,
            topic=str(topic) if topic is not None else None,
            datetime=str(datetime_value) if datetime_value is not None else None,
            participants=participants,  # type: ignore[arg-type]
            open_questions=open_questions,
            utterances=utterances,
        )

    def open_question_index(self) -> Dict[str, OpenQuestion]:
        return {q.question_id: q for q in self.open_questions or []}

    def unresolved_questions(self) -> List[OpenQuestion]:
        return [q for q in self.open_questions or [] if q.status == QuestionStatus.OPEN]

    def commitments(self) -> Dict[str, List[UtteranceEvent]]:
        bucket: Dict[str, List[UtteranceEvent]] = {}
        for event in self.utterances:
            if event.commitment_id:
                bucket.setdefault(event.commitment_id, []).append(event)
        return bucket

    def unique_speakers(self) -> List[str]:
        if self.participants:
            return list(self.participants)
        seen: Dict[str, None] = {}
        for event in self.utterances:
            seen.setdefault(event.speaker, None)
        return list(seen.keys())


@dataclass
class ConstraintViolation(ModelMixin):
    commitment_id: str
    turn: int
    violation_type: str
    description: str
    speaker: Optional[str] = None
    severity: Literal["warning", "error"] = "error"

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConstraintViolation":
        return cls(
            commitment_id=str(data["commitment_id"]),
            turn=int(data["turn"]),
            violation_type=str(data["violation_type"]),
            description=str(data["description"]),
            speaker=str(data["speaker"]) if data.get("speaker") is not None else None,
            severity=data.get("severity", "error"),  # type: ignore[arg-type]
        )


@dataclass
class ConstraintSummary(ModelMixin):
    meeting_id: str
    total_commitments: int
    violation_count: int
    violations: List[ConstraintViolation]
    stages: Dict[str, List[CommitmentStateEnum]]
    cp_status: Dict[str, str]

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConstraintSummary":
        violations_data = data.get("violations", [])
        violations = [ConstraintViolation.from_dict(item) for item in violations_data]
        stages_data = data.get("stages", {})
        stages: Dict[str, List[CommitmentStateEnum]] = {}
        for cid, seq in stages_data.items():
            stages[cid] = [CommitmentStateEnum(value) for value in seq]
        cp_status_data = data.get("cp_status", {})
        return cls(
            meeting_id=str(data["meeting_id"]),
            total_commitments=int(data["total_commitments"]),
            violation_count=int(data["violation_count"]),
            violations=violations,
            stages=stages,
            cp_status={str(k): str(v) for k, v in cp_status_data.items()},
        )


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
