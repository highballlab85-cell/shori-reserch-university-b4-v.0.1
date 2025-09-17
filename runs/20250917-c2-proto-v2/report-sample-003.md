会議ID: sample-003
トピック: リリース前レビュー調整

## コミットメント状態
- C4: status=cancelled, owner=Eve, due=2025-09-21, 履歴ターン=4
- C5: status=cancelled, owner=None, due=None, 履歴ターン=1
- C6: status=cancelled, owner=Gina, due=2025-09-23, 履歴ターン=2

## 検出された矛盾
- turn3 C4: unauthorized_cancel (オーナー(Eve)以外がCANCEL) 発話者=Frank | 提案: コミットメントのオーナー本人、または合意を得たファシリテータがキャンセルを宣言できる状況に揃える。
- turn4 C4: duplicate_cancel (既にCANCEL済みのコミットメント) 発話者=Eve | 提案: 一度キャンセルした場合は進行ログを共有し、重複報告を避ける運用にする。
- turn5 C5: cancel_without_assignment (ASSIGN前にCANCELが発生) 発話者=Dave | 提案: ASSIGNの記録が残っているか確認し、割り当て情報を明示した上でキャンセルを宣言する。
- turn7 C6: cancel_before_confirmation (REVISE/ASSIGN の確認前にCANCEL) 発話者=Gina | 提案: REVISE/ASSIGN後は担当者のCONFIRMを待ち、必要に応じてリマインドを送る。

矛盾総数: 4

## 指標サマリ
- コミットメント数: 3 / 矛盾検出コミットメント数: 3
- 矛盾率: 1.00 (矛盾総数: 4)
- 矛盾タイプ内訳:
  - cancel_before_confirmation: 1
  - cancel_without_assignment: 1
  - duplicate_cancel: 1
  - unauthorized_cancel: 1