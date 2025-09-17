会議ID: sample-004
トピック: QA引き継ぎ確認ミーティング

## コミットメント状態
- C7: status=revised, owner=Bob, due=2025-09-26, 履歴ターン=2
- C8: status=confirmed, owner=Eve, due=2025-09-23, 履歴ターン=2

## 検出された矛盾
- turn3 C7: missing_confirmation (ASSIGN/REVISE後にCONFIRMが未完了) 発話者=Bob | 提案: ASSIGN/REVISE後の確認が抜けていないかを点検し、担当者から明示的なCONFIRM発話を得る。

矛盾総数: 1

## 指標サマリ
- コミットメント数: 2 / 矛盾検出コミットメント数: 1
- 矛盾率: 0.50 (矛盾総数: 1)
- 矛盾タイプ内訳:
  - missing_confirmation: 1