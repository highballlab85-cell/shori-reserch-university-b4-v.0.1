# AGENTS.md（テーマ探索版 / Codex CLI）

> 目的：**研究テーマそのもの**を Detect→Frame→Model/Hypothesize→Design→Run→Analyze→Update→Communicate→Decide のループに乗せ、
> **新規性×卒研規模の実現可能性**を同時に満たす Minimum Viable Research（MVR）に収束させる。

## 0) 不変原則（研究単位）
- 単位は **「主張＋根拠＋手続＋範囲」**。すべてのメモ・ログ・スライドに適用。
- 成果物は **コード・データ手順・評価スクリプト・ログ・限界** を同梱し再現可能に。
- 初期の基準（DER≤15%, TripleF1≥0.85, QA≥0.70）は中間発表の表（p.9）から出発し、テーマ更新で改訂可。
- **AI応答言語**：常に日本語で応答し、研究内容の説明・議論・質疑応答をすべて日本語で実施。

## 1) Roles
- Theme‑Scout（文献探索→差分仮説） / Novelty‑Scorer（新規性×実現可採点）
- Orchestrator（全体進行とExit判断） / Data Engineer（Diarization/ASR/整形）
- IE/Graph Builder（Triple抽出とGraphRAG） / Analyst（指標と検定） / Writer（公開）

## 2) THEME LOOP
1) **Detect**：似た先行が多い・複数人特有の課題（addressee/矛盾/重複発話）未解決点を列挙  
2) **Frame**：Exit条件＝「新規性1行説明」「8週以内実現」「測れる」  
3) **Model/Hypothesize**：テーマ別に予測まで言語化  
4) **Design**：データ（AMI/ICSI/自前）・ベースライン（Flat‑RAG/要約QA）・指標（DER/WER/Triple/QA＋固有指標）  
5) **Run**：seed固定・モデル固定・`runs/<theme>/<ts>` にログ  
6) **Analyze**：95%CI・誤り事例Top10  
7) **Update**：反証的更新（何を捨て何を残すか）  
8) **Communicate**：手順・限界・負債を明記  
9) **Decide**：継続 / Pivot / 撤退（次のギャップへ）

## 3) 候補テーマ（新規性×卒研規模）
- **B. Commitment & Contradiction Graph（C2‑Graph）〈推奨〉**  
  会話から `ASSIGN/CONFIRM/REVISE/CANCEL` を抽出し**コミットメントの状態遷移**と**矛盾**をグラフ制約で検出。  
  *評価*：Action‑Item F1 / **矛盾検出F1** / Who‑What‑When QA。

- A. Addressee‑Conditioned GraphRAG（AC‑GraphRAG）  
  **アドレス指示**（誰に向けたか）を辺に保持してQA性能を比較。

- C. Signed Social‑Interaction Graph（SSI‑Graph）  
  `ASSIGN/CONFIRM/DISPUTE` を**有向・符号付きエッジ**にし関係値を推定。

- D. Overlap‑Aware Triple Extraction  
  **重複発話**検出（EEND）とIEを統合し誤結合を削減。

## 4) スキーマ最小（C2‑Graph）
- Node：`Person`, `Utterance(ts, speaker)`, `Commitment(task, owner, due?, status)`  
- Edge：`ASSIGN/CONFIRM/REVISE/CANCEL`（すべて source→target, commitment_id）  
- Constraint例：`CANCEL` の前に `ASSIGN` が必須／同一commitmentに同時矛盾禁止。

## 5) 指標と基準（卒研版）
- DER, WER, Triple F1, QA（Who‑What‑When）, **Contradiction F1**, Tokens/Query, 実行時間。  
- 初期基準：DER≤0.15, TripleF1≥0.85, QA≥0.70（テーマ固有は別途設定）。

## 6) データ／ツール（MVP）
- Datasets：AMI subset・ICSI subset・自前 triads（同意＋匿名化）。
- ASR：WhisperX、Diarization：EEND/pyannote、Graph：NetworkX→Neo4j 任意、RAG：FAISS + Graphサブグラフ。

## 7) 実験テンプレ（YAML）
```yaml
goal: "C2‑Graph で会議理解を強化"
datasets: ["AMI_subset(10会議×10–20分)", "inhouse_triads(3–4人×2本)"]
pipeline:
  diarization: "EEND/pyannote"
  asr: "WhisperX"
  ie: ["LLM+ルールで ASSIGN/CONFIRM/REVISE/CANCEL を抽出"]
  graph: "NetworkX→Neo4j(任意)"
  rag:
    baselines: ["Flat-RAG", "要約QA"]
    proposed: "C2-GraphRAG"
metrics: ["action_item_f1","contradiction_f1","qa_acc_who_what_when","tokens_per_query"]
success_criteria: ["action_item_f1>=0.80","contradiction_f1>=0.70","qa_acc_who_what_when>=0.75"]
exit_rules: ["2週間で上記の2/3未達→Pivot A or C"]
```

## 8) プロンプト雛形（抜粋）
- **Theme‑Scout**：主要論文を各200字で「主張＋根拠＋手続＋範囲＋既存限界」、差分を3行。  
- **Novelty‑Scorer**：A/B/C/Dを4軸採点し、Exit条件をYAMLで出力。  
- **IE抽出器**：各発話を `ASSIGN/CONFIRM/REVISE/CANCEL/OTHER` に分類し JSONL 出力（根拠span付き）。  
- **Constraint‑Checker**：`ASSIGN -> (CONFIRM|REVISE)* -> (COMPLETE|CANCEL)?` を検査し違反を列挙。

## 9) フォルダ規約
```
agents/AGENTS.md
themes/frame.yaml
data/{raw,processed}
runs/YYYYMMDD-HHMM/
graphs/
report/
papers/notes.md
docs/
```

## 10) DONE > PERFECT
MVP→測定→改善の短サイクル。毎Runのヘッダに **主張・根拠・手続・範囲** を明記。
