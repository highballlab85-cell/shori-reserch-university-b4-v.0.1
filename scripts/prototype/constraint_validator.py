#!/usr/bin/env python3
"""C2-Graph コミットメント制約バリデータ (MVP)。

- 会議JSONを読み込み、軽量データクラスモデルで構造を検証
- OR-Tools CP-SAT が利用可能なら遷移制約を充足可能性チェック
- 手続き的なルールで権限違反や重複キャンセル、確認漏れ等を検出
- Markdown/JSON の簡易レポートを生成
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from ortools.sat.python import cp_model
except ImportError:  # OR-Tools がない場合は None を保持
    cp_model = None

try:
    from scripts.prototype.c2_models import (
        CommitmentStateEnum,
        ConstraintSummary,
        ConstraintViolation,
        MeetingRecord,
        UtteranceEvent,
        iter_commitment_states,
    )
except ModuleNotFoundError:
    import sys
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.append(str(CURRENT_DIR))
    from c2_models import (
        CommitmentStateEnum,
        ConstraintSummary,
        ConstraintViolation,
        MeetingRecord,
        UtteranceEvent,
        iter_commitment_states,
    )


ALLOWED_TRANSITIONS: Dict[str, Sequence[Tuple[CommitmentStateEnum, CommitmentStateEnum]]] = {
    "ASSIGN": (
        (CommitmentStateEnum.UNASSIGNED, CommitmentStateEnum.ASSIGNED_PENDING),
        (CommitmentStateEnum.CANCELLED, CommitmentStateEnum.ASSIGNED_PENDING),
    ),
    "CONFIRM": (
        (CommitmentStateEnum.ASSIGNED_PENDING, CommitmentStateEnum.CONFIRMED),
        (CommitmentStateEnum.REVISED_PENDING, CommitmentStateEnum.CONFIRMED),
    ),
    "REVISE": (
        (CommitmentStateEnum.ASSIGNED_PENDING, CommitmentStateEnum.REVISED_PENDING),
        (CommitmentStateEnum.CONFIRMED, CommitmentStateEnum.REVISED_PENDING),
        (CommitmentStateEnum.CANCELLED, CommitmentStateEnum.REVISED_PENDING),
    ),
    "CANCEL": (
        (CommitmentStateEnum.ASSIGNED_PENDING, CommitmentStateEnum.CANCELLED),
        (CommitmentStateEnum.CONFIRMED, CommitmentStateEnum.CANCELLED),
        (CommitmentStateEnum.REVISED_PENDING, CommitmentStateEnum.CANCELLED),
    ),
}


@dataclass
class CommitmentContext:
    commitment_id: str
    owner: Optional[str] = None
    due: Optional[str] = None
    state: CommitmentStateEnum = CommitmentStateEnum.UNASSIGNED
    requires_confirmation: bool = False


class ConstraintValidator:
    def __init__(self, enable_cp: bool = True) -> None:
        self.enable_cp = enable_cp and cp_model is not None

    def validate(self, meeting: MeetingRecord) -> ConstraintSummary:
        violations: List[ConstraintViolation] = []
        stages: Dict[str, List[CommitmentStateEnum]] = {}

        cp_status_map: Dict[str, str] = {}

        for cid, events in meeting.commitments().items():
            context = CommitmentContext(commitment_id=cid)
            stages[cid] = iter_commitment_states(events)
            violations.extend(self._validate_commitment(context, events))

            cp_status = "SKIPPED"
            cp_states = None
            if self.enable_cp:
                cp_status, cp_states = self._run_cp(events)
                if cp_status == "INFEASIBLE":
                    violations.append(
                        ConstraintViolation(
                            commitment_id=cid,
                            turn=events[0].turn,
                            violation_type="cp_infeasible_transition",
                            description="OR-Tools による遷移制約が充足不能",
                            speaker=None,
                        )
                    )
                elif cp_status == "FEASIBLE" and cp_states is not None:
                    stages[cid] = [CommitmentStateEnum(value) for value in cp_states]
            cp_status_map[cid] = cp_status

        summary = ConstraintSummary(
            meeting_id=meeting.meeting_id,
            total_commitments=len(stages),
            violation_count=len(violations),
            violations=violations,
            stages=stages,
            cp_status=cp_status_map,
        )
        return summary

    def _validate_commitment(
        self, context: CommitmentContext, events: List[UtteranceEvent]
    ) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []

        for event in events:
            allowed = ALLOWED_TRANSITIONS.get(event.act, ())
            transition = (context.state, self._next_state(event))

            if allowed and transition not in allowed:
                violations.append(
                    ConstraintViolation(
                        commitment_id=context.commitment_id,
                        turn=event.turn,
                        violation_type="invalid_transition",
                        description=f"{context.state.name} から {event.act} は許可されていない遷移",
                        speaker=event.speaker,
                    )
                )

            if event.act == "ASSIGN":
                context.owner = event.owner or context.owner
                context.due = event.due or context.due
                context.requires_confirmation = True
                context.state = CommitmentStateEnum.ASSIGNED_PENDING
            elif event.act == "CONFIRM":
                if context.state == CommitmentStateEnum.UNASSIGNED:
                    violations.append(
                        ConstraintViolation(
                            commitment_id=context.commitment_id,
                            turn=event.turn,
                            violation_type="confirm_without_assign",
                            description="ASSIGN が存在しない状態で CONFIRM が発生",
                            speaker=event.speaker,
                        )
                    )
                context.owner = context.owner or event.owner or event.speaker
                context.requires_confirmation = False
                context.state = CommitmentStateEnum.CONFIRMED
            elif event.act == "REVISE":
                if context.state == CommitmentStateEnum.UNASSIGNED:
                    violations.append(
                        ConstraintViolation(
                            commitment_id=context.commitment_id,
                            turn=event.turn,
                            violation_type="revise_without_assign",
                            description="ASSIGN 前に REVISE が発生",
                            speaker=event.speaker,
                        )
                    )
                if event.new_owner:
                    context.owner = event.new_owner
                if event.new_due:
                    context.due = event.new_due
                context.requires_confirmation = True
                context.state = CommitmentStateEnum.REVISED_PENDING
            elif event.act == "CANCEL":
                self._validate_cancel(context, event, violations)
                context.requires_confirmation = False
                context.state = CommitmentStateEnum.CANCELLED

        if context.requires_confirmation and events:
            last_event = events[-1]
            violations.append(
                ConstraintViolation(
                    commitment_id=context.commitment_id,
                    turn=last_event.turn,
                    violation_type="missing_confirmation",
                    description="ASSIGN/REVISE 後に CONFIRM が未完了",
                    speaker=context.owner or last_event.speaker,
                    severity="warning",
                )
            )

        return violations

    def _next_state(self, event: UtteranceEvent) -> CommitmentStateEnum:
        if event.act == "ASSIGN":
            return CommitmentStateEnum.ASSIGNED_PENDING
        if event.act == "CONFIRM":
            return CommitmentStateEnum.CONFIRMED
        if event.act == "REVISE":
            return CommitmentStateEnum.REVISED_PENDING
        if event.act == "CANCEL":
            return CommitmentStateEnum.CANCELLED
        return CommitmentStateEnum.UNASSIGNED

    def _validate_cancel(
        self,
        context: CommitmentContext,
        event: UtteranceEvent,
        violations: List[ConstraintViolation],
    ) -> None:
        if context.state == CommitmentStateEnum.UNASSIGNED:
            violations.append(
                ConstraintViolation(
                    commitment_id=context.commitment_id,
                    turn=event.turn,
                    violation_type="cancel_without_assignment",
                    description="ASSIGN 前に CANCEL が発生",
                    speaker=event.speaker,
                )
            )
        if context.owner and event.speaker != context.owner:
            violations.append(
                ConstraintViolation(
                    commitment_id=context.commitment_id,
                    turn=event.turn,
                    violation_type="unauthorized_cancel",
                    description=f"オーナー {context.owner} 以外が CANCEL を実施",
                    speaker=event.speaker,
                )
            )
        if context.state == CommitmentStateEnum.CANCELLED:
            violations.append(
                ConstraintViolation(
                    commitment_id=context.commitment_id,
                    turn=event.turn,
                    violation_type="duplicate_cancel",
                    description="既にキャンセル済みのコミットメントに対する重複CANCEL",
                    speaker=event.speaker,
                )
            )
        if context.requires_confirmation:
            violations.append(
                ConstraintViolation(
                    commitment_id=context.commitment_id,
                    turn=event.turn,
                    violation_type="cancel_before_confirmation",
                    description="REVISE/ASSIGN の確認前にCANCEL",
                    speaker=event.speaker,
                )
            )

    def _run_cp(
        self, events: List[UtteranceEvent]
    ) -> Tuple[str, Optional[List[int]]]:
        if cp_model is None or not events:
            return "SKIPPED", None

        model = cp_model.CpModel()
        state_vars = [model.NewIntVar(0, 4, f"state_{idx}") for idx in range(len(events) + 1)]
        model.Add(state_vars[0] == CommitmentStateEnum.UNASSIGNED.value)

        for idx, event in enumerate(events):
            allowed = ALLOWED_TRANSITIONS.get(event.act, ())
            if not allowed:
                # OTHER などは前後状態が変わらないとみなす
                model.Add(state_vars[idx + 1] == state_vars[idx])
                continue
            tuples = [(prev.value, nxt.value) for prev, nxt in allowed]
            model.AddAllowedAssignments([state_vars[idx], state_vars[idx + 1]], tuples)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 1.0
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return "FEASIBLE", [int(solver.Value(var)) for var in state_vars]
        if status == cp_model.INFEASIBLE:
            return "INFEASIBLE", None
        return "UNKNOWN", None


def render_markdown(summary: ConstraintSummary) -> str:
    lines: List[str] = []
    lines.append(f"会議ID: {summary.meeting_id}")
    lines.append("")
    lines.append("## コミットメント状態シーケンス")
    for cid, states in summary.stages.items():
        state_labels = ", ".join(state.name for state in states)
        cp_status = summary.cp_status.get(cid, "SKIPPED")
        lines.append(f"- {cid} (CP: {cp_status}): {state_labels}")
    lines.append("")
    lines.append("## 検出された違反")
    if not summary.violations:
        lines.append("- 違反なし")
    else:
        for violation in summary.violations:
            speaker = f" (話者: {violation.speaker})" if violation.speaker else ""
            lines.append(
                f"- turn{violation.turn} {violation.commitment_id}: {violation.violation_type}"
                f" | {violation.description}{speaker}"
            )
    lines.append("")
    lines.append(
        f"違反件数: {summary.violation_count} / コミットメント総数: {summary.total_commitments}"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="C2-Graph 制約バリデータ")
    parser.add_argument("input", type=Path, help="会議JSONファイル")
    parser.add_argument(
        "--outdir",
        type=Path,
        help="レポート出力ディレクトリ (指定時は Markdown と JSON を保存)",
    )
    parser.add_argument(
        "--no-cp",
        action="store_true",
        help="CP-SAT を使用せず、ルールチェックのみ実施",
    )
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    meeting = MeetingRecord.model_validate(data)

    validator = ConstraintValidator(enable_cp=not args.no_cp)
    summary = validator.validate(meeting)

    markdown = render_markdown(summary)
    print(markdown)

    if args.outdir:
        args.outdir.mkdir(parents=True, exist_ok=True)
        md_path = args.outdir / f"{meeting.meeting_id}_constraint_report.md"
        json_path = args.outdir / f"{meeting.meeting_id}_constraint_report.json"
        md_path.write_text(markdown, encoding="utf-8")
        json_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
