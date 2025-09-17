#!/usr/bin/env python3
"""C2-Graph試作スクリプト

サンプルの会議トランスクリプト(JSON)を入力し、ASSIGN/CONFIRM/REVISE/CANCEL
の状態遷移をトラッキングして矛盾を検出する。矛盾検出ルールは暫定:

- 未割り当てのコミットメントに対する CANCEL
- オーナー以外による CANCEL
- すでにキャンセル済みのコミットメントに対する重複 CANCEL
- REVISE 後に確認(CONFIRM)される前の CANCEL
- ASSIGN / REVISE の確認待ち状態が指定時間を過ぎた場合（将来対応予定）

出力はテキストレポートとして stdout へ。--output を指定するとファイルにも保存する。
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import networkx as nx
except ImportError:  # networkxが未インストールでも動作可能にする
    nx = None

try:
    from .c2_models import MeetingRecord, UtteranceEvent
except ImportError:
    import sys
    CURRENT_DIR = Path(__file__).resolve().parent
    if str(CURRENT_DIR) not in sys.path:
        sys.path.append(str(CURRENT_DIR))
    from c2_models import MeetingRecord, UtteranceEvent

@dataclass
class CommitmentState:
    commitment_id: str
    owner: Optional[str] = None
    due: Optional[str] = None
    status: str = "assigned"
    history: List[dict] = field(default_factory=list)
    requires_confirmation: bool = False

    def record(self, event: UtteranceEvent) -> None:
        self.history.append(event.model_dump())


def load_meeting(path: Path) -> MeetingRecord:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return MeetingRecord.model_validate(data)


def build_graph(events: List[UtteranceEvent]):
    graph = None
    if nx is not None:
        graph = nx.DiGraph()
        for event in events:
            node = f"commitment:{event.commitment_id}"
            if event.commitment_id and not graph.has_node(node):
                graph.add_node(node, type="commitment")
            speaker_node = f"speaker:{event.speaker}"
            if not graph.has_node(speaker_node):
                graph.add_node(speaker_node, type="speaker")
            if event.commitment_id:
                graph.add_edge(
                    speaker_node,
                    node,
                    act=event.act,
                    turn=event.turn,
                    timestamp=event.timestamp,
                )
    return graph


CONTRADICTION_SUGGESTIONS = {
    "cancel_without_assignment": "ASSIGNの記録が残っているか確認し、割り当て情報を明示した上でキャンセルを宣言する。",
    "unauthorized_cancel": "コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。",
    "duplicate_cancel": "一度キャンセルした場合は進行ログを共有し、重複報告を避ける運用にする。",
    "cancel_before_confirmation": "REVISE/ASSIGN後は担当者のCONFIRMを待ち、必要に応じてリマインドを送る。",
    "missing_confirmation": "ASSIGN/REVISE後の確認が抜けていないかを点検し、担当者から明示的なCONFIRM発話を得る。",
}


def suggest_action(contradiction_type: str) -> str:
    return CONTRADICTION_SUGGESTIONS.get(
        contradiction_type,
        "矛盾の原因を確認し、担当者全員で是正手順を合意する。",
    )


def analyse_meeting(meeting: MeetingRecord) -> Dict[str, object]:
    commitments: Dict[str, CommitmentState] = {}
    contradictions: List[dict] = []

    for event in meeting.utterances:
        act = event.act.upper()
        cid = event.commitment_id
        if not cid:
            continue
        state = commitments.get(cid)

        if act == "ASSIGN":
            state = commitments.setdefault(cid, CommitmentState(cid))
            state.owner = event.owner or state.owner
            state.due = event.due or state.due
            state.status = "assigned"
            state.requires_confirmation = True
            state.record(event)
        elif act == "CONFIRM":
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            state.owner = state.owner or event.owner or event.speaker
            state.status = "confirmed"
            state.requires_confirmation = False
            state.record(event)
        elif act == "REVISE":
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            if event.new_owner:
                state.owner = event.new_owner
            if event.new_due:
                state.due = event.new_due
            state.status = "revised"
            state.requires_confirmation = True
            state.record(event)
        elif act == "CANCEL":
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
                state.status = "cancelled"
                state.requires_confirmation = False
                state.record(event)
                contradictions.append(
                    {
                        "turn": event.turn,
                        "commitment_id": cid,
                        "type": "cancel_without_assignment",
                        "speaker": event.speaker,
                        "detail": "ASSIGN前にCANCELが発生",
                        "suggestion": suggest_action("cancel_without_assignment"),
                    }
                )
                continue
            if state.owner and event.speaker != state.owner:
                contradictions.append(
                    {
                        "turn": event.turn,
                        "commitment_id": cid,
                        "type": "unauthorized_cancel",
                        "speaker": event.speaker,
                        "detail": f"オーナー({state.owner})以外がCANCEL",
                        "suggestion": suggest_action("unauthorized_cancel"),
                    }
                )
            elif state.status == "cancelled":
                contradictions.append(
                    {
                        "turn": event.turn,
                        "commitment_id": cid,
                        "type": "duplicate_cancel",
                        "speaker": event.speaker,
                        "detail": "既にCANCEL済みのコミットメント",
                        "suggestion": suggest_action("duplicate_cancel"),
                    }
                )
            if state.requires_confirmation:
                contradictions.append(
                    {
                        "turn": event.turn,
                        "commitment_id": cid,
                        "type": "cancel_before_confirmation",
                        "speaker": event.speaker,
                        "detail": "REVISE/ASSIGN の確認前にCANCEL",
                        "suggestion": suggest_action("cancel_before_confirmation"),
                    }
                )
            state.status = "cancelled"
            state.requires_confirmation = False
            state.record(event)
        else:
            # 未定義のアクトは履歴に記録した上でスキップ
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            state.record(event)

    for state in commitments.values():
        if state.requires_confirmation:
            last_event = state.history[-1] if state.history else {}
            contradictions.append(
                {
                    "turn": last_event.get("turn"),
                    "commitment_id": state.commitment_id,
                    "type": "missing_confirmation",
                    "speaker": state.owner or last_event.get("speaker"),
                    "detail": "ASSIGN/REVISE後にCONFIRMが未完了",
                    "suggestion": suggest_action("missing_confirmation"),
                }
            )

    graph = build_graph(meeting.utterances)

    metrics = summarise_metrics(commitments, contradictions)

    return {
        "meeting_id": meeting.meeting_id,
        "topic": meeting.topic,
        "commitments": commitments,
        "contradictions": contradictions,
        "graph": graph,
        "metrics": metrics,
    }


def summarise_metrics(commitments: Dict[str, CommitmentState], contradictions: List[dict]) -> Dict[str, object]:
    total_commitments = len(commitments)
    contradiction_count = len(contradictions)
    contradicted_commitments = len({c["commitment_id"] for c in contradictions})
    type_counter = Counter(c["type"] for c in contradictions)
    contradiction_rate = (
        contradicted_commitments / total_commitments if total_commitments else 0.0
    )
    return {
        "total_commitments": total_commitments,
        "contradiction_count": contradiction_count,
        "contradicted_commitments": contradicted_commitments,
        "contradiction_rate": contradiction_rate,
        "contradiction_types": dict(sorted(type_counter.items())),
    }


def render_report(result: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append(f"会議ID: {result['meeting_id']}")
    if result.get("topic"):
        lines.append(f"トピック: {result['topic']}")
    lines.append("")
    lines.append("## コミットメント状態")
    for cid, state in result["commitments"].items():
        lines.append(
            f"- {cid}: status={state.status}, owner={state.owner}, due={state.due}, 履歴ターン={len(state.history)}"
        )
    lines.append("")
    lines.append("## 検出された矛盾")
    contradictions = result["contradictions"]
    if not contradictions:
        lines.append("- 矛盾なし")
    else:
        for item in contradictions:
            suggestion = item.get("suggestion")
            suggestion_suffix = f" | 提案: {suggestion}" if suggestion else ""
            lines.append(
                f"- turn{item['turn']} {item['commitment_id']}: {item['type']} ({item['detail']}) 発話者={item['speaker']}{suggestion_suffix}"
            )
    lines.append("")
    lines.append(f"矛盾総数: {len(contradictions)}")

    metrics = result.get("metrics", {})
    if metrics:
        lines.append("")
        lines.append("## 指標サマリ")
        lines.append(
            f"- コミットメント数: {metrics['total_commitments']}"
            f" / 矛盾検出コミットメント数: {metrics['contradicted_commitments']}"
        )
        lines.append(
            f"- 矛盾率: {metrics['contradiction_rate']:.2f}"
            f" (矛盾総数: {metrics['contradiction_count']})"
        )
        if metrics.get("contradiction_types"):
            lines.append("- 矛盾タイプ内訳:")
            for key, value in metrics["contradiction_types"].items():
                lines.append(f"  - {key}: {value}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="C2-Graph試作矛盾検出")
    parser.add_argument("input", type=Path, help="会議JSONファイル")
    parser.add_argument("--output", type=Path, help="レポート出力先 (省略時は標準出力)")
    args = parser.parse_args()

    meeting = load_meeting(args.input)
    result = analyse_meeting(meeting)
    report = render_report(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
