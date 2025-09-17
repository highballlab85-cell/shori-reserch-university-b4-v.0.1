# 2025-09-17 類似モデル改善アプローチ整理

## 目的
- C2-Graph の抽出→矛盾検知→提案パイプラインを、先行研究で実績がある LLM 改善パターンに寄せてブラッシュアップする。
- 「制約遵守」「反復最適化」「構造化表現」「共有認識更新」「評価体制」の5観点で差分を特定し、次サイクルの実装タスクにブレイクダウンする。

## 参照した先行研究・プロダクト概要
1. **GenCP (Bonlarron et al., IJCAI 2025)**: LLM 予測を制約プログラミング (CP) に接続し、Masked LM を併用して前後文脈を見渡したドメインプレビューを挟むことで、制約充足率と探索効率を両立。コール数は増えるが、厳格な制約下でも可行解生成率が向上。citeturn2view0
2. **GA LLM (Shum et al., 2025)**: 出力を遺伝的アルゴリズムの個体として扱い、LLM が生成・評価・交叉・突然変異をガイド。構造制約を守りつつ高品質解を得るハイブリッド最適化フレームワーク。citeturn3view0
3. **NL2FLOW (Kang, 2025)**: 自然言語→中間 JSON→PDDL の二段変換で 2,296 件のワークフロー計画問題を自動生成し、構造化インターフェースが有効計画率 (86%) と最適計画率 (69%) を押し上げたと報告。citeturn4view0
4. **Common Ground Tracking (Khebour et al., 2024)**: マルチモーダル対話の共有認識を推定し、推論結果を形式的なクロージャルールで更新。対話参加者間で共有される命題集合と「議論中の問い (QUD)」を逐次維持する方法論。citeturn6view0
5. **Amazon Nova 事例 (Chaudhury et al., 2025)**: 企業向け会議アシスタントで、ペルソナ付与＋チェーン・オブ・ソート＋LLM-as-a-judge 評価を組み合わせ、Faithfulness 0.83〜1.0 のレンジでモデル別性能を比較。迅速なプロンプト調整と評価自動化の運用知見。citeturn7view0
6. **IBM 会議アクションアイテム特許 (US10102198B2)**: 会議トピックモデルでトランスクリプトをチャンク化し、IE→アクションアイテム→依存関係グラフを段階生成。可視化と優先度付けを含む業務フローが実装例として明示。citeturn9view0
7. **ProgCo (Song et al., ACL 2025)**: LLM 自身が擬似プログラムを生成・実行する検証フェーズ (ProgVe) と、検証結果を反映するリファインフェーズ (ProgRe) で自己修正を安定化。citeturn11search4
8. **MermaidFlow (Jiang et al., 2025)**: 高レベルプランナーがタスク系列を生成し、低レベル実行器が安全制約を守る形でアクションに落とし込む二層構造。Risk-Aware 指標 (RA@k) で安全性遵守率を測定。citeturn8view0

## C2-Graph への適用方針
### 1. 制約遵守レイヤ
- LLM 抽出後に `commitment_id` ごとの状態遷移列を CP ソルバへ送る *Constraint Check Stage* を新設。
- GenCP に倣い、Masked LM による「次候補遷移の語彙制限」を導入し、`ASSIGN→CONFIRM/REVISE→CANCEL/COMPLETE` の必須制約・権限制約をハード制約、期限や優先度をソフト制約として扱う。
- 実装タスク: `scripts/prototype/constraint_validator.py`（仮）を作成し、`python-constraint` か OR-Tools CP-SAT を用いて矛盾種別を自動分類する。 

### 2. 反復最適化ループ
- GA LLM と MermaidFlow の示唆を合成し、**グラフ進化ループ**を試作。初期グラフを LLM が生成→CP 検証→評価スコアに基づき交叉・突然変異（例: エッジの再配属、提案文の強度調整）を行う。citeturn3view0turn8view0
- 目的関数: (a) 制約違反数減少、(b) 矛盾タイプ多様性、(c) 提案文の具体性スコア（LLM-as-a-judge 評価）。
- 第1段階として遺伝的探索は 3 世代・母集団 8 を上限にし、実行時間を制御。 

### 3. 構造化表現レイヤ
- NL2FLOW の二段表現を踏まえ、`utterance_span -> action_record -> graph_event` の JSON スキーマを定義。特に `owner`, `delegator`, `due`, `status` を明示し、Pydantic モデルでバリデーション。
- 後段の CP と GA が JSON を直接扱えるよう、`data/schemas/c2_graph_event.json` を用意予定。

### 4. 共有認識アップデート
- Common Ground Tracking の QUD 概念を借り、会議内で未解決の問い/要求を `open_questions` としてグラフに保持。`REVISE` で所有者が変わった場合は QUD を再投入、`CONFIRM` で解消、といったクロージャルールを State Machine 化。
- これにより矛盾提案文に「未解決問い」リストを添付し、次会議への引継ぎ情報を補完。

### 5. 評価・自己修正フロー
- Amazon Nova 事例と ProgCo を組み合わせ、評価→自己修正を自動化。
  - Faithfulness/QA/Conciseness を LLM-as-a-judge でスコア化し、Threshold 未達時に ProgVe 形式の検証プロンプトを生成。
  - 検証プロンプトは矛盾箇所ごとに「証拠発話」「現在の説明」「修正候補」を JSON で受け取り、差分をレポート。
  - 解析結果を `runs/<date>-c2-evolve/iteration-<n>.md` に保存し、コミットメッセージの「結果」「考察」に統合。

## 近日の実装タスク
- [ ] JSON スキーマ草案 & バリデーション (`data/schemas/`)
- [ ] CP バリデータ試作 (`scripts/prototype/constraint_validator.py`)
- [ ] GA ループたたき台 (`scripts/prototype/graph_evolver.py`)
- [ ] LLM-as-a-judge 評価スクリプト (`scripts/eval/llm_judge.py`)
- [ ] ProgCo 風検証プロンプトテンプレ (`prompts/validator/progco_style.md`)

## 想定リスクと対応
- **計算コスト**: CP + GA + LLM-as-a-judge の多段構成でレイテンシ増。→ まずはサンプル会議3件でベンチ、ボトルネックを測定。
- **LLM 評価の揺らぎ**: Judge モデルによるバラツキを避けるため、同一プロンプトを3回実行し中央値を採用。
- **権限データ不足**: 権限外CANCEL検出を強化するにはオーナー交替履歴が必要。→ Common Ground 手法を応用した共有認識ログを追加収集。

## 14日ロードマップへの組み込み
- Day 1-3: JSON スキーマと CP バリデータを MVP 化。
- Day 4-6: GA ループをサンプル会議に適用し、 `矛盾率` と `提案文スコア` の比較表を作成。
- Day 7-10: LLM-as-a-judge + ProgCo 風自己修正を統合し、改善幅を測定。
- Day 11-14: AMI サブセット 2 会議でスモールラン、Pivot 判断用レポートに反映。
