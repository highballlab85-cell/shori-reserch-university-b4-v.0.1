会議ID: sample-003

## コミットメント状態シーケンス
- C4: UNASSIGNED, ASSIGNED_PENDING, CONFIRMED, CANCELLED, CANCELLED
- C5: UNASSIGNED, CANCELLED
- C6: UNASSIGNED, ASSIGNED_PENDING, CANCELLED

## 検出された違反
- turn3 C4: unauthorized_cancel | オーナー Eve 以外が CANCEL を実施 (話者: Frank)
- turn4 C4: invalid_transition | CANCELLED から CANCEL は許可されていない遷移 (話者: Eve)
- turn4 C4: duplicate_cancel | 既にキャンセル済みのコミットメントに対する重複CANCEL (話者: Eve)
- turn5 C5: invalid_transition | UNASSIGNED から CANCEL は許可されていない遷移 (話者: Dave)
- turn5 C5: cancel_without_assignment | ASSIGN 前に CANCEL が発生 (話者: Dave)
- turn7 C6: cancel_before_confirmation | REVISE/ASSIGN の確認前にCANCEL (話者: Gina)

違反件数: 6 / コミットメント総数: 3