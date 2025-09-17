# Detect フェーズメモ (C2-Graph)

## 1. 探索キーワード
- "action item detection meeting"
- "commitment extraction dialogue"
- "contradiction detection conversations"
- "meeting graph reasoning"

## 2. 先行研究サマリ
### Action-Item-Driven Summarization of Long Meeting Transcripts (Golia & Kalita, 2023)
- AMIコーパスを対象に、アクションアイテム抽出→セクション要約→統合という階層型パイプラインを提案。
- BERTScore 64.98（AMI基準）でSOTAを更新。長尺会議をトピックセグメント化する工夫が有用。
- C2-Graphへの示唆: セクション分割＋局所行動抽出のパイプラインは、`ASSIGN/CONFIRM` 抽出に応用可能。
  - 出典: arXiv:2312.17581

### Meeting Action Item Detection with Regularized Context Modeling (Liu et al., 2023)
- 中国語会議コーパスを新規作成し、コンテキストドロップ（局所/大域文脈のコントラスト学習）でアクションアイテム検出性能を向上。
- AMI英語コーパスにも適用し精度向上を報告。多言語対応のヒント。
- C2-Graphへの示唆: 発話の局所編集（rephrase）に強い頑健性が必要。
  - 出典: arXiv:2303.16763

### Red Teaming Language Models for Contradictory Dialogues (Wen et al., 2024)
- LLMが自己矛盾を生成するケースに対し、矛盾位置と説明を含むデータセットを構築。
- 矛盾検出＋修正のタスク定義。説明生成が指標改善に寄与。
- C2-Graphへの示唆: 矛盾抽出時に説明（どのコミットメントが衝突しているか）を含める設計が重要。
  - 出典: arXiv:2405.10128

### MUG Benchmark (Zhang et al., 2023)
- AliMeeting4MUG コーパスで会議理解タスク（要約・キーフレーズ・アクションアイテム等）を統合。
- アクションアイテム検出タスクと評価指標がセットで提供される。中国語中心だが構成が参考になる。
- C2-Graphへの示唆: 多タスク一体型ベンチマークを意識し、指標と評価データの整合性を確保。
  - 出典: arXiv:2303.13939

## 3. 課題ギャップ
- `ASSIGN/CONFIRM/REVISE/CANCEL` を扱う公開データセットは見つからず。既存アクションアイテムは `ASSIGN` 寄りで状態遷移ラベルが欠落。
- 矛盾検出は主に QA ないし自己矛盾タスクで、コミットメント間の因果グラフ利用は未整備。
- 長時間会議のリアルタイム処理に向けた軽量パイプライン事例は少なく、推論コスト設計が必要。

## 4. TODO（9/18〜）
- AMI コーパス内の action item アノテーション仕様を確認し、C2-Graph 用のラベルマッピング案をまとめる。
- 先行研究の評価指標（特に Contradiction F1 相当）を調査し、再利用可能な定義があるか確認。
- 追加文献探索: "commitment graph dialogue", "task responsibility extraction"。
- 自前アノテーション設計案のドラフトを `docs/` に作成。

## 5. 追加実験ログ（2025-09-18）
- `scripts/prototype/c2_graph_baseline.py` に `missing_confirmation` ルールを追加し、ASSIGN/REVISE 後に CONFIRM が得られないコミットメントを検出できるようにした。
- サンプル会議 `meeting-sample-004.json` を作成し、`REVISE` 後に承認が保留されたケースと未解決質問 (`open_questions`) の連携をテスト。
- 4件のサンプル会議に対するバッチ集計では、矛盾タイプに `missing_confirmation` が新たに加わり、矛盾コミットメント数6件・矛盾率0.60を確認。確認漏れを担当者ベースでリマインドする提案文が生成されることを検証。
- `missing_confirmation` を含む複数矛盾が同一ターンに並ぶケースで最優先の提案だけを残すよう `c2_graph_baseline` を更新し、レポートでは各コミットメントに対して最も重大な指摘のみを提示するよう調整。

---
担当: Codex CLIエージェント / 更新日: 2025-09-18
