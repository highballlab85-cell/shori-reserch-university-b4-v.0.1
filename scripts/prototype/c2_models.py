from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    cast,
)

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


TModel = TypeVar("TModel", bound="ModelMixin")


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
    def model_dump(self, *, exclude_none: bool = False) -> Dict[str, object]:
        result: Dict[str, object] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if exclude_none and value is None:
                continue
            result[f.name] = _serialize(value)
        return result

    def model_dump_json(
        self, indent: Optional[int] = None, *, exclude_none: bool = False
    ) -> str:
        return json.dumps(
            self.model_dump(exclude_none=exclude_none),
            ensure_ascii=False,
            indent=indent,
        )

    @classmethod
    def model_validate(cls: Type[TModel], data: Any) -> TModel:
        if isinstance(data, cls):
            return data
        if isinstance(data, Mapping):
            return cls.from_dict(dict(data))
        raise TypeError(f"{cls.__name__} expects dict for validation")

    @classmethod
    def model_validate_json(cls: Type[TModel], data: str) -> TModel:
        return cls.model_validate(json.loads(data))

    def model_copy(
        self: TModel, *, update: Optional[Mapping[str, Any]] = None
    ) -> TModel:
        payload = self.model_dump()
        if update:
            payload.update(update)
        return self.__class__.model_validate(payload)


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

    def __post_init__(self) -> None:
        self.question_id = str(self.question_id).strip()
        if not self.question_id or not self.question_id.startswith("Q"):
            raise ValueError("question_id must start with 'Q'")
        self.text = str(self.text)
        if isinstance(self.status, str):
            self.status = QuestionStatus(self.status)
        if self.raised_by is not None:
            self.raised_by = str(self.raised_by)
        if self.raised_turn is not None:
            self.raised_turn = int(self.raised_turn)
            if self.raised_turn < 1:
                raise ValueError("raised_turn must be >=1")
        if self.resolved_by is not None:
            self.resolved_by = str(self.resolved_by)
        if self.resolved_turn is not None:
            self.resolved_turn = int(self.resolved_turn)
            if self.resolved_turn < 1:
                raise ValueError("resolved_turn must be >=1")
        if self.status == QuestionStatus.RESOLVED and not (
            self.resolved_by and self.resolved_turn
        ):
            raise ValueError("resolved questions require resolved_by and resolved_turn")
        if self.commitment_refs is not None:
            cleaned: List[str] = []
            for ref in self.commitment_refs:
                if not ref:
                    raise ValueError(
                        "commitment_refs must not contain empty strings"
                    )
                ref_str = str(ref)
                cleaned.append(ref_str)
            self.commitment_refs = _dedupe_preserve_order(cleaned)
        if self.notes is not None:
            self.notes = str(self.notes)

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

    def __post_init__(self) -> None:
        self.turn = int(self.turn)
        if self.turn < 1:
            raise ValueError("turn must be >=1")
        self.timestamp = str(self.timestamp)
        if not TIMESTAMP_PATTERN.match(self.timestamp):
            raise ValueError("timestamp must match HH:MM:SS or HH:MM:SS.mmm format")
        self.speaker = str(self.speaker)
        self.text = str(self.text)
        act_value = self.act
        if isinstance(act_value, str):
            act_value = act_value.upper()
        if act_value not in {"ASSIGN", "CONFIRM", "REVISE", "CANCEL", "OTHER"}:
            raise ValueError(f"unsupported act: {act_value}")
        self.act = cast(ActLiteral, act_value)
        if self.commitment_id is not None:
            cid = str(self.commitment_id).strip()
            if not cid:
                raise ValueError("commitment_id must not be empty")
            self.commitment_id = cid
        if self.act in {"ASSIGN", "CONFIRM", "REVISE", "CANCEL"} and not self.commitment_id:
            raise ValueError("commitment_id is required for commitment-related acts")
        if self.task is not None:
            self.task = str(self.task)
        if self.owner is not None:
            self.owner = str(self.owner)
        if self.due is not None:
            self.due = str(self.due)
        if self.new_owner is not None:
            self.new_owner = str(self.new_owner)
        if self.new_due is not None:
            self.new_due = str(self.new_due)
        if self.reason is not None:
            self.reason = str(self.reason)
        if self.act == "ASSIGN" and not self.owner:
            raise ValueError("ASSIGN requires owner field")
        if self.act == "REVISE" and not (self.new_owner or self.new_due):
            raise ValueError("REVISE requires new_owner or new_due")
        if self.question_refs is not None:
            cleaned: List[str] = []
            for ref in self.question_refs:
                if not ref:
                    raise ValueError("question_refs must not contain empty strings")
                ref_str = str(ref)
                if not ref_str.startswith("Q"):
                    raise ValueError("question_refs entries must start with 'Q'")
                cleaned.append(ref_str)
            self.question_refs = _dedupe_preserve_order(cleaned)
        if self.confidence is not None:
            self.confidence = float(self.confidence)
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError("confidence must be between 0 and 1")
            self.confidence = round(self.confidence, 6)
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary if provided")

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
        act_literal = cast(ActLiteral, act)
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
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary if provided")
        return cls(
            turn=turn,
            timestamp=timestamp,
            speaker=speaker,
            text=text,
            act=act_literal,
            commitment_id=commitment_id,
            task=str(data.get("task")) if data.get("task") is not None else None,
            owner=owner,
            due=due,
            new_owner=new_owner,
            new_due=new_due,
            reason=reason,
            question_refs=question_refs,
            confidence=confidence,
            metadata=metadata,
        )


