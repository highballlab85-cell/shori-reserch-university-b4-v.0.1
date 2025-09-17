#!/usr/bin/env python3
"""複数会議のC2-Graph矛盾検出結果を集計するスクリプト。

Usage:
    c2_batch_report.py <input_dir> [--output <file>]

- input_dir 以下の *.json を対象に `c2_graph_baseline.analyse_meeting` を実行
- 各会議の矛盾検出結果と指標サマリをMarkdown形式で出力
- 全体の合計件数、矛盾率、タイプ内訳を集計
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import sys

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import c2_graph_baseline as baseline  # noqa: E402


def gather_json_files(input_dir: Path) -> List[Path]:
    return sorted(p for p in input_dir.glob("*.json") if p.is_file())


def format_meeting_section(meeting_path: Path, result: Dict[str, object]) -> str:
    metrics = result.get("metrics", {})
    contradictions = result.get("contradictions", [])
    lines: List[str] = []
    lines.append(f"### {result['meeting_id']} ({meeting_path.name})")
    lines.append(f"- トピック: {result.get('topic', 'N/A')}")
    lines.append(
        "- コミットメント: {count} / 矛盾コミットメント: {contradicted} / 矛盾率: {rate:.2f}".format(
            count=metrics.get("total_commitments", 0),
            contradicted=metrics.get("contradicted_commitments", 0),
            rate=metrics.get("contradiction_rate", 0.0),
        )
    )
    if contradictions:
        lines.append("- 検出矛盾:")
        for item in contradictions:
            suggestion = item.get("suggestion")
            suggestion_suffix = f" | 提案: {suggestion}" if suggestion else ""
            lines.append(
                "  - turn{turn} {cid}: {ctype} ({detail}) 発話者={speaker}{suggestion}".format(
                    turn=item["turn"],
                    cid=item["commitment_id"],
                    ctype=item["type"],
                    detail=item["detail"],
                    speaker=item["speaker"],
                    suggestion=suggestion_suffix,
                )
            )
    else:
        lines.append("- 検出矛盾: なし")
    lines.append("")
    return "\n".join(lines)


def aggregate_metrics(results: List[Dict[str, object]]) -> Dict[str, object]:
    total_commitments = sum(r["metrics"]["total_commitments"] for r in results)
    total_contradictions = sum(r["metrics"]["contradiction_count"] for r in results)
    total_contradicted = sum(r["metrics"]["contradicted_commitments"] for r in results)

    type_counter: Dict[str, int] = {}
    for r in results:
        for key, value in r["metrics"]["contradiction_types"].items():
            type_counter[key] = type_counter.get(key, 0) + value

    return {
        "meetings": len(results),
        "total_commitments": total_commitments,
        "contradiction_count": total_contradictions,
        "contradicted_commitments": total_contradicted,
        "contradiction_rate": total_contradicted / total_commitments if total_commitments else 0.0,
        "contradiction_types": dict(sorted(type_counter.items())),
    }


def render_report(results: List[Tuple[Path, Dict[str, object]]], aggregate: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# C2-Graph 矛盾検出バッチレポート")
    lines.append("")
    lines.append("## 会議別サマリ")
    lines.append("")
    for meeting_path, result in results:
        lines.append(format_meeting_section(meeting_path, result))
    lines.append("## 集計結果")
    lines.append("")
    lines.append(f"- 会議数: {aggregate['meetings']}")
    lines.append(
        "- コミットメント合計: {total} / 矛盾コミットメント数: {contradicted} / 矛盾率: {rate:.2f}".format(
            total=aggregate["total_commitments"],
            contradicted=aggregate["contradicted_commitments"],
            rate=aggregate["contradiction_rate"],
        )
    )
    lines.append(f"- 矛盾総数: {aggregate['contradiction_count']}")
    if aggregate["contradiction_types"]:
        lines.append("- 矛盾タイプ内訳:")
        for key, value in aggregate["contradiction_types"].items():
            lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="C2-Graph矛盾検出バッチ実行")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    meeting_paths = gather_json_files(args.input_dir)
    if not meeting_paths:
        raise SystemExit("入力ディレクトリにJSONファイルがありません")

    results: List = []
    for path in meeting_paths:
        meeting = baseline.load_meeting(path)
        result = baseline.analyse_meeting(meeting)
        results.append((path, result))

    aggregate = aggregate_metrics([r for _, r in results])
    report = render_report(results, aggregate)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
