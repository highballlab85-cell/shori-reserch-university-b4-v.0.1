# C2-Graph 矛盾検出バッチレポート

## 会議別サマリ

### sample-001 (meeting-sample-001.json)
- トピック: 9月スプリント準備
- コミットメント: 3 / 矛盾コミットメント: 2 / 矛盾率: 0.67
- 検出矛盾:
  - turn10 C2: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Bob
  - turn13 C3: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Dave
  - turn13 C3: cancel_before_confirmation (REVISE/ASSIGN の確認前にCANCEL) 発話者=Dave

### sample-002 (meeting-sample-002.json)
- トピック: 10月リリース準備
- コミットメント: 2 / 矛盾コミットメント: 0 / 矛盾率: 0.00
- 検出矛盾: なし

## 集計結果

- 会議数: 2
- コミットメント合計: 5 / 矛盾コミットメント数: 2 / 矛盾率: 0.40
- 矛盾総数: 3
- 矛盾タイプ内訳:
  - cancel_before_confirmation: 1
  - unauthorized_cancel: 2