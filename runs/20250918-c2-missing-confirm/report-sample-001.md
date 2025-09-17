会議ID: sample-001
トピック: 9月スプリント準備

## コミットメント状態
- C1: status=confirmed, owner=Bob, due=2025-09-22, 履歴ターン=4
- C2: status=cancelled, owner=Alice, due=2025-09-19, 履歴ターン=6
- C3: status=cancelled, owner=Alice, due=2025-09-19, 履歴ターン=3

## 検出された矛盾
- turn10 C2: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Bob | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。
- turn13 C3: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Dave | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。

矛盾総数: 2

## 指標サマリ
- コミットメント数: 3 / 矛盾検出コミットメント数: 2
- 矛盾率: 0.67 (矛盾総数: 2)
- 矛盾タイプ内訳:
  - unauthorized_cancel: 2