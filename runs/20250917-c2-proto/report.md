会議ID: sample-001
トピック: 9月スプリント準備

## コミットメント状態
- C1: status=confirmed, owner=Bob, due=2025-09-22, 履歴ターン=4
- C2: status=cancelled, owner=Alice, due=2025-09-19, 履歴ターン=6

## 検出された矛盾
- turn10 C2: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Bob

矛盾総数: 1