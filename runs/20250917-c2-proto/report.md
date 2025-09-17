会議ID: sample-001
トピック: 9月スプリント準備

## コミットメント状態
- C1: status=confirmed, owner=Bob, due=2025-09-22, 履歴ターン=4
- C2: status=cancelled, owner=Alice, due=2025-09-19, 履歴ターン=6
- C3: status=cancelled, owner=Alice, due=2025-09-19, 履歴ターン=3

## 検出された矛盾
- turn10 C2: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Bob
- turn13 C3: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Dave
- turn13 C3: cancel_before_confirmation (REVISE/ASSIGN の確認前にCANCEL) 発話者=Dave

矛盾総数: 3

## 指標サマリ
- コミットメント数: 3 / 矛盾検出コミットメント数: 2
- 矛盾率: 0.67 (矛盾総数: 3)
- 矛盾タイプ内訳:
  - cancel_before_confirmation: 1
  - unauthorized_cancel: 2