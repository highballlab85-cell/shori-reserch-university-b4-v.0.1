会議ID: sample-001

## コミットメント状態シーケンス
- C1 (CP: SKIPPED): UNASSIGNED, ASSIGNED_PENDING, CONFIRMED, REVISED_PENDING, CONFIRMED
- C2 (CP: SKIPPED): UNASSIGNED, ASSIGNED_PENDING, CONFIRMED, CANCELLED, REVISED_PENDING, CONFIRMED, CANCELLED
- C3 (CP: SKIPPED): UNASSIGNED, ASSIGNED_PENDING, REVISED_PENDING, CANCELLED

## 検出された違反
- turn10 C2: unauthorized_cancel | オーナー Alice 以外が CANCEL を実施 (話者: Bob)
- turn13 C3: unauthorized_cancel | オーナー Alice 以外が CANCEL を実施 (話者: Dave)
- turn13 C3: cancel_before_confirmation | REVISE/ASSIGN の確認前にCANCEL (話者: Dave)

違反件数: 3 / コミットメント総数: 3