# C2-Graph 矛盾検出バッチレポート

## 会議別サマリ

### sample-001 (meeting-sample-001.json)
- トピック: 9月スプリント準備
- コミットメント: 3 / 矛盾コミットメント: 2 / 矛盾率: 0.67
- 検出矛盾:
  - turn10 C2: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Bob | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。
  - turn13 C3: unauthorized_cancel (オーナー(Alice)以外がCANCEL) 発話者=Dave | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。
  - turn13 C3: cancel_before_confirmation (REVISE/ASSIGN の確認前にCANCEL) 発話者=Dave | 提案: REVISE/ASSIGN後は担当者のCONFIRMを待ち、必要に応じてリマインドを送る。

### sample-002 (meeting-sample-002.json)
- トピック: 10月リリース準備
- コミットメント: 2 / 矛盾コミットメント: 0 / 矛盾率: 0.00
- 検出矛盾: なし

### sample-003 (meeting-sample-003.json)
- トピック: リリース前レビュー調整
- コミットメント: 3 / 矛盾コミットメント: 3 / 矛盾率: 1.00
- 検出矛盾:
  - turn3 C4: unauthorized_cancel (オーナー(Eve)以外がCANCEL) 発話者=Frank | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。
  - turn4 C4: duplicate_cancel (既にCANCEL済みのコミットメント) 発話者=Eve | 提案: 一度キャンセルした場合は進行ログを共有し、重複報告を避ける運用にする。
  - turn5 C5: cancel_without_assignment (ASSIGN前にCANCELが発生) 発話者=Dave | 提案: ASSIGNの記録が残っているか確認し、割り当て情報を明示した上でキャンセルを宣言する。
  - turn7 C6: cancel_before_confirmation (REVISE/ASSIGN の確認前にCANCEL) 発話者=Gina | 提案: REVISE/ASSIGN後は担当者のCONFIRMを待ち、必要に応じてリマインドを送る。

## 集計結果

- 会議数: 3
- コミットメント合計: 8 / 矛盾コミットメント数: 5 / 矛盾率: 0.62
- 矛盾総数: 7
- 矛盾タイプ内訳:
  - cancel_before_confirmation: 2
  - cancel_without_assignment: 1
  - duplicate_cancel: 1
  - unauthorized_cancel: 3