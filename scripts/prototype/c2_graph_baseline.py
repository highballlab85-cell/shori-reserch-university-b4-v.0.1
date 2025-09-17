#!/usr/bin/env python3
"""C2-Graph試作スクリプト

サンプルの会議トランスクリプト(JSON)を入力し、ASSIGN/CONFIRM/REVISE/CANCEL
の状態遷移をトラッキングして矛盾を検出する。矛盾検出ルールは暫定:

- 未割り当てのコミットメントに対する CANCEL
- オーナー以外による CANCEL
- すでにキャンセル済みのコミットメントに対する重複 CANCEL

出力はテキストレポートとして stdout へ。--output を指定するとファイルにも保存する。
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import networkx as nx
except ImportError:  # networkxが未インストールでも動作可能にする
    nx = None


@dataclass
class CommitmentState:
    commitment_id: str
    owner: Optional[str] = None
    due: Optional[str] = None
    status: str = "assigned"
    history: List[dict] = field(default_factory=list)

    def record(self, event: dict) -> None:
        self.history.append(event)


def load_meeting(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_graph(events: List[dict]):
    graph = None
    if nx is not None:
        graph = nx.DiGraph()
        for event in events:
            node = f"commitment:{event['commitment_id']}"
            if not graph.has_node(node):
                graph.add_node(node, type="commitment")
            speaker_node = f"speaker:{event['speaker']}"
            if not graph.has_node(speaker_node):
                graph.add_node(speaker_node, type="speaker")
            graph.add_edge(
                speaker_node,
                node,
                act=event["act"],
                turn=event["turn"],
                timestamp=event["timestamp"],
            )
    return graph


def analyse_meeting(meeting: dict) -> Dict[str, object]:
    commitments: Dict[str, CommitmentState] = {}
    contradictions: List[dict] = []

    for event in meeting["utterances"]:
        act = event["act"].upper()
        cid = event["commitment_id"]
        state = commitments.get(cid)

        if act == "ASSIGN":
            state = commitments.setdefault(cid, CommitmentState(cid))
            state.owner = event.get("owner", state.owner)
            state.due = event.get("due", state.due)
            state.status = "assigned"
            state.record(event)
        elif act == "CONFIRM":
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            # CONFIRM の発話者をオーナーとして上書き（暫定仕様）
            state.owner = state.owner or event.get("owner") or event.get("speaker")
            state.status = "confirmed"
            state.record(event)
        elif act == "REVISE":
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            if "new_owner" in event:
                state.owner = event["new_owner"]
            if "new_due" in event:
                state.due = event["new_due"]
            state.status = "revised"
            state.record(event)
        elif act == "CANCEL":
            if state is None:
                contradictions.append(
                    {
                        "turn": event["turn"],
                        "commitment_id": cid,
                        "type": "cancel_without_assignment",
                        "speaker": event["speaker"],
                        "detail": "ASSIGN前にCANCELが発生",
                    }
                )
                continue
            if state.owner and event["speaker"] != state.owner:
                contradictions.append(
                    {
                        "turn": event["turn"],
                        "commitment_id": cid,
                        "type": "unauthorized_cancel",
                        "speaker": event["speaker"],
                        "detail": f"オーナー({state.owner})以外がCANCEL",
                    }
                )
            elif state.status == "cancelled":
                contradictions.append(
                    {
                        "turn": event["turn"],
                        "commitment_id": cid,
                        "type": "duplicate_cancel",
                        "speaker": event["speaker"],
                        "detail": "既にCANCEL済みのコミットメント",
                    }
                )
            state.status = "cancelled"
            state.record(event)
        else:
            # 未定義のアクトは履歴に記録した上でスキップ
            if state is None:
                state = commitments.setdefault(cid, CommitmentState(cid))
            state.record(event)

    graph = build_graph(meeting["utterances"])

    return {
        "meeting_id": meeting["meeting_id"],
        "topic": meeting.get("topic"),
        "commitments": commitments,
        "contradictions": contradictions,
        "graph": graph,
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
            lines.append(
                f"- turn{item['turn']} {item['commitment_id']}: {item['type']} ({item['detail']}) 発話者={item['speaker']}"
            )
    lines.append("")
    lines.append(f"矛盾総数: {len(contradictions)}")

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
