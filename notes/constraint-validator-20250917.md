# 2025-09-17 Constraint Validator MVP 結果

## 実装概要
- `data/schemas/c2_graph_meeting.schema.json` で C2-Graph 会議JSONの最小スキーマを定義し、`ASSIGN/CONFIRM/REVISE/CANCEL/OTHER` の必須フィールド制約を明文化。
- `scripts/prototype/c2_models.py` に Pydantic v2 ベースの `MeetingRecord`/`UtteranceEvent`/`ConstraintSummary` を追加し、読み込み時に turn 整列とフィールド整合性を自動チェック。
- `scripts/prototype/constraint_validator.py` を新設。OR-Tools CP-SAT が利用可能な環境では遷移制約の充足可能性を検証し、フォールバックとして従来ルールの矛盾検出を実行。Markdown/JSON レポートを `runs/20250917-c2-constraint/` に自動保存。

## CP-SAT 実行環境
- 現行環境では OR-Tools が未インストールのため `cp_model` が読み込めず、CP チェックは `SKIPPED` ステータスとなった。
- CP エンジン導入時に 1.0s タイムアウトで動作する設計を組み込んでおり、インストール後は追加コード変更なしで有効化できる。

## サンプル会議での検証結果
| Meeting | Violations | 主な指摘 | CP ステータス |
| --- | --- | --- | --- |
| sample-001 | 3 | `unauthorized_cancel`×2, `cancel_before_confirmation`×1 | SKIPPED |
| sample-002 | 0 | 正常シナリオ | SKIPPED |
| sample-003 | 6 | 権限外Cancel, 重複Cancel, 未割当Cancel, 確認前Cancelなど網羅 | SKIPPED |

- 出力レポート: `runs/20250917-c2-constraint/*.md` / `*.json`
- 既存の `c2_graph_baseline.py` も新モデル経由で読み込むよう更新し、抽出・矛盾查出が同一バリデーションパスを通る構成に統一。

## 考察
1. **構造バリデーションの一元化**: Pydantic モデル導入で抽出結果の品質ログを定量化しやすくなった。将来的には `confidence` や `metadata` を活用したエラー分析が容易になる。
2. **制約エンジンは即時差し替え可能**: 現状は SKIPPED だが、OR-Tools を導入すれば `cp_infeasible_transition` を自動追加でき、違反検出のカバレッジを向上できる。
3. **矛盾タイプの網羅性**: sample-003 のテストにより、`cancel_without_assignment`・`duplicate_cancel` など主要ケースで期待通りの違反が出力されることを確認。`confirm_without_assign` などのレアケースも検出可能になった。

## 次のアクション
1. OR-Tools を環境に導入し、実データで CP フェーズが有効化されるか確認（`pip install ortools` 想定）。
2. `ConstraintSummary` を `c2_batch_report.py` に統合し、バッチレポートにも CP ステータス列を表示。
3. Common Ground 由来の `open_questions` 表現を Schema/Model に追加し、介入提案文生成と連動。
4. LLM-as-a-judge 用スクリプトに `ConstraintSummary` を入力し、違反説明の具体性スコアリングを自動化。

## 追補 (Open Question モデル追加 / バッチ連携強化)
- JSONスキーマに `open_questions` と `question_refs` を追加し、QUD管理情報を保持できるようにした。
- `scripts/prototype/c2_models.py` に `OpenQuestion` モデルと `MeetingRecord.unresolved_questions` ヘルパを実装し、今後の介入提案ロジックで未解決問いを直接参照可能。
- `scripts/prototype/c2_batch_report.py` を制約バリデータと統合し、CPステータスと制約違反件数を会議ごと・全体集計に追記。出力例は `runs/20250917-c2-constraint/batch_report_with_constraints.md` を参照。