@dataclass
class MeetingRecord(ModelMixin):
    meeting_id: str
    topic: Optional[str] = None
    datetime: Optional[str] = None
    participants: Optional[List[str]] = None
    open_questions: Optional[List[OpenQuestion]] = None
    utterances: List[UtteranceEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.meeting_id = str(self.meeting_id).strip()
        if not self.meeting_id:
            raise ValueError("meeting_id must not be empty")
        if self.topic is not None:
            self.topic = str(self.topic)
        if self.datetime is not None:
            self.datetime = str(self.datetime)
        if self.participants is not None:
            participants_list: List[str] = []
            for participant in self.participants:
                participant_str = str(participant).strip()
                if not participant_str:
                    raise ValueError("participants entries must not be empty")
                participants_list.append(participant_str)
            self.participants = _dedupe_preserve_order(participants_list)
        if self.open_questions is not None:
            parsed_questions: List[OpenQuestion] = []
            seen_ids = set()
            for item in self.open_questions:
                question = OpenQuestion.model_validate(item)
                if question.question_id in seen_ids:
                    raise ValueError(
                        f"duplicated question_id detected: {question.question_id}"
                    )
                seen_ids.add(question.question_id)
                parsed_questions.append(question)
            self.open_questions = parsed_questions
        if not isinstance(self.utterances, list) or not self.utterances:
            raise ValueError("utterances must be a non-empty list")
        parsed_utterances: List[UtteranceEvent] = []
        for item in self.utterances:
            parsed_utterances.append(UtteranceEvent.model_validate(item))
        parsed_utterances.sort(key=lambda ev: ev.turn)
        self.utterances = parsed_utterances
        question_ids = {q.question_id for q in self.open_questions or []}
        for event in self.utterances:
            if event.question_refs:
                unknown = [ref for ref in event.question_refs if ref not in question_ids]
                if unknown:
                    raise ValueError(
                        f"Utterance turn {event.turn} references unknown questions: {unknown}"
                    )

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "MeetingRecord":
        if "meeting_id" not in data:
            raise ValueError("meeting_id is required")
        participants_data = data.get("participants")
        if participants_data is not None and not isinstance(participants_data, list):
            raise ValueError("participants must be a list")
        open_questions_data = data.get("open_questions")
        if open_questions_data is not None and not isinstance(open_questions_data, list):
            raise ValueError("open_questions must be a list")
        utterances_data = data.get("utterances")
        if not isinstance(utterances_data, list):
            raise ValueError("utterances must be provided as a list")
        return cls(
            meeting_id=data["meeting_id"],
            topic=data.get("topic"),
            datetime=data.get("datetime"),
            participants=participants_data,
            open_questions=open_questions_data,
            utterances=utterances_data,  # type: ignore[arg-type]
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

    def __post_init__(self) -> None:
        self.commitment_id = str(self.commitment_id).strip()
        if not self.commitment_id:
            raise ValueError("commitment_id must not be empty")
        self.turn = int(self.turn)
        self.violation_type = str(self.violation_type)
        self.description = str(self.description)
        if self.speaker is not None:
            speaker_value = str(self.speaker).strip()
            self.speaker = speaker_value if speaker_value else None
        severity_value = self.severity
        if isinstance(severity_value, str):
            severity_value = severity_value.lower()
        if severity_value not in {"warning", "error"}:
            raise ValueError("severity must be 'warning' or 'error'")
        self.severity = cast(Literal["warning", "error"], severity_value)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConstraintViolation":
        return cls(
            commitment_id=str(data["commitment_id"]),
            turn=int(data["turn"]),
            violation_type=str(data["violation_type"]),
            description=str(data["description"]),
            speaker=str(data["speaker"]) if data.get("speaker") is not None else None,
            severity=str(data.get("severity", "error")),
        )


@dataclass
class ConstraintSummary(ModelMixin):
    meeting_id: str
    total_commitments: int
    violation_count: int
    violations: List[ConstraintViolation]
    stages: Dict[str, List[CommitmentStateEnum]]
    cp_status: Dict[str, str]

    def __post_init__(self) -> None:
        self.meeting_id = str(self.meeting_id)
        self.total_commitments = int(self.total_commitments)
        self.violation_count = int(self.violation_count)
        validated_violations: List[ConstraintViolation] = []
        for violation in self.violations:
            validated_violations.append(ConstraintViolation.model_validate(violation))
        self.violations = validated_violations
        validated_stages: Dict[str, List[CommitmentStateEnum]] = {}
        if not isinstance(self.stages, Mapping):
            raise ValueError("stages must be a mapping")
        for cid, seq in self.stages.items():
            cid_str = str(cid)
            if not isinstance(seq, Sequence):
                raise ValueError("stage sequences must be iterable")
            validated_seq: List[CommitmentStateEnum] = []
            for value in seq:
                if isinstance(value, CommitmentStateEnum):
                    validated_seq.append(value)
                else:
                    validated_seq.append(CommitmentStateEnum(value))
            validated_stages[cid_str] = validated_seq
        self.stages = validated_stages
        if not isinstance(self.cp_status, Mapping):
            raise ValueError("cp_status must be a mapping")
        self.cp_status = {str(k): str(v) for k, v in self.cp_status.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ConstraintSummary":
        violations_data = data.get("violations", [])
        violations = [ConstraintViolation.from_dict(item) for item in violations_data]
        stages_data = data.get("stages", {})
        if not isinstance(stages_data, Mapping):
            raise ValueError("stages must be a mapping")
        stages: Dict[str, List[CommitmentStateEnum]] = {}
        for cid, seq in stages_data.items():
            stages[cid] = [CommitmentStateEnum(value) for value in seq]
        cp_status_data = data.get("cp_status", {})
        if not isinstance(cp_status_data, Mapping):
            raise ValueError("cp_status must be a mapping")
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
